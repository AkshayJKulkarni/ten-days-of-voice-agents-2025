import logging
import json
import os
from datetime import datetime
from dotenv import load_dotenv
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
from livekit.plugins import murf, silero, google, deepgram, noise_cancellation
from livekit.plugins.turn_detector.multilingual import MultilingualModel

logger = logging.getLogger("sdr_agent")
load_dotenv(".env.local")

class SDRAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""You are Priya, a friendly and professional Sales Development Representative from India. 

IMPORTANT: When users provide information, call collect_lead_field function with the appropriate field and value.
When users ask company questions, call answer_from_faq function.
When conversation ends, call save_lead_json function.

Use collect_lead_field for:
- name: when user provides their name
- company: when user mentions their company
- email: when user provides email
- role: when user mentions job title
- use_case: when user explains what they need
- team_size: when user mentions team size
- timeline: when user mentions implementation timeline

Greet warmly, ask what brought them here, and naturally collect information while answering their questions.""",
        )
        self.faq_data = self.load_faq()
        self.lead_data = {
            "name": "",
            "company": "",
            "email": "",
            "role": "",
            "use_case": "",
            "team_size": "",
            "timeline": "",
            "conversation_summary": "",
            "timestamp": ""
        }
        self.conversation_log = []
        self.room = None

    def load_faq(self):
        """Load FAQ data from JSON file"""
        try:
            faq_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "shared-data", "day5_company_faq.json")
            with open(faq_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load FAQ: {e}")
            return {}

    def is_end_of_call(self, text):
        """Detect end-of-call phrases"""
        end_phrases = [
            "goodbye", "bye", "thank you", "that's all", "i'm done", 
            "talk later", "speak soon", "have a good day", "thanks for your time",
            "i'll be in touch", "i need to go", "that's everything"
        ]
        return any(phrase in text.lower() for phrase in end_phrases)

    @function_tool
    async def answer_from_faq(self, context: RunContext, question: str):
        """Answer questions using FAQ data"""
        self.room = context.room
        self.conversation_log.append(f"User asked: {question}")
        
        question_lower = question.lower()
        
        # Check FAQ items
        for faq_item in self.faq_data.get("faqs", []):
            if any(word in question_lower for word in faq_item["question"].lower().split()):
                answer = faq_item["answer"]
                self.conversation_log.append(f"Agent answered: {answer}")
                return answer
        
        # Check other sections
        if "about" in question_lower or "company" in question_lower:
            answer = self.faq_data.get("about", "I don't have that information available.")
            self.conversation_log.append(f"Agent answered: {answer}")
            return answer
        elif "product" in question_lower or "features" in question_lower:
            answer = self.faq_data.get("product_overview", "I don't have that information available.")
            self.conversation_log.append(f"Agent answered: {answer}")
            return answer
        elif "pricing" in question_lower or "cost" in question_lower:
            answer = self.faq_data.get("pricing", "I don't have that information available.")
            self.conversation_log.append(f"Agent answered: {answer}")
            return answer
        
        return "That's a great question! Let me connect you with our technical team who can provide detailed information about that."

    @function_tool
    async def collect_lead_field(self, context: RunContext, field: str, value: str):
        """Collect lead information"""
        self.room = context.room
        self.lead_data[field] = value
        self.conversation_log.append(f"Collected {field}: {value}")
        
        logger.info(f"Collected lead field - {field}: {value}")
        
        # Check if conversation is ending
        if self.is_end_of_call(value):
            return await self.save_lead_json(context)
        
        # Guide conversation based on missing fields
        missing_fields = [k for k, v in self.lead_data.items() 
                         if not v and k not in ["conversation_summary", "timestamp"]]
        
        if missing_fields:
            if "name" in missing_fields:
                return "Great! And may I have your name please?"
            elif "company" in missing_fields:
                return "Perfect! Which company are you with?"
            elif "role" in missing_fields:
                return "Wonderful! What's your role there?"
            elif "email" in missing_fields:
                return "Excellent! Could I get your business email?"
            elif "use_case" in missing_fields:
                return "That sounds interesting! What specific use case are you looking to solve?"
            elif "team_size" in missing_fields:
                return "Got it! How large is your team?"
            elif "timeline" in missing_fields:
                return "Perfect! When are you looking to implement this?"
        
        return "Thank you for that information! Is there anything else you'd like to know about our platform?"

    @function_tool
    async def save_lead_json(self, context: RunContext):
        """Save lead data to JSON file"""
        try:
            # Generate conversation summary
            summary = f"Lead qualification call with {self.lead_data.get('name', 'prospect')} from {self.lead_data.get('company', 'unknown company')}. "
            summary += f"Role: {self.lead_data.get('role', 'not specified')}. "
            summary += f"Use case: {self.lead_data.get('use_case', 'not specified')}. "
            summary += f"Timeline: {self.lead_data.get('timeline', 'not specified')}."
            
            self.lead_data["conversation_summary"] = summary
            self.lead_data["timestamp"] = datetime.now().isoformat()
            self.lead_data["conversation_log"] = self.conversation_log
            
            # Save to output directory
            output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "output")
            os.makedirs(output_dir, exist_ok=True)
            
            output_path = os.path.join(output_dir, "lead_data.json")
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(self.lead_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Lead data saved to {output_path}")
            
            # Provide spoken summary
            spoken_summary = f"Thank you so much for your time today! Just to recap: I spoke with {self.lead_data.get('name', 'you')} "
            if self.lead_data.get('company'):
                spoken_summary += f"from {self.lead_data['company']} "
            spoken_summary += f"about implementing our conversational AI platform. "
            if self.lead_data.get('use_case'):
                spoken_summary += f"You're looking to {self.lead_data['use_case']} "
            if self.lead_data.get('timeline'):
                spoken_summary += f"with a timeline of {self.lead_data['timeline']}. "
            spoken_summary += "Our team will follow up with you shortly. Have a wonderful day!"
            
            return spoken_summary
            
        except Exception as e:
            logger.error(f"Failed to save lead data: {e}")
            return "Thank you for your time! Our team will be in touch soon."

def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()

async def entrypoint(ctx: JobContext):
    ctx.log_context_fields = {"room": ctx.room.name}

    session = AgentSession(
        stt=deepgram.STT(model="nova-3"),
        llm=google.LLM(model="gemini-2.5-flash"),
        tts=murf.TTS(
            voice="en-IN-neerja", 
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
        agent=SDRAgent(),
        room=ctx.room,
        room_input_options=RoomInputOptions(
            noise_cancellation=noise_cancellation.BVC(),
        ),
    )

    await ctx.connect()

if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint, prewarm_fnc=prewarm))