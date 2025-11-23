import logging

from dotenv import load_dotenv
from order_helper import save_order_to_json, is_order_complete
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


class CoffeeShopBarista(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""You are a friendly coffee shop barista. Your job is to take coffee orders step by step.
            You must collect: drink type, size, milk preference, extras, and customer name.
            
            IMPORTANT: When the customer provides any order information, you MUST call the update_order function with the appropriate field and value.
            
            Use update_order function for:
            - drinkType: when customer says what drink they want
            - size: when customer says small, medium, large
            - milk: when customer mentions milk type
            - extras: when customer mentions extras like sugar, vanilla, etc.
            - name: when customer provides their name
            
            Ask one question at a time and be conversational. Keep responses short and friendly.
            Guide customers through the ordering process systematically.
            Don't use complex formatting, emojis, or symbols in your responses.""",
        )
        self.order_state = {
            "drinkType": "",
            "size": "",
            "milk": "",
            "extras": [],
            "name": ""
        }
        self.room = None

    async def broadcast_state(self, order_state):
        """Send order state to frontend via data channel"""
        if self.room:
            await self.room.local_participant.publish_data(
                json.dumps({"type": "order_state", "data": order_state}).encode()
            )



    @function_tool
    async def update_order(self, context: RunContext, field: str, value: str):
        """Update a field in the order state
        
        Args:
            field: The field to update (drinkType, size, milk, extras, name)
            value: The value to set for the field
        """
        if field == "extras":
            if value not in self.order_state["extras"]:
                self.order_state["extras"].append(value)
        else:
            self.order_state[field] = value
        
        self.room = context.room
        logger.info(f"Updated order: {self.order_state}")
        
        await self.broadcast_state(self.order_state)
        
        if is_order_complete(self.order_state):
            filepath = save_order_to_json(self.order_state)
            await self.room.local_participant.publish_data(
                json.dumps({"type": "order_complete", "data": self.order_state}).encode()
            )
            await context.send_data(
                json.dumps({"type": "final_order", "data": self.order_state}).encode()
            )
            # Reset order state for next customer
            self.order_state = {
                "drinkType": "",
                "size": "",
                "milk": "",
                "extras": [],
                "name": ""
            }
            return f"Your order is complete! Saving it now. Order saved successfully."
        
        # Guide to next step
        if not self.order_state["drinkType"]:
            return "What drink would you like today?"
        elif not self.order_state["size"]:
            return "What size would you like? Small, medium, or large?"
        elif not self.order_state["milk"]:
            return "What type of milk would you prefer? Whole, skim, oat, almond, or soy?"
        elif not self.order_state["name"]:
            return "Any extras like sugar, vanilla, or whipped cream? If not, just say none. Also, what name should I put on the order?"
        
        return "Let me know if you need anything else!"


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
        agent=CoffeeShopBarista(),
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
