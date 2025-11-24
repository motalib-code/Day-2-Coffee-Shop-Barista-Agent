import logging
import json
from datetime import datetime
from pathlib import Path

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
from livekit import rtc

logger = logging.getLogger("agent")

load_dotenv(".env.local")

# Create orders directory if it doesn't exist
ORDERS_DIR = Path(__file__).parent.parent / "orders"
ORDERS_DIR.mkdir(exist_ok=True)


class Assistant(Agent):
    def __init__(self, room: rtc.Room) -> None:
        super().__init__(
            instructions="""You are a friendly barista at Brew Haven Coffee Shop. The user is interacting with you via voice.
            
            Your job is to take coffee orders and gather all necessary information:
            - Drink type (e.g., latte, cappuccino, americano, espresso, mocha, cold brew)
            - Size (small, medium, large)
            - Milk preference (whole, skim, oat, almond, soy, or none)
            - Any extras (whipped cream, extra shot, vanilla syrup, caramel syrup, etc.)
            - Customer's name for the order
            
            Be conversational and friendly. Ask clarifying questions one at a time if information is missing.
            Once you have all the information, use the save_order tool to finalize the order.
            
            Your responses are concise, warm, and natural - like a real barista would speak.
            Don't use complex formatting, emojis, or asterisks in your responses.""",
        )
        self.room = room
        
        # Initialize order state
        self.order_state = {
            "drinkType": None,
            "size": None,
            "milk": None,
            "extras": [],
            "name": None
        }

    async def _update_display(self):
        """Generate HTML and publish it to the room."""
        html = self._generate_html()
        try:
            await self.room.local_participant.publish_data(
                payload=html.encode("utf-8"),
                topic="drink_visualization"
            )
            logger.info("Published drink visualization")
        except Exception as e:
            logger.error(f"Failed to publish data: {e}")

    def _generate_html(self) -> str:
        """Generate HTML representation of the drink."""
        state = self.order_state
        
        # Determine cup size
        height = "150px" # Default medium
        if state["size"] == "small": height = "120px"
        if state["size"] == "large": height = "180px"
        
        # Determine drink color
        color = "#6F4E37" # Coffee brown
        dtype = state["drinkType"] or ""
        if "latte" in dtype: color = "#C8A2C8" # Light brown/beige (approx) - actually #D2B48C is tan
        if "milk" in dtype: color = "#D2B48C"
        if "matcha" in dtype: color = "#90EE90"
        if "black" in dtype or "espresso" in dtype: color = "#3b2f2f"
        
        # Extras visuals
        extras_html = ""
        if "whipped" in str(state["extras"]):
            extras_html += '<div style="position: absolute; top: -20px; left: 10%; width: 80%; height: 30px; background: white; border-radius: 50% 50% 0 0;"></div>'
            
        # Summary text
        summary = f"{state['size'] or '???'} {state['drinkType'] or 'Coffee'}"
        if state['name']:
            summary += f" for {state['name']}"
            
        html = f"""
        <div style="font-family: sans-serif; text-align: center; padding: 20px; background: #f5f5f5; border-radius: 10px;">
            <h2>Brew Haven Order</h2>
            <div style="display: flex; justify-content: center; align-items: flex-end; height: 250px; margin: 20px 0;">
                <div style="position: relative; width: 100px; height: {height}; background: {color}; border-radius: 0 0 15px 15px; border: 2px solid #333;">
                    <div style="position: absolute; top: 10px; right: -20px; width: 20px; height: 40px; border: 2px solid #333; border-left: none; border-radius: 0 10px 10px 0;"></div>
                    {extras_html}
                </div>
            </div>
            <div style="background: white; padding: 10px; border-radius: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
                <p><strong>Name:</strong> {state['name'] or '...'}</p>
                <p><strong>Drink:</strong> {state['drinkType'] or '...'}</p>
                <p><strong>Size:</strong> {state['size'] or '...'}</p>
                <p><strong>Milk:</strong> {state['milk'] or '...'}</p>
                <p><strong>Extras:</strong> {', '.join(state['extras']) if state['extras'] else 'None'}</p>
            </div>
        </div>
        """
        return html

    @function_tool
    async def save_order(self, context: RunContext):
        """Use this tool when all order information has been collected (drink type, size, milk, extras, and customer name).
        This finalizes the order and saves it to a file.
        """
        
        # Validate that all required fields are filled
        if not all([
            self.order_state["drinkType"],
            self.order_state["size"],
            self.order_state["milk"] is not None,  # Can be empty string for "none"
            self.order_state["name"]
        ]):
            missing = []
            if not self.order_state["drinkType"]:
                missing.append("drink type")
            if not self.order_state["size"]:
                missing.append("size")
            if self.order_state["milk"] is None:
                missing.append("milk preference")
            if not self.order_state["name"]:
                missing.append("customer name")
            
            return f"Cannot save order yet. Still missing: {', '.join(missing)}"
        
        # Create order with timestamp
        order = {
            **self.order_state,
            "timestamp": datetime.now().isoformat(),
            "status": "pending"
        }
        
        # Save to JSON file
        filename = f"order_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{self.order_state['name']}.json"
        filepath = ORDERS_DIR / filename
        
        with open(filepath, 'w') as f:
            json.dump(order, f, indent=2)
        
        logger.info(f"Order saved: {filepath}")
        
        # Update display one last time
        await self._update_display()
        
        # Create a nice summary
        extras_text = ", ".join(self.order_state["extras"]) if self.order_state["extras"] else "none"
        milk_text = self.order_state["milk"] if self.order_state["milk"] else "no milk"
        
        summary = f"""Order confirmed for {self.order_state['name']}!
{self.order_state['size'].capitalize()} {self.order_state['drinkType']} with {milk_text}.
Extras: {extras_text}.
Your order will be ready shortly!"""
        
        return summary

    @function_tool
    async def update_drink_type(self, context: RunContext, drink_type: str):
        """Update the drink type in the order.
        
        Args:
            drink_type: The type of coffee drink (e.g., latte, cappuccino, americano, espresso, mocha, cold brew)
        """
        self.order_state["drinkType"] = drink_type.lower()
        logger.info(f"Updated drink type: {drink_type}")
        await self._update_display()
        return f"Got it, {drink_type}"

    @function_tool
    async def update_size(self, context: RunContext, size: str):
        """Update the size in the order.
        
        Args:
            size: The size of the drink (small, medium, or large)
        """
        size_lower = size.lower()
        if size_lower not in ["small", "medium", "large"]:
            return "Please choose small, medium, or large"
        
        self.order_state["size"] = size_lower
        logger.info(f"Updated size: {size}")
        await self._update_display()
        return f"Got it, {size}"

    @function_tool
    async def update_milk(self, context: RunContext, milk: str):
        """Update the milk preference in the order.
        
        Args:
            milk: The type of milk (whole, skim, oat, almond, soy, or none)
        """
        self.order_state["milk"] = milk.lower()
        logger.info(f"Updated milk: {milk}")
        await self._update_display()
        return f"Got it, {milk}"

    @function_tool
    async def add_extra(self, context: RunContext, extra: str):
        """Add an extra item to the order.
        
        Args:
            extra: An extra item (e.g., whipped cream, extra shot, vanilla syrup, caramel syrup)
        """
        if extra.lower() not in self.order_state["extras"]:
            self.order_state["extras"].append(extra.lower())
            logger.info(f"Added extra: {extra}")
            await self._update_display()
            return f"Added {extra}"
        return f"{extra} is already in your order"

    @function_tool
    async def update_name(self, context: RunContext, name: str):
        """Update the customer name for the order.
        
        Args:
            name: The customer's name
        """
        self.order_state["name"] = name
        logger.info(f"Updated name: {name}")
        await self._update_display()
        return f"Got it, {name}"


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
        agent=Assistant(room=ctx.room),
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
