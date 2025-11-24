import logging

from dotenv import load_dotenv
from order_helper import save_order_to_json, is_order_complete
from wellness_storage import save_wellness_entry, load_wellness_log
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
from livekit.plugins import murf, silero, google, deepgram, noise_cancellation
from livekit.plugins.turn_detector.multilingual import MultilingualModel

logger = logging.getLogger("agent")

load_dotenv(".env.local")


class WellnessCompanion(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""You are a warm, supportive Health & Wellness Companion. Your role is to provide emotional check-ins and gentle reflection, NOT medical advice.
            
            IMPORTANT: You do NOT diagnose, treat, or give medical advice. You simply listen and support.
            
            Your goal is to collect:
            - mood: How they're feeling emotionally
            - energy: Their energy level today
            - stressors: What's causing stress or concern
            - goals: 1-3 simple wellness goals for today
            - summary: A brief recap of the session
            
            Process:
            1. Check previous wellness entries to reference past check-ins
            2. Ask about their mood today
            3. Ask about their energy level
            4. Ask what's causing stress or concern
            5. Ask for 1-3 goals for today
            6. Provide a supportive recap
            7. Save the session using save_wellness_session tool
            
            Be conversational, warm, and grounded. Keep responses short and supportive.
            Reference previous entries when relevant: "Last time you mentioned feeling tired. How are you today?"
            
            Never use medical terms, diagnose, or give health advice.""",
        )
        self.wellness_state = {
            "mood": "",
            "energy": "",
            "stressors": "",
            "goals": [],
            "summary": ""
        }
        self.previous_entries = []
        self.session_started = False
        
    async def initialize_session(self):
        """Initialize session and load previous entries"""
        if not self.session_started:
            await self.load_previous_entries()
            self.session_started = True
            return self.get_session_greeting()
        return None
        
    def get_session_greeting(self):
        """Get appropriate greeting based on previous entries"""
        if not self.previous_entries:
            return "Hello! I'm here to check in with you today. How are you feeling?"
        
        last_entry = self.previous_entries[-1]
        
        # Reference goals from last session
        if "goals" in last_entry and last_entry["goals"]:
            goal = last_entry["goals"][0]
            return f"Hi there! I saw last time you wanted to {goal}. How did that go? Let's do today's check-in."
        
        # Reference mood from last session
        elif "mood" in last_entry and last_entry["mood"]:
            return f"Hello! Last time you were feeling {last_entry['mood']}. How are you today?"
        
        return "Hi! Good to see you back for another wellness check-in. How are you feeling today?"

    def is_complete(self):
        """Check if all required wellness fields are filled"""
        return all([
            self.wellness_state["mood"],
            self.wellness_state["energy"],
            self.wellness_state["stressors"],
            len(self.wellness_state["goals"]) > 0
        ])

    def reset_state(self):
        """Reset wellness state for next session"""
        self.wellness_state = {
            "mood": "",
            "energy": "",
            "stressors": "",
            "goals": [],
            "summary": ""
        }

    def update_state(self, field, value):
        """Update a specific field in wellness state"""
        if field == "goals":
            if value not in self.wellness_state["goals"]:
                self.wellness_state["goals"].append(value)
        else:
            self.wellness_state[field] = value

    def get_next_prompt(self):
        """Get the next question based on current state"""
        previous_context = ""
        if self.previous_entries:
            last_entry = self.previous_entries[-1]
            
        if not self.wellness_state["mood"]:
            if self.previous_entries and "mood" in self.previous_entries[-1]:
                previous_context = f"Last time you felt {self.previous_entries[-1]['mood']}. "
            return f"{previous_context}How are you feeling emotionally today?"
        elif not self.wellness_state["energy"]:
            if self.previous_entries and "energy" in self.previous_entries[-1]:
                previous_context = f"Last time your energy was {self.previous_entries[-1]['energy']}. "
            return f"{previous_context}What's your energy level like today?"
        elif not self.wellness_state["stressors"]:
            return "What's causing you stress or concern today? It's okay if nothing major."
        elif len(self.wellness_state["goals"]) == 0:
            return "What are 1 to 3 simple wellness goals you'd like to focus on today?"
        else:
            return "Is there anything else you'd like to add to your goals?"

    async def load_previous_entries(self):
        """Load previous wellness entries for context"""
        self.previous_entries = load_wellness_log()
        
    async def broadcast_state(self, wellness_state):
        """Send wellness state to frontend via data channel"""
        if self.room:
            await self.room.local_participant.publish_data(
                json.dumps({"type": "wellness_state", "data": wellness_state}).encode()
            )



    @function_tool
    async def update_wellness(self, context: RunContext, field: str, value: str):
        """Update wellness check-in information
        
        Args:
            field: The field to update (mood, energy, stressors, goals)
            value: The value to set for the field
        """
        self.room = context.room
        
        # Initialize session if first interaction
        greeting = await self.initialize_session()
        if greeting:
            # Return greeting and first question
            return f"{greeting} {self.get_next_prompt()}"
        
        # Update the state
        self.update_state(field, value)
        
        logger.info(f"Updated wellness: {self.wellness_state}")
        await self.broadcast_state(self.wellness_state)
        
        # Check if check-in is complete
        if self.is_complete():
            # Generate summary
            goals_text = ", ".join(self.wellness_state["goals"])
            summary = f"Feeling {self.wellness_state['mood']} with {self.wellness_state['energy']} energy. Stressors: {self.wellness_state['stressors']}. Goals: {goals_text}"
            self.wellness_state["summary"] = summary
            
            # Save the session directly using wellness_storage
            entry = {
                "mood": self.wellness_state["mood"],
                "energy": self.wellness_state["energy"],
                "stressors": self.wellness_state["stressors"],
                "goals": self.wellness_state["goals"],
                "summary": self.wellness_state["summary"]
            }
            
            success = save_wellness_entry(entry)
            result_msg = "Your wellness session has been saved successfully!" if success else "There was an issue saving your session."
            
            # Reset state for next session
            self.reset_state()
            
            return f"Here's your wellness recap: {summary}. {result_msg}"
        
        # Continue with next question  
        return self.get_next_prompt()

    @function_tool
    async def save_wellness_session(self, context: RunContext, mood: str, energy: str, stressors: str, goals: list, summary: str):
        """Save a wellness session entry
        
        Args:
            mood: Current mood state
            energy: Energy level
            stressors: What's causing stress
            goals: List of wellness goals
            summary: Session summary
        """
        entry = {
            "mood": mood,
            "energy": energy,
            "stressors": stressors,
            "goals": goals,
            "summary": summary
        }
        
        success = save_wellness_entry(entry)
        if success:
            return "Your wellness session has been saved successfully. Keep up the great work on your wellness journey!"
        else:
            return "There was an issue saving your wellness session. Please try again."


def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()


async def entrypoint(ctx: JobContext):
    # Logging setup
    # Add any other context you want in all log entries here
    ctx.log_context_fields = {
        "room": ctx.room.name,
    }

    # Set up a voice AI pipeline using OpenAI, Cartesia, AssemblyAI, and the LiveKit turn detector
    session = AgentSession(
        # Speech-to-text (STT) is your agent's ears, turning the user's speech into text that the LLM can understand
        # See all available models at https://docs.livekit.io/agents/models/stt/
        stt=deepgram.STT(model="nova-3"),
        # A Large Language Model (LLM) is your agent's brain, processing user input and generating a response
        # See all available models at https://docs.livekit.io/agents/models/llm/
        llm=google.LLM(
                model="gemini-2.5-flash",
            ),
        # Text-to-speech (TTS) is your agent's voice, turning the LLM's text into speech that the user can hear
        # See all available models as well as voice selections at https://docs.livekit.io/agents/models/tts/
        tts=murf.TTS(
                voice="en-US-matthew", 
                style="Conversation",
                tokenizer=tokenize.basic.SentenceTokenizer(min_sentence_len=2),
                text_pacing=True
            ),
        # VAD and turn detection are used to determine when the user is speaking and when the agent should respond
        # See more at https://docs.livekit.io/agents/build/turns
        turn_detection=MultilingualModel(),
        vad=ctx.proc.userdata["vad"],
        # allow the LLM to generate a response while waiting for the end of turn
        # See more at https://docs.livekit.io/agents/build/audio/#preemptive-generation
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

    # Start the session, which initializes the voice pipeline and warms up the models
    await session.start(
        agent=WellnessCompanion(),
        room=ctx.room,
        room_input_options=RoomInputOptions(
            # For telephony applications, use `BVCTelephony` for best results
            noise_cancellation=noise_cancellation.BVC(),
        ),
    )

    # Join the room and connect to the user
    await ctx.connect()


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint, prewarm_fnc=prewarm))
