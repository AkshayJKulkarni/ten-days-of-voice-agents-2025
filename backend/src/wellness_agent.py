import logging
from dotenv import load_dotenv
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

logger = logging.getLogger("wellness_agent")
load_dotenv(".env.local")

class WellnessCompanion(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""You are a warm, supportive Health & Wellness Companion. 
            
            Your role is to conduct daily wellness check-ins. You do NOT diagnose or give medical advice.
            
            IMPORTANT: When users provide wellness information, call update_wellness function with the appropriate field and value.
            
            Use update_wellness for:
            - mood: when user describes how they're feeling
            - energy: when user mentions energy level
            - stressors: when user mentions stress or concerns
            - goals: when user mentions wellness goals
            
            Ask one question at a time. Be warm, supportive, and conversational.
            Reference previous sessions when available.""",
        )
        self.wellness_state = {
            "mood": "",
            "energy": "",
            "stressors": "",
            "goals": [],
            "summary": ""
        }
        self.room = None

    @function_tool
    async def update_wellness(self, context: RunContext, field: str, value: str):
        """Update wellness check-in information"""
        if field == "goals":
            if value not in self.wellness_state["goals"]:
                self.wellness_state["goals"].append(value)
        else:
            self.wellness_state[field] = value
        
        self.room = context.room
        logger.info(f"Updated wellness: {self.wellness_state}")
        
        # Check if complete
        if all([
            self.wellness_state["mood"],
            self.wellness_state["energy"], 
            self.wellness_state["stressors"],
            len(self.wellness_state["goals"]) > 0
        ]):
            # Generate summary
            goals_text = ", ".join(self.wellness_state["goals"])
            summary = f"Feeling {self.wellness_state['mood']} with {self.wellness_state['energy']} energy, and focused on {goals_text} today."
            self.wellness_state["summary"] = summary
            
            # Save entry
            save_wellness_entry(self.wellness_state.copy())
            
            # Reset for next session
            self.wellness_state = {
                "mood": "",
                "energy": "",
                "stressors": "",
                "goals": [],
                "summary": ""
            }
            
            return f"Thank you for sharing. Here's your recap: {summary}. Your wellness session has been saved!"
        
        # Continue with next question
        if not self.wellness_state["mood"]:
            return "How are you feeling today?"
        elif not self.wellness_state["energy"]:
            return "What's your energy level like?"
        elif not self.wellness_state["stressors"]:
            return "What's causing you stress or concern today?"
        elif len(self.wellness_state["goals"]) == 0:
            return "What are 1-3 wellness goals you'd like to focus on today?"
        
        return "Anything else you'd like to add?"

def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()

async def entrypoint(ctx: JobContext):
    ctx.log_context_fields = {"room": ctx.room.name}

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

    usage_collector = metrics.UsageCollector()

    @session.on("metrics_collected")
    def _on_metrics_collected(ev: MetricsCollectedEvent):
        metrics.log_metrics(ev.metrics)
        usage_collector.collect(ev.metrics)

    async def log_usage():
        summary = usage_collector.get_summary()
        logger.info(f"Usage: {summary}")

    ctx.add_shutdown_callback(log_usage)

    await session.start(
        agent=WellnessCompanion(),
        room=ctx.room,
        room_input_options=RoomInputOptions(
            noise_cancellation=noise_cancellation.BVC(),
        ),
    )

    await ctx.connect()

if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint, prewarm_fnc=prewarm))