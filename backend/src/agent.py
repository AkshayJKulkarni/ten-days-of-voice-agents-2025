import logging
import os

from dotenv import load_dotenv
from faq_loader import load_faq_data

def load_catalog():
    """Load catalog from day7_catalog.json and return item_id -> item_data mapping"""
    try:
        catalog_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "shared-data", "day7_catalog.json")
        with open(catalog_path, 'r', encoding='utf-8') as f:
            catalog_list = json.load(f)
        
        # Convert list to dictionary mapping item_id -> item_data
        catalog = {item["id"]: item for item in catalog_list}
        return catalog
    except Exception as e:
        logger.error(f"Failed to load catalog: {e}")
        return {}
from livekit.agents import (
    Agent,
    AgentSession,
    JobContext,
    JobProcess,
    MetricsCollectedEvent,
    RoomInputOptions,
    WorkerOptions,
    cli,
    metrics,
    tokenize,
    function_tool,
    RunContext
)
import json
from datetime import datetime
from livekit.plugins import murf, silero, google, deepgram, noise_cancellation
from livekit.plugins.turn_detector.multilingual import MultilingualModel

logger = logging.getLogger("agent")

load_dotenv(".env.local")

# Global cart state that persists during the session
cart = {
    "items": [],
    "total": 0
}

# Global lead state that persists during the session
lead_state = {
    "name": "",
    "company": "",
    "email": "",
    "role": "",
    "use_case": "",
    "team_size": "",
    "timeline": ""
}

def add_to_cart(item_id, qty):
    """Add item to cart or update quantity if exists"""
    catalog = load_catalog()
    if item_id not in catalog:
        return False
    
    # Check if item already in cart
    for item in cart["items"]:
        if item["item_id"] == item_id:
            item["qty"] += qty
            update_cart_total()
            return True
    
    # Add new item
    cart["items"].append({
        "item_id": item_id,
        "name": catalog[item_id]["name"],
        "qty": qty,
        "price": catalog[item_id]["price"]
    })
    update_cart_total()
    return True

def remove_from_cart(item_id):
    """Remove item from cart"""
    cart["items"] = [item for item in cart["items"] if item["item_id"] != item_id]
    update_cart_total()

def update_quantity(item_id, qty):
    """Update item quantity in cart"""
    for item in cart["items"]:
        if item["item_id"] == item_id:
            if qty <= 0:
                remove_from_cart(item_id)
            else:
                item["qty"] = qty
                update_cart_total()
            return True
    return False

def list_cart():
    """Return cart contents as string"""
    if not cart["items"]:
        return "Your cart is empty."
    
    items_str = "\n".join([f"{item['qty']}x {item['name']} - ₹{item['price'] * item['qty']}" for item in cart["items"]])
    return f"Your cart:\n{items_str}\nTotal: ₹{cart['total']}"

def update_cart_total():
    """Update cart total"""
    cart["total"] = sum(item["price"] * item["qty"] for item in cart["items"])


class SalesSDR(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""You are a friendly food & grocery ordering assistant. Your job is to help customers build their shopping cart and place orders.

            CAPABILITIES:
            - Order groceries, food, snacks, beverages, and prepared foods
            - Add ingredients for specific dishes using recipe mappings
            - Manage shopping cart (add, remove, update quantities)
            - Calculate total prices and place orders
            
            IMPORTANT: When customers request items, call the appropriate function:
            - add_to_cart(item_name, quantity) for adding items
            - remove_from_cart(item_name) for removing items
            - update_quantity(item_name, quantity) for changing amounts
            - show_cart() to display current cart
            - place_order() when they say "place my order", "that's all", "I'm done"
            
            CONVERSATION FLOW:
            1. Greet warmly and explain what you can do
            2. Ask what they'd like to order
            3. For recipe requests like "ingredients for pasta", use recipe mappings
            4. Ask clarifying questions about quantity, size, brand when needed
            5. Confirm every cart update verbally
            6. When ready to order, summarize cart, calculate total, and save to JSON
            
            Be helpful, ask clarifying questions, and always confirm cart changes.""",
        )
        # Use global lead_state
        global lead_state
        self.lead_state = lead_state
        self.session_started = False
        self.conversation_complete = False
        self.room = None
        
        # Recipe mappings for grocery requests
        self.recipes = {
            "peanut butter sandwich": ["bread_01", "peanut_butter_01"],
            "pasta for two": ["pasta_01", "pasta_sauce_01"],
            "tea": ["tea_bag_01", "milk_01", "sugar_01"],
            "salad": ["lettuce_01", "tomato_01", "cucumber_01"]
        }
        
        # Load FAQ data at startup
        self.company_name, self.description, self.pricing, self.faq_list = load_faq_data()
    
    def find_faq_answer(self, user_query: str) -> str:
        """Find FAQ answer using keyword matching
        
        Args:
            user_query: User's question or query
            
        Returns:
            FAQ answer if found, None if not found
        """
        query_lower = user_query.lower()
        
        for faq_item in self.faq_list:
            question = faq_item.get("question", "").lower()
            
            # Simple keyword matching - check if question words are in user query
            question_words = question.split()
            if any(word in query_lower for word in question_words if len(word) > 2):
                return faq_item.get("answer", "")
        
        return None
    
    def save_lead_to_json(self) -> str:
        """Save lead state to JSON file with timestamp"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"lead_{timestamp}.json"
        
        leads_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "leads")
        os.makedirs(leads_dir, exist_ok=True)
        
        filepath = os.path.join(leads_dir, filename)
        
        # Add timestamp to lead data
        lead_data = self.lead_state.copy()
        lead_data["timestamp"] = datetime.now().isoformat()
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(lead_data, f, indent=2, ensure_ascii=False)
        
        return filepath
    
    def detect_end_of_call(self, user_input: str) -> bool:
        """Detect if user wants to end the conversation"""
        end_phrases = ["that's all", "i'm done", "thanks", "thank you", "you can end the call", "goodbye", "bye"]
        user_lower = user_input.lower()
        return any(phrase in user_lower for phrase in end_phrases)
    
    def generate_lead_summary(self) -> str:
        """Generate verbal summary of collected lead information"""
        filled_fields = []
        
        if self.lead_state["name"]:
            filled_fields.append(f"name is {self.lead_state['name']}")
        if self.lead_state["company"]:
            filled_fields.append(f"from {self.lead_state['company']}")
        if self.lead_state["role"]:
            filled_fields.append(f"working as {self.lead_state['role']}")
        if self.lead_state["use_case"]:
            filled_fields.append(f"interested in {self.lead_state['use_case']}")
        
        if filled_fields:
            return f"Great! I have your information: {', '.join(filled_fields)}. I'll save this and someone from our team will follow up soon."
        else:
            return "Thank you for your time today! Feel free to reach out if you have any questions."
    
    def reset_lead_state(self):
        """Reset lead state to empty values"""
        global lead_state
        for key in lead_state:
            lead_state[key] = ""
        self.lead_state = lead_state

    def update_lead_info(self, field: str, value: str):
        """Update lead information field"""
        if field in self.lead_state:
            self.lead_state[field] = value
    
    def get_missing_lead_fields(self) -> list:
        """Get list of missing lead information fields"""
        return [field for field, value in self.lead_state.items() if not value.strip()]
    
    def ask_for_missing_info(self) -> str:
        """Ask for missing lead information naturally"""
        missing = self.get_missing_lead_fields()
        
        if "name" in missing:
            return "By the way, I'd love to know your name so I can personalize our conversation."
        elif "company" in missing:
            return "What company are you with?"
        elif "role" in missing:
            return "What's your role there?"
        elif "use_case" in missing:
            return "What would you be looking to use our solution for?"
        elif "team_size" in missing:
            return "How big is your team?"
        elif "timeline" in missing:
            return "What's your timeline for implementing something like this?"
        elif "email" in missing:
            return "Could I get your email so someone from our team can follow up with more details?"
        
        return ""



    @function_tool
    async def handle_conversation(self, context: RunContext, user_input: str):
        """Handle SDR conversation flow
        
        Args:
            user_input: What the user said
        """
        self.room = context.room
        
        # Initial greeting
        if not self.session_started:
            self.session_started = True
            return f"Hi there! Welcome to {self.company_name}. I'm here to help answer any questions you might have. What brought you to us today?"
        
        user_lower = user_input.lower()
        
        # Check for recipe requests
        if "ingredients for" in user_lower or "things for making" in user_lower or "for making" in user_lower:
            for recipe_name, item_ids in self.recipes.items():
                if recipe_name in user_lower:
                    catalog = load_catalog()
                    added_items = []
                    for item_id in item_ids:
                        if add_to_cart(item_id, 1):
                            added_items.append(catalog[item_id]["name"])
                    
                    if added_items:
                        items_text = " and ".join(added_items)
                        return f"I've added {items_text} for your {recipe_name}. Anything else?"
                    else:
                        return f"Sorry, I couldn't find all ingredients for {recipe_name}."
        
        # Check for end-of-order
        if any(phrase in user_lower for phrase in ["place my order", "that's all", "i'm done"]):
            if not cart["items"]:
                return "Your cart is empty. Would you like to add some items first?"
            
            # Save order and summarize
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            order_data = {
                "items": cart["items"],
                "total": cart["total"],
                "timestamp": datetime.now().isoformat()
            }
            
            orders_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "orders")
            os.makedirs(orders_dir, exist_ok=True)
            
            order_path = os.path.join(orders_dir, f"order_{timestamp}.json")
            with open(order_path, 'w', encoding='utf-8') as f:
                json.dump(order_data, f, indent=2, ensure_ascii=False)
            
            summary = list_cart()
            cart["items"] = []
            cart["total"] = 0
            
            return f"Order placed successfully! {summary} Your order has been saved and will be processed shortly."
        
        # Default response
        return "I can help you add items to your cart or get ingredients for recipes. What would you like to order?"
    
    def extract_lead_info(self, user_input: str):
        """Extract lead information from user input"""
        user_lower = user_input.lower()
        
        # Simple extraction patterns
        if "my name is" in user_lower or "i'm" in user_lower:
            # Extract name after "my name is" or "i'm"
            for phrase in ["my name is ", "i'm ", "i am "]:
                if phrase in user_lower:
                    name_part = user_input[user_lower.find(phrase) + len(phrase):].split()[0]
                    if name_part and not self.lead_state["name"]:
                        self.lead_state["name"] = name_part.capitalize()
        
        # Extract email if mentioned
        if "@" in user_input and not self.lead_state["email"]:
            words = user_input.split()
            for word in words:
                if "@" in word and "." in word:
                    self.lead_state["email"] = word
        
        # Extract company info
        if any(phrase in user_lower for phrase in ["work at", "from", "company is", "at"]) and not self.lead_state["company"]:
            # Simple company extraction
            for phrase in ["work at ", "from ", "company is ", "at "]:
                if phrase in user_lower:
                    company_part = user_input[user_lower.find(phrase) + len(phrase):].split()[0]
                    if company_part:
                        self.lead_state["company"] = company_part.capitalize()


def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()


async def entrypoint(ctx: JobContext):
    # Logging setup
    ctx.log_context_fields = {
        "room": ctx.room.name,
    }

    # Create agent instance
    agent = TeachTheTutor()

    # Set up a voice AI pipeline
    session = AgentSession(
        stt=deepgram.STT(model="nova-3"),
        llm=google.LLM(model="gemini-2.5-flash"),
        tts=murf.TTS(
            voice="en-US-matthew",  # Default voice
            style="Conversation",
            tokenizer=tokenize.basic.SentenceTokenizer(min_sentence_len=2),
            text_pacing=True
        ),
        turn_detection=MultilingualModel(),
        vad=ctx.proc.userdata["vad"],
        preemptive_generation=True,
    )

    # To use a realtime model instead of a voice pipeline, use the following session setup instead.
    # (Note: This is for the OpenAI Realtime API. For other providers, see https://docs.livekit.io/agents/models/realtime/))
    # 1. Install livekit-agents[openai]
    # 2. Set OPENAI_API_KEY in .env.local
    # 3. Add `from livekit.plugins import openai` to the top of this file
    # 4. Use the following session setup instead of the version above
    # session = AgentSession(
    #     llm=openai.realtime.RealtimeModel(voice="marin")
    # )

    # Metrics collection, to measure pipeline performance
    # For more information, see https://docs.livekit.io/agents/build/metrics/
    usage_collector = metrics.UsageCollector()

    @session.on("metrics_collected")
    def _on_metrics_collected(ev: MetricsCollectedEvent):
        metrics.log_metrics(ev.metrics)
        usage_collector.collect(ev.metrics)

    async def log_usage():
        summary = usage_collector.get_summary()
        logger.info(f"Usage: {summary}")

    ctx.add_shutdown_callback(log_usage)

    # # Add a virtual avatar to the session, if desired
    # # For other providers, see https://docs.livekit.io/agents/models/avatar/
    # avatar = hedra.AvatarSession(
    #   avatar_id="...",  # See https://docs.livekit.io/agents/models/avatar/plugins/hedra
    # )
    # # Start the avatar and wait for it to join
    # await avatar.start(session, room=ctx.room)

    # Start the session
    await session.start(
        agent=agent,
        room=ctx.room,
        room_input_options=RoomInputOptions(
            noise_cancellation=noise_cancellation.BVC(),
        ),
    )

    # Join the room and connect to the user
    await ctx.connect()


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint, prewarm_fnc=prewarm))
