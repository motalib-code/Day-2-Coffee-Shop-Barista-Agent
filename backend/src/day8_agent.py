import logging
import json
import random
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
import uuid

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

logger = logging.getLogger("day8_agent")

load_dotenv(".env.local")

# Paths
SAVES_FILE = Path(__file__).parent.parent / "day8_saves.json"

class GameMasterAgent(Agent):
    def __init__(self, room: rtc.Room) -> None:
        super().__init__(
            instructions="""You are the Ultimate Game Master, capable of running interactive adventures in any setting.

            **Your Goal:**
            Guide the player through an immersive, interactive story. You describe the scenes, play the NPCs, and adjudicate the rules.

            **Phase 1: Setup**
            - If the game hasn't started (no universe selected), ask the player what kind of adventure they want to play.
            - Options: "Classic Fantasy", "Cyberpunk Sci-Fi", "Zombie Apocalypse", or "Custom".
            - Once they choose, initialize the game by setting the tone and describing the opening scene.

            **Phase 2: The Adventure**
            - **Describe**: Paint a vivid picture of the current scene. Use sensory details (sight, sound, smell).
            - **Interact**: Ask "What do you do?" or offer choices.
            - **React**: When the player speaks, interpret their actions.
            - **Mechanics**: 
                - If the player attempts something risky or uncertain, use the `roll_dice` tool.
                - If the player asks about their status or inventory, use the `check_status` or `check_inventory` tools.
                - If the player finds an item, use `update_inventory` to add it.
                - If the player gets hurt or heals, use `update_health`.
            
            **Rules of Engagement:**
            - Keep descriptions concise but evocative (voice is linear, don't ramble).
            - Be a fan of the player's character, but make challenges real.
            - Maintain continuity. Remember names, locations, and past actions.
            - Drive towards a "mini-arc" conclusion (e.g., finding the artifact, escaping the city) within 10-15 turns.

            **Tools:**
            - ALWAYS use `roll_dice` for uncertain outcomes. Don't just decide arbitrarily.
            - Keep the `world_state` updated via tools.
            
            **Tone:**
            - Adapt to the chosen universe (e.g., grandiose for Fantasy, gritty for Cyberpunk).
            - Always remain in character as the Narrator/GM.
            """,
        )
        self.room = room
        self.world_state: Dict[str, Any] = {
            "universe": None,
            "character": {
                "name": "Traveler",
                "hp": 20,
                "max_hp": 20,
                "stats": {"strength": 10, "agility": 10, "intelligence": 10},
                "inventory": [],
                "status": "Healthy"
            },
            "location": "Unknown",
            "quest": "None",
            "turn_count": 0,
            "history": []
        }
        
        # Load saves if available (to check for existing saves, though we start fresh by default unless requested)
        self._ensure_saves_file()

    def _ensure_saves_file(self):
        if not SAVES_FILE.exists():
            with open(SAVES_FILE, "w") as f:
                json.dump({}, f)

    async def _broadcast_state(self):
        """Broadcast the current world state to the frontend."""
        try:
            payload = json.dumps(self.world_state)
            if self.room and self.room.local_participant:
                await self.room.local_participant.publish_data(payload, topic="world_state")
                logger.info("Broadcasted world state")
        except Exception as e:
            logger.error(f"Failed to broadcast state: {e}")

    @function_tool
    async def initialize_universe(
        self, 
        context: RunContext, 
        universe_type: str,
        character_name: str = "Traveler"
    ) -> str:
        """Initialize the game universe and character.
        
        Args:
            universe_type: The chosen setting (e.g., "Fantasy", "Cyberpunk").
            character_name: The player's character name.
        """
        self.world_state["universe"] = universe_type
        self.world_state["character"]["name"] = character_name
        
        # Set default stats based on universe
        if "fantasy" in universe_type.lower():
            self.world_state["character"]["inventory"] = ["Rusty Sword", "Rations", "Water Skin"]
            self.world_state["character"]["stats"] = {"strength": 12, "agility": 10, "intelligence": 8}
        elif "cyberpunk" in universe_type.lower():
            self.world_state["character"]["inventory"] = ["Datapad", "Credit Chip", "Multi-tool"]
            self.world_state["character"]["stats"] = {"strength": 10, "agility": 12, "intelligence": 10}
        elif "zombie" in universe_type.lower():
            self.world_state["character"]["inventory"] = ["Flashlight", "Baseball Bat", "Bandages"]
            self.world_state["character"]["stats"] = {"strength": 11, "agility": 11, "intelligence": 9}
            
        await self._broadcast_state()
        logger.info(f"Initialized universe: {universe_type}")
        return f"Universe set to {universe_type}. Character {character_name} is ready. Inventory: {', '.join(self.world_state['character']['inventory'])}."

    @function_tool
    async def roll_dice(
        self, 
        context: RunContext, 
        sides: int = 20,
        modifier: int = 0,
        reason: str = "Action check"
    ) -> str:
        """Roll a die to determine the outcome of an action.
        
        Args:
            sides: Number of sides on the die (default 20).
            modifier: Bonus or penalty to add to the roll.
            reason: The reason for the roll (e.g., "Attack goblin", "Climb wall").
        """
        roll = random.randint(1, sides)
        total = roll + modifier
        
        outcome = "Failure"
        if total >= 15:
            outcome = "Great Success"
        elif total >= 10:
            outcome = "Success"
        elif total >= 5:
            outcome = "Partial Success / Complication"
        else:
            outcome = "Critical Failure"
            
        result_text = f"Rolled d{sides}: {roll} + {modifier} = {total}. Outcome: {outcome}"
        logger.info(f"Dice Roll ({reason}): {result_text}")
        return result_text

    @function_tool
    async def check_status(self, context: RunContext) -> str:
        """Check the player's current health and stats."""
        char = self.world_state["character"]
        return f"Name: {char['name']}\nHP: {char['hp']}/{char['max_hp']}\nStatus: {char['status']}\nStats: {char['stats']}"

    @function_tool
    async def check_inventory(self, context: RunContext) -> str:
        """Check what items the player is carrying."""
        items = self.world_state["character"]["inventory"]
        if not items:
            return "Inventory is empty."
        return f"Inventory: {', '.join(items)}"

    @function_tool
    async def update_inventory(
        self, 
        context: RunContext, 
        item_name: str, 
        action: str = "add"
    ) -> str:
        """Add or remove an item from the player's inventory.
        
        Args:
            item_name: The name of the item.
            action: "add" or "remove".
        """
        inventory = self.world_state["character"]["inventory"]
        if action == "add":
            inventory.append(item_name)
            msg = f"Added {item_name} to inventory."
        elif action == "remove":
            if item_name in inventory:
                inventory.remove(item_name)
                msg = f"Removed {item_name} from inventory."
            else:
                return f"{item_name} not found in inventory."
        else:
            return "Invalid action."
            
        await self._broadcast_state()
        return msg

    @function_tool
    async def update_health(
        self, 
        context: RunContext, 
        amount: int, 
        reason: str = "Damage/Healing"
    ) -> str:
        """Update the player's HP.
        
        Args:
            amount: Positive to heal, negative to take damage.
            reason: Cause of the change.
        """
        char = self.world_state["character"]
        old_hp = char["hp"]
        char["hp"] = max(0, min(char["max_hp"], char["hp"] + amount))
        
        if char["hp"] <= 0:
            char["status"] = "Unconscious"
        elif char["hp"] < char["max_hp"] * 0.3:
            char["status"] = "Critical"
        elif char["hp"] < char["max_hp"]:
            char["status"] = "Injured"
        else:
            char["status"] = "Healthy"
            
        await self._broadcast_state()
        logger.info(f"Health update ({reason}): {old_hp} -> {char['hp']}")
        return f"HP changed by {amount}. Current HP: {char['hp']}/{char['max_hp']} ({char['status']})."

    @function_tool
    async def save_game(self, context: RunContext, save_name: str = "autosave") -> str:
        """Save the current game state.
        
        Args:
            save_name: Name for the save file.
        """
        try:
            with open(SAVES_FILE, "r") as f:
                saves = json.load(f)
        except:
            saves = {}
            
        self.world_state["timestamp"] = datetime.now().isoformat()
        saves[save_name] = self.world_state
        
        with open(SAVES_FILE, "w") as f:
            json.dump(saves, f, indent=2)
            
        logger.info(f"Game saved as '{save_name}'")
        return f"Game saved successfully as '{save_name}'."

    @function_tool
    async def load_game(self, context: RunContext, save_name: str = "autosave") -> str:
        """Load a saved game state.
        
        Args:
            save_name: Name of the save to load.
        """
        if not SAVES_FILE.exists():
            return "No save file found."
            
        with open(SAVES_FILE, "r") as f:
            saves = json.load(f)
            
        if save_name not in saves:
            return f"Save '{save_name}' not found. Available saves: {', '.join(saves.keys())}"
            
        self.world_state = saves[save_name]
        await self._broadcast_state()
        logger.info(f"Game loaded from '{save_name}'")
        
        char = self.world_state["character"]
        return f"Game loaded! Welcome back to the {self.world_state['universe']} universe. You are {char['name']} (HP: {char['hp']}). Location: {self.world_state['location']}."

def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()

async def entrypoint(ctx: JobContext):
    # Logging setup
    ctx.log_context_fields = {
        "room": ctx.room.name,
    }

    # Initialize TTS - Using a storytelling voice if possible
    murf_tts = murf.TTS(
        voice="en-US-fin-falcon", # Deep, storytelling voice often good for GMs
        style="Narrative", # Or "Promo" or "Conversation"
        tokenizer=tokenize.basic.SentenceTokenizer(min_sentence_len=2),
        text_pacing=True,
    )

    # Set up voice AI pipeline
    session = AgentSession(
        stt=deepgram.STT(model="nova-3"),
        llm=google.LLM(model="gemini-2.5-flash"),
        tts=murf_tts,
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
    agent = GameMasterAgent(room=ctx.room)
    
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
