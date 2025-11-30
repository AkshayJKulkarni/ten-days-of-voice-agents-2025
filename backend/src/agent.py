import logging

from dotenv import load_dotenv
from commerce_backend import list_products, create_order, get_last_order, get_product_by_id
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


class EcommerceAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""You are a helpful voice-driven shopping assistant following the Agentic Commerce Protocol (ACP) pattern.
            
            Your role is to:
            1. Help customers browse and discover products
            2. Answer questions about product details, availability, and pricing
            3. Assist with placing orders through voice commands
            4. Provide order confirmations and summaries
            
            Available product categories: mugs, clothing (t-shirts, hoodies)
            
            Shopping flow:
            1. Greet customers and ask what they're looking for
            2. Use browse_catalog function to show relevant products
            3. Help customers select products and quantities
            4. Use place_order function to create orders
            5. Confirm order details and provide order ID
            
            Key behaviors:
            - Always use functions to get real product data - DO NOT make up products
            - When showing products, mention name, price, and key details
            - Help resolve ambiguous requests ("the second hoodie you mentioned")
            - Confirm order details before placing
            - Be helpful and conversational throughout
            
            Example interactions:
            - "Show me coffee mugs" → call browse_catalog with mug category
            - "I want the blue mug" → identify product and help place order
            - "What did I just buy?" → call get_last_order to show recent purchase""",
        )
        self.session_started = False
        self.last_shown_products = []  # Track products shown to user
        self.room = None

    @function_tool
    async def browse_catalog(self, context: RunContext, category: str = "", max_price: int = 0, color: str = "", search_term: str = ""):
        """Browse product catalog with filters
        
        Args:
            category: Product category (mug, clothing)
            max_price: Maximum price filter
            color: Color filter
            search_term: Search in product names
        """
        self.room = context.room
        
        filters = {}
        if category:
            filters["category"] = category
        if max_price > 0:
            filters["max_price"] = max_price
        if color:
            filters["color"] = color
        if search_term:
            filters["name_contains"] = search_term
        
        products = list_products(filters)
        self.last_shown_products = products
        
        if not products:
            return "I couldn't find any products matching your criteria. Try a different search or ask to see all products."
        
        # Format product list
        product_list = []
        for i, product in enumerate(products[:5], 1):  # Show max 5 products
            product_list.append(f"{i}. {product['name']} - ₹{product['price']} ({product['color']} {product.get('size', '')})")
        
        products_text = "\n".join(product_list)
        return f"Here are the products I found:\n{products_text}\n\nWould you like more details about any of these, or shall I help you place an order?"

    @function_tool
    async def place_order(self, context: RunContext, product_reference: str, quantity: int = 1):
        """Place an order for a product
        
        Args:
            product_reference: Product name, ID, or reference like "first one", "blue mug"
            quantity: Quantity to order
        """
        # Try to resolve product reference
        product = None
        
        # Check if it's a direct product ID
        product = get_product_by_id(product_reference)
        
        # If not found, try to match from last shown products
        if not product and self.last_shown_products:
            reference_lower = product_reference.lower()
            
            # Handle ordinal references
            if "first" in reference_lower or "1" in reference_lower:
                product = self.last_shown_products[0] if len(self.last_shown_products) > 0 else None
            elif "second" in reference_lower or "2" in reference_lower:
                product = self.last_shown_products[1] if len(self.last_shown_products) > 1 else None
            elif "third" in reference_lower or "3" in reference_lower:
                product = self.last_shown_products[2] if len(self.last_shown_products) > 2 else None
            
            # Handle color/name matching
            if not product:
                for p in self.last_shown_products:
                    if (reference_lower in p["name"].lower() or 
                        reference_lower in p["color"].lower()):
                        product = p
                        break
        
        if not product:
            return f"I couldn't find the product '{product_reference}'. Could you be more specific or browse the catalog again?"
        
        # Create order
        line_items = [{"product_id": product["id"], "quantity": quantity}]
        order = create_order(line_items)
        
        return f"Order placed successfully! Order ID: {order['id']}\n\nYou ordered:\n{quantity}x {product['name']} - ₹{product['price'] * quantity}\n\nTotal: ₹{order['total']}\n\nYour order is confirmed and will be processed shortly."

    @function_tool
    async def get_order_status(self, context: RunContext):
        """Get the last order details"""
        order = get_last_order()
        
        if not order:
            return "You haven't placed any orders yet. Would you like to browse our catalog?"
        
        items_text = "\n".join([f"{item['quantity']}x {item['product_name']} - ₹{item['total_price']}" 
                               for item in order['items']])
        
        return f"Your last order (ID: {order['id']}):\n{items_text}\n\nTotal: ₹{order['total']}\nStatus: {order['status']}\nPlaced: {order['created_at'][:19]}"

    @function_tool
    async def handle_shopping(self, context: RunContext, user_input: str):
        """Handle general shopping conversation
        
        Args:
            user_input: What the user said
        """
        self.room = context.room
        
        if not self.session_started:
            self.session_started = True
            return "Welcome to our online store! I'm here to help you find and order products. What are you looking for today? I can show you mugs, clothing, or help you search for something specific."
        
        user_lower = user_input.lower()
        
        # Handle browsing requests
        if any(word in user_lower for word in ["show", "browse", "see", "looking for"]):
            if "mug" in user_lower:
                return await self.browse_catalog(context, category="mug")
            elif any(word in user_lower for word in ["clothing", "shirt", "hoodie"]):
                return await self.browse_catalog(context, category="clothing")
            elif "under" in user_lower and any(char.isdigit() for char in user_input):
                # Extract price
                price = int(''.join(filter(str.isdigit, user_input)))
                return await self.browse_catalog(context, max_price=price)
            elif any(color in user_lower for color in ["black", "blue", "white", "gray"]):
                color = next(color for color in ["black", "blue", "white", "gray"] if color in user_lower)
                return await self.browse_catalog(context, color=color)
        
        # Handle order requests
        if any(word in user_lower for word in ["buy", "order", "purchase", "want", "take"]):
            # Try to extract product reference
            if "first" in user_lower or "second" in user_lower or "third" in user_lower:
                return await self.place_order(context, user_input)
            elif any(color in user_lower for color in ["black", "blue", "white", "gray"]):
                return await self.place_order(context, user_input)
        
        # Handle status requests
        if any(word in user_lower for word in ["bought", "ordered", "last order", "recent"]):
            return await self.get_order_status(context)
        
        return "I can help you browse products, place orders, or check your order status. What would you like to do? Try saying 'show me mugs' or 'I want to buy something'."


def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()


async def entrypoint(ctx: JobContext):
    # Logging setup
    ctx.log_context_fields = {
        "room": ctx.room.name,
    }

    # Create agent instance
    agent = EcommerceAgent()

    # Set up a voice AI pipeline
    session = AgentSession(
        stt=deepgram.STT(model="nova-3"),
        llm=google.LLM(model="gemini-2.5-flash"),
        tts=murf.TTS(
            voice="en-US-matthew",
            style="Conversation",
            tokenizer=tokenize.basic.SentenceTokenizer(min_sentence_len=2),
            text_pacing=True
        ),
        turn_detection=MultilingualModel(),
        vad=ctx.proc.userdata["vad"],
        preemptive_generation=True,
    )

    # Metrics collection
    usage_collector = metrics.UsageCollector()

    @session.on("metrics_collected")
    def _on_metrics_collected(ev: MetricsCollectedEvent):
        metrics.log_metrics(ev.metrics)
        usage_collector.collect(ev.metrics)

    async def log_usage():
        summary = usage_collector.get_summary()
        logger.info(f"Usage: {summary}")

    ctx.add_shutdown_callback(log_usage)

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