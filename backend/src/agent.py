import logging

from dotenv import load_dotenv
from tutor_content import load_course_content, select_concept, get_available_concepts
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


class TeachTheTutor(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""You are a supportive programming tutor with three modes:
            
            LEARN MODE: Explain programming concepts clearly using provided summaries
            QUIZ MODE: Ask questions to test understanding  
            TEACH_BACK MODE: Have students explain concepts back to you and provide encouraging feedback
            
            Always be supportive, patient, and encouraging. Never make students feel bad about mistakes.
            Use simple language appropriate for beginners. Keep explanations clear and concise.
            
            Available concepts: variables, loops, functions, conditionals
            
            Process:
            1. Ask user which mode they prefer (learn, quiz, or teach_back)
            2. Ask which concept they want to work on
            3. Execute the chosen mode
            4. After completion, offer to switch modes or concepts
            
            Be encouraging and supportive throughout the learning process.""",
        )
        self.current_mode = ""
        self.current_concept = None
        self.session_started = False
        self.available_concepts = get_available_concepts()
        self.room = None

    def get_voice_for_mode(self, mode):
        """Get appropriate voice for each mode"""
        voices = {
            "learn": "en-US-matthew",
            "quiz": "en-US-alicia", 
            "teach_back": "en-US-ken"
        }
        return voices.get(mode, "en-US-matthew")
    
    def evaluate_teach_back_response(self, user_explanation, concept_title):
        """Generate encouraging feedback for teach_back mode"""
        explanation_lower = user_explanation.lower()
        concept_lower = concept_title.lower()
        
        # Identify strengths
        strengths = []
        if concept_lower in explanation_lower:
            strengths.append("you mentioned the concept by name")
        if any(word in explanation_lower for word in ["example", "like", "such as"]):
            strengths.append("you provided examples")
        if any(word in explanation_lower for word in ["use", "used", "help", "allows"]):
            strengths.append("you explained how it's used")
        if len(user_explanation.split()) > 10:
            strengths.append("you gave a detailed explanation")
        if any(word in explanation_lower for word in ["store", "contain", "hold"]) and "variable" in concept_lower:
            strengths.append("you understood the storage concept")
        if any(word in explanation_lower for word in ["repeat", "again", "multiple"]) and "loop" in concept_lower:
            strengths.append("you grasped the repetition idea")
        
        # Default strengths if none detected
        if not strengths:
            strengths = ["you attempted to explain the concept", "you're engaging with the material"]
        
        # Select up to 2 strengths
        selected_strengths = strengths[:2]
        
        # Generate suggestions based on concept
        suggestions = {
            "variables": "try mentioning how variables can store different types of data",
            "loops": "consider explaining when you might use a loop in real programming",
            "functions": "think about how functions help organize and reuse code",
            "conditionals": "try describing how if statements help programs make decisions"
        }
        
        suggestion = suggestions.get(concept_lower, "try adding a simple example next time")
        
        # Build encouraging response
        strengths_text = " and ".join(selected_strengths)
        return f"Great effort! I noticed {strengths_text}. To make it even better, {suggestion}. You're doing well with programming concepts!"



    @function_tool
    async def detect_intent(self, context: RunContext, user_input: str):
        """Detect user intent for mode switching and concept selection
        
        Args:
            user_input: What the user said
        """
        self.room = context.room
        
        if not self.session_started:
            self.session_started = True
            return "Hi! I'm your programming tutor. Which mode would you like: learn, quiz, or teach_back? And which concept: variables, loops, functions, or conditionals?"
        
        user_lower = user_input.lower()
        
        # Detect mode switching intents
        if "learn mode" in user_lower or "switch to learn" in user_lower:
            return self.switch_mode("learn")
        elif "quiz mode" in user_lower or "switch to quiz" in user_lower:
            return self.switch_mode("quiz")
        elif "teach back mode" in user_lower or "teach_back mode" in user_lower or "switch to teach back" in user_lower:
            return self.switch_mode("teach_back")
        
        # Detect concept selection
        for concept_id in self.available_concepts:
            if concept_id in user_lower:
                self.current_concept = select_concept(concept_id)
                if self.current_mode:
                    return self.execute_mode()
                else:
                    return f"Great! I've selected {concept_id}. Now which mode would you like: learn, quiz, or teach_back?"
        
        # Default response
        if not self.current_concept:
            return "Please choose a concept first: variables, loops, functions, or conditionals."
        elif not self.current_mode:
            return "Which mode would you like: learn, quiz, or teach_back?"
        else:
            return "I'm ready to help! What would you like to do?"
    
    def switch_mode(self, new_mode):
        """Switch to a new mode while preserving concept"""
        self.current_mode = new_mode
        self.broadcast_tutor_state()
        
        if not self.current_concept:
            return f"Switched to {new_mode} mode! Please choose a concept: variables, loops, functions, or conditionals."
        
        return self.execute_mode()
    
    async def broadcast_tutor_state(self):
        """Send current tutor state to frontend"""
        if self.room:
            state = {
                "mode": self.current_mode,
                "concept": self.current_concept.get('title', '') if self.current_concept else ''
            }
            await self.room.local_participant.publish_data(
                json.dumps({"type": "tutor_state", "data": state}).encode()
            )
    
    @function_tool
    async def set_concept(self, context: RunContext, concept_id: str):
        """Set the concept to work on
        
        Args:
            concept_id: The concept ID (variables, loops, functions, conditionals)
        """
        if concept_id not in self.available_concepts:
            return f"Please choose from: {', '.join(self.available_concepts)}"
        
        self.current_concept = select_concept(concept_id)
        await self.broadcast_tutor_state()
        
        if self.current_mode:
            return self.execute_mode()
        else:
            return f"Great! I've selected {concept_id}. Now which mode would you like: learn, quiz, or teach_back?"
    
    def execute_mode(self):
        """Execute the current mode"""
        if not self.current_concept:
            return "Please select a concept first."
        
        concept = self.current_concept
        
        if self.current_mode == "learn":
            return f"Let me explain {concept['title']}. {concept['summary']} Would you like me to explain another concept or switch modes?"
        
        elif self.current_mode == "quiz":
            return f"Quiz time! {concept['sample_question']} Take your time to think about it."
        
        elif self.current_mode == "teach_back":
            return f"Now it's your turn! Can you explain {concept['title']} back to me in your own words? Don't worry about being perfect."
        
        return "Please choose a mode: learn, quiz, or teach_back."
    
    @function_tool
    async def give_feedback(self, context: RunContext, student_response: str):
        """Provide feedback on student's explanation
        
        Args:
            student_response: What the student said
        """
        if self.current_mode == "teach_back" and self.current_concept:
            feedback = self.evaluate_teach_back_response(student_response, self.current_concept['title'])
            return f"{feedback} Would you like to try another concept or switch to a different mode?"
        elif self.current_mode == "quiz":
            return "Nice work on that question! Learning programming takes practice. Want to try another concept or mode?"
        else:
            return "Would you like to switch modes or try a different concept?"


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
