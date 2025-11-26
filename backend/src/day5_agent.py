import logging
import json
from datetime import datetime
from pathlib import Path
from typing import Annotated, Optional

from dotenv import load_dotenv
from livekit import rtc
from livekit.agents import (
    Agent,
    AgentSession,
    JobContext,
    JobProcess,
    MetricsCollectedEvent,
    RoomInputOptions,
    RunContext,
    WorkerOptions,
    cli,
    function_tool,
    metrics,
    tokenize,
)
from livekit.plugins import murf, silero, google, deepgram, noise_cancellation
from livekit.plugins.turn_detector.multilingual import MultilingualModel

logger = logging.getLogger("day5_agent")

load_dotenv(".env.local")

# Paths
CONTENT_FILE = Path(__file__).parent.parent / "shared-data" / "day5_sdr_content.json"
LEADS_DIR = Path(__file__).parent.parent / "leads"
LEADS_DIR.mkdir(exist_ok=True)

class SDRAgent(Agent):
    def __init__(self, room: rtc.Room) -> None:
        self.content = self._load_content()
        
        super().__init__(
            instructions=f"""You are Riya, a Sales Development Representative (SDR) for Razorpay, India's leading payments company.
            
            Your goal is to:
            1. Qualify the lead by gathering key information.
            2. Answer their questions about Razorpay using the provided knowledge base.
            3. Be friendly, professional, and helpful.
            
            **Company Info**:
            {json.dumps(self.content['company'])}
            
            **Products**:
            {json.dumps(self.content['products'])}
            
            **Pricing**:
            {json.dumps(self.content['pricing'])}
            
            **FAQs**:
            {json.dumps(self.content['faqs'])}
            
            **Lead Qualification Fields to Collect**:
            - Name
            - Company Name
            - Role/Designation
            - Use Case (What do they want to use Razorpay for?)
            - Team Size
            - Timeline (When do they want to go live?)
            - Email Address
            
            **Conversation Flow**:
            1. **Greeting**: "Hi, this is Riya from Razorpay. Thanks for reaching out! What brings you here today?"
            2. **Discovery**: Ask about their business and needs. Naturally weave in the qualification questions. Don't interrogate them; make it conversational.
            3. **Answering**: If they ask about pricing or features, answer using the provided JSON data. If you don't know, say you'll check with a specialist.
            4. **Closing**: Once you have enough info or the user is done, summarize what you've heard and say you'll have a specialist reach out. Use the `finalize_call` tool.
            
            **Important**:
            - Always update the lead details using `update_lead_info` as you learn new things.
            - If the user says "I'm done", "That's all", or "Thanks", initiate the closing sequence and call `finalize_call`.
            """,
        )
        self.room = room
        self.lead_data = {
            "name": None,
            "company": None,
            "role": None,
            "use_case": None,
            "team_size": None,
            "timeline": None,
            "email": None,
            "notes": []
        }

    def _load_content(self) -> dict:
        try:
            with open(CONTENT_FILE) as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load content: {e}")
            return {"company": {}, "products": [], "pricing": {}, "faqs": []}

    @function_tool
    async def update_lead_info(
        self, 
        context: RunContext, 
        name: Optional[str] = None,
        company: Optional[str] = None,
        role: Optional[str] = None,
        use_case: Optional[str] = None,
        team_size: Optional[str] = None,
        timeline: Optional[str] = None,
        email: Optional[str] = None
    ):
        """Update the lead's information as you gather it during the conversation.
        Call this tool whenever the user provides new details.
        """
        updates = []
        if name:
            self.lead_data["name"] = name
            updates.append(f"name: {name}")
        if company:
            self.lead_data["company"] = company
            updates.append(f"company: {company}")
        if role:
            self.lead_data["role"] = role
            updates.append(f"role: {role}")
        if use_case:
            self.lead_data["use_case"] = use_case
            updates.append(f"use_case: {use_case}")
        if team_size:
            self.lead_data["team_size"] = team_size
            updates.append(f"team_size: {team_size}")
        if timeline:
            self.lead_data["timeline"] = timeline
            updates.append(f"timeline: {timeline}")
        if email:
            self.lead_data["email"] = email
            updates.append(f"email: {email}")
            
        if updates:
            logger.info(f"Updated lead info: {', '.join(updates)}")
            return f"Updated: {', '.join(updates)}"
        return "No updates provided."

    @function_tool
    async def get_pricing_info(self, context: RunContext):
        """Get detailed pricing information for Razorpay products."""
        return json.dumps(self.content['pricing'])

    @function_tool
    async def lookup_faq(self, context: RunContext, query: str):
        """Search the FAQ database for an answer to a specific question.
        
        Args:
            query: The topic or question the user is asking about.
        """
        # Simple keyword search
        query_lower = query.lower()
        matches = []
        for faq in self.content['faqs']:
            if query_lower in faq['question'].lower() or query_lower in faq['answer'].lower():
                matches.append(f"Q: {faq['question']}\nA: {faq['answer']}")
        
        if matches:
            return "\n\n".join(matches)
        
        return "I couldn't find a specific FAQ entry for that. Please answer based on general knowledge or offer to connect them with support."

    @function_tool
    async def finalize_call(self, context: RunContext):
        """End the call, save the lead data, and provide a verbal summary.
        Call this when the user indicates they are done or you have collected all necessary information.
        """
        # Save to JSON
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"lead_{timestamp}_{self.lead_data['name'] or 'unknown'}.json"
        filepath = LEADS_DIR / filename
        
        final_data = {
            "timestamp": datetime.now().isoformat(),
            "lead_details": self.lead_data,
            "status": "qualified" if self.lead_data['email'] else "partial"
        }
        
        try:
            with open(filepath, 'w') as f:
                json.dump(final_data, f, indent=2)
            logger.info(f"Lead saved to {filepath}")
        except Exception as e:
            logger.error(f"Failed to save lead: {e}")
            return "I encountered an error saving the lead details."

        # Generate summary for the user
        summary = "Thanks for your time! "
        if self.lead_data['name']:
            summary += f"It was great speaking with you, {self.lead_data['name']}. "
        
        summary += "I've noted that "
        points = []
        if self.lead_data['company']:
            points.append(f"you're from {self.lead_data['company']}")
        if self.lead_data['use_case']:
            points.append(f"you're looking to use Razorpay for {self.lead_data['use_case']}")
        if self.lead_data['timeline']:
            points.append(f"you want to start {self.lead_data['timeline']}")
            
        if points:
            summary += ", ".join(points) + "."
        else:
            summary += "you're interested in our services."
            
        summary += " I'll have one of our specialists reach out to you at "
        summary += self.lead_data['email'] if self.lead_data['email'] else "your email"
        summary += " with next steps. Have a great day!"
        
        return summary

def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()

async def entrypoint(ctx: JobContext):
    # Logging setup
    ctx.log_context_fields = {
        "room": ctx.room.name,
    }

    # Set up voice AI pipeline
    session = AgentSession(
        stt=deepgram.STT(model="nova-3"),
        llm=google.LLM(model="gemini-2.5-flash"),
        tts=murf.TTS(
            voice="en-US-terra", # Professional female voice suitable for SDR
            style="Promo",
            tokenizer=tokenize.basic.SentenceTokenizer(min_sentence_len=2),
            text_pacing=True,
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
        agent=SDRAgent(room=ctx.room),
        room=ctx.room,
        room_input_options=RoomInputOptions(
            noise_cancellation=noise_cancellation.BVC(),
        ),
    )

    # Join the room and connect to the user
    await ctx.connect()

if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint, prewarm_fnc=prewarm))
