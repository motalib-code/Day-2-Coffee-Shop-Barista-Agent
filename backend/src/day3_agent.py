import json
import logging
from datetime import datetime
from pathlib import Path

from wellness_analytics import (
    calculate_goal_completion_rate,
    calculate_mood_trend,
    generate_weekly_insights,
    get_common_stressors,
)
from mcp_tools import (
    create_calendar_reminder,
    create_todoist_tasks,
    is_mcp_available,
    mark_todoist_task_complete,
)

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
from livekit.plugins import deepgram, google, murf, noise_cancellation, silero
from livekit.plugins.turn_detector.multilingual import MultilingualModel

logger = logging.getLogger("agent")

load_dotenv(".env.local")

# Create wellness log file path
WELLNESS_LOG = Path(__file__).parent.parent / "wellness_log.json"


class WellnessCompanion(Agent):
    def __init__(self, room: rtc.Room) -> None:
        # Load history before setting instructions so we can personalize the greeting
        self.history = self._load_history()

        # Generate personalized instructions based on history
        instructions = self._generate_instructions()

        super().__init__(instructions=instructions)
        self.room = room

        # Initialize current session state
        self.current_session = {
            "date": datetime.now().isoformat(),
            "mood": None,
            "energy": None,
            "stressors": [],
            "goals": [],
            "summary": None,
        }

    def _load_history(self) -> list:
        """Load past check-ins from JSON file."""
        if not WELLNESS_LOG.exists():
            return []

        try:
            with open(WELLNESS_LOG) as f:
                return json.load(f)
        except json.JSONDecodeError:
            logger.warning("Could not parse wellness log, starting fresh")
            return []
        except Exception as e:
            logger.error(f"Error loading history: {e}")
            return []

    def _generate_instructions(self) -> str:
        """Generate personalized instructions based on history."""
        base_instructions = """You are a supportive health and wellness companion. The user is interacting with you via voice.

Your role is to conduct a brief, grounded daily check-in. You are NOT a clinician and should avoid giving medical advice or making diagnoses.

Your conversation flow:
1. **Greeting**: Warmly greet the user. If there's past history, briefly reference it (e.g., "Last time we talked, you mentioned feeling low on energy. How does today compare?")

2. **Mood & Energy Check**: Ask about their current mood and energy level. Keep it conversational:
   - "How are you feeling today?"
   - "What's your energy like?"
   - "Anything stressing you out right now?"

3. **Daily Goals**: Ask what they'd like to accomplish today:
   - "What are 1-3 things you'd like to get done today?"
   - "Is there anything you want to do for yourself - rest, exercise, hobbies?"

4. **Simple Advice**: Offer grounded, realistic suggestions:
   - Break large goals into smaller steps
   - Encourage short breaks
   - Suggest simple grounding activities (5-minute walk, deep breathing)
   - Keep it practical and actionable

5. **Recap**: Summarize the session:
   - Repeat back today's mood summary
   - List the main 1-3 objectives
   - Ask: "Does this sound right?"
   - Once confirmed, use the save_log tool to persist this session

**Weekly Reflections**: If the user asks about trends or patterns (e.g., "How has my mood been?", "Am I following through on my goals?"), use the analytics tools:
   - Use get_mood_trend for mood analysis
   - Use get_goal_summary for goal tracking patterns
   - Use get_weekly_summary for comprehensive insights
   - Keep insights supportive and non-judgmental

Keep your responses:
- **Concise**: You're having a voice conversation
- **Warm and supportive**: But realistic, not overly cheerful
- **Grounded**: Practical advice, not medical claims
- **Natural**: Like a real wellness coach would speak

Don't use complex formatting, emojis, or asterisks."""

        # Add context from last session if available
        if self.history:
            last_session = self.history[-1]
            context_note = f"\n\nContext from last check-in ({last_session.get('date', 'recent')}):\n"
            if last_session.get("mood"):
                context_note += f"- Mood: {last_session.get('mood')}\n"
            if last_session.get("energy"):
                context_note += f"- Energy: {last_session.get('energy')}\n"
            if last_session.get("goals"):
                context_note += f"- Goals: {', '.join(last_session.get('goals', []))}\n"

            base_instructions += context_note

        return base_instructions

    @function_tool
    async def save_log(
        self,
        context: RunContext,
        mood: str,
        energy: str,
        goals: list[str],
        stressors: str = "",
        summary: str = "",
    ):
        """Save the current check-in session to the wellness log.

        Use this tool after you've completed the check-in and the user has confirmed
        that your recap is correct.

        Args:
            mood: User's self-reported mood (e.g., "good", "tired", "stressed")
            energy: User's energy level (e.g., "high", "medium", "low", "energetic")
            goals: List of 1-3 goals or intentions for the day
            stressors: Optional description of what's stressing them out
            summary: A brief agent-generated summary of the session
        """
        # Update current session
        self.current_session.update(
            {
                "date": datetime.now().isoformat(),
                "mood": mood,
                "energy": energy,
                "stressors": stressors.split(",") if stressors else [],
                "goals": goals,
                "summary": summary,
            }
        )

        # Append to history
        self.history.append(self.current_session)

        # Save to file
        try:
            with open(WELLNESS_LOG, "w") as f:
                json.dump(self.history, f, indent=2)
            logger.info(f"Saved wellness log: {len(self.history)} total sessions")
            return "Session saved! Take care, and I'll check in with you next time."
        except Exception as e:
            logger.error(f"Failed to save wellness log: {e}")
            return "I had trouble saving the log, but I'll remember our conversation for now."

    @function_tool
    async def get_mood_trend(self, context: RunContext, days: int = 7):
        """Analyze the user's mood trends over recent days.
        
        Use this when the user asks about their mood patterns, like:
        - "How has my mood been this week?"
        - "Am I feeling better than last week?"
        - "What's my mood trend?"
        
        Args:
            days: Number of days to analyze (default: 7 for one week)
        
        Returns:
            A natural language summary of mood trends
        """
        analysis = calculate_mood_trend(self.history, days=days)
        
        if analysis["recent_sessions"] == 0:
            return "I don't have enough recent check-ins to analyze your mood trend. Let's do a check-in now to start building that history!"
        
        # Build a conversational response
        response = analysis["trend_summary"]
        
        # Add energy context if available
        if analysis.get("energies"):
            high_energy_count = sum(1 for e in analysis["energies"] if e in ["high", "energetic", "good"])
            low_energy_count = sum(1 for e in analysis["energies"] if e in ["low", "tired", "exhausted"])
            
            if high_energy_count > len(analysis["energies"]) // 2:
                response += " Your energy levels have been pretty good too."
            elif low_energy_count > len(analysis["energies"]) // 2:
                response += " Your energy has been on the lower side - make sure you're getting enough rest."
        
        return response

    @function_tool
    async def get_goal_summary(self, context: RunContext, days: int = 7):
        """Summarize the user's goal-setting patterns and follow-through.
        
        Use this when the user asks about their goals, like:
        - "Am I following through on my goals?"
        - "How many goals have I been setting?"
        - "Am I being consistent with my intentions?"
        
        Args:
            days: Number of days to analyze (default: 7 for one week)
        
        Returns:
            A natural language summary of goal patterns
        """
        analysis = calculate_goal_completion_rate(self.history, days=days)
        
        if analysis["total_goals_set"] == 0:
            return "You haven't set specific goals in recent check-ins. Would you like to set some today?"
        
        return analysis["summary"]

    @function_tool
    async def get_weekly_summary(self, context: RunContext):
        """Generate a comprehensive weekly wellness summary.
        
        Use this when the user asks for an overall weekly review, like:
        - "How has my week been?"
        - "Can you give me a weekly summary?"
        - "What are my patterns this week?"
        
        Returns:
            A comprehensive natural language summary of the week
        """
        summary = generate_weekly_insights(self.history)
        return summary

    @function_tool
    async def create_tasks(
        self, context: RunContext, goals: list[str], confirmed: bool = False
    ):
        """Create tasks in Todoist from the user's goals.
        
        IMPORTANT: Only call this if the user explicitly requests task creation AND confirms.
        First ask: "Would you like me to turn these into Todoist tasks?"
        Only proceed if they say yes.
        
        Args:
            goals: List of goals to convert into tasks
            confirmed: Must be True (user must confirm before calling)
        
        Returns:
            Status message about task creation
        """
        if not is_mcp_available():
            return "Task creation isn't set up yet. To enable it, you'll need to set up Todoist integration with an API token."
        
        if not confirmed:
            return "I need your confirmation before creating tasks. Please confirm you want to create these tasks."
        
        result = await create_todoist_tasks(goals)
        
        if result["success"]:
            return f"Great! I've created {result['task_count']} tasks in Todoist for you: {', '.join(goals)}"
        else:
            return f"I had trouble creating tasks: {result['message']}"

    @function_tool
    async def set_reminder(
        self,
        context: RunContext,
        activity: str,
        time: str,
        confirmed: bool = False,
    ):
        """Create a reminder for a self-care activity or goal.
        
        IMPORTANT: Only call this if the user explicitly mentions wanting a reminder AND confirms.
        First ask: "Would you like me to set a reminder for that?"
        Only proceed if they say yes.
        
        Args:
            activity: What to be reminded about (e.g., "take a walk", "call mom")
            time: When to set the reminder (e.g., "6 PM", "3:00 PM", "in 2 hours")
            confirmed: Must be True (user must confirm before calling)
        
        Returns:
            Status message about reminder creation
        """
        if not is_mcp_available():
            return f"Reminder features aren't enabled yet, but I'll note that you wanted to {activity} at {time}. You'll need to set that manually for now."
        
        if not confirmed:
            return f"Just to confirm - you want me to set a reminder to {activity} at {time}?"
        
        result = await create_calendar_reminder(activity, time)
        
        if result["success"]:
            return f"Perfect! I've set a reminder for you to {activity} at {time}."
        else:
            return result["message"]



def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()


async def entrypoint(ctx: JobContext):
    # Logging setup
    ctx.log_context_fields = {
        "room": ctx.room.name,
    }

    # Set up voice AI pipeline
    session = AgentSession(
        # Speech-to-text (STT)
        stt=deepgram.STT(model="nova-3"),
        # Large Language Model (LLM)
        llm=google.LLM(model="gemini-2.5-flash"),
        # Text-to-speech (TTS)
        tts=murf.TTS(
            voice="en-US-matthew",
            style="Conversation",
            tokenizer=tokenize.basic.SentenceTokenizer(min_sentence_len=2),
            text_pacing=True,
        ),
        # VAD and turn detection
        turn_detection=MultilingualModel(),
        vad=ctx.proc.userdata["vad"],
        # Allow LLM to generate while waiting for end of turn
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
        agent=WellnessCompanion(room=ctx.room),
        room=ctx.room,
        room_input_options=RoomInputOptions(
            noise_cancellation=noise_cancellation.BVC(),
        ),
    )

    # Join the room and connect to the user
    await ctx.connect()


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint, prewarm_fnc=prewarm))
