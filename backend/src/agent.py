import logging

from dotenv import load_dotenv
from faq_loader import load_faq_data
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


class SalesSDR(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""You are a warm, friendly Sales Development Representative (SDR) for our company.
            
            Your role is to:
            1. Greet visitors warmly and make them feel welcome
            2. Ask what brought them here and what they need help with
            3. Keep conversations focused on understanding their needs
            4. Use ONLY the FAQ content to answer product/company/pricing questions - DO NOT hallucinate
            5. Naturally collect lead information throughout the conversation
            6. When they're done, provide a summary and save their information
            
            Lead information to collect:
            - name: Their full name
            - company: Company they work for
            - email: Contact email
            - role: Their job title/role
            - use_case: What they want to use our product for
            - team_size: Size of their team
            - timeline: When they're looking to implement
            
            Conversation flow:
            - Start with warm greeting
            - Ask what brought them here
            - Listen to their needs and answer from FAQ
            - Naturally weave in lead qualification questions
            - When they say "that's all", "I'm done", "thank you" etc., summarize and save
            
            Be conversational, helpful, and professional. Focus on their needs first, qualification second.""",
        )
        # Use global lead_state
        global lead_state
        self.lead_state = lead_state
        self.session_started = False
        self.conversation_complete = False
        self.room = None
        
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
        
        # Check for end-of-call
        if self.detect_end_of_call(user_input):
            summary = self.generate_lead_summary()
            if any(self.lead_state.values()):
                self.save_lead_to_json()
            self.reset_lead_state()
            return f"{summary} Have a great day!"
        
        # Try to find FAQ answer first
        faq_answer = self.find_faq_answer(user_input)
        if faq_answer:
            # After answering FAQ, ask for missing info if needed
            missing_info_question = self.ask_for_missing_info()
            if missing_info_question:
                return f"{faq_answer} {missing_info_question}"
            return faq_answer
        
        # Extract lead information from user input
        self.extract_lead_info(user_input)
        
        # Ask for missing information
        missing_info_question = self.ask_for_missing_info()
        if missing_info_question:
            return missing_info_question
        
        # Default helpful response
        return "That's great! Is there anything else about our product or company you'd like to know?"
    
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
