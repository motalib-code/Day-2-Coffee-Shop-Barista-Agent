import logging
import json
from datetime import datetime
from pathlib import Path
from typing import Annotated

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

import tutor_utils

logger = logging.getLogger("day4_agent")

load_dotenv(".env.local")

class TutorAgent(Agent):
    def __init__(self, room: rtc.Room, tts: murf.TTS) -> None:
        super().__init__(
            instructions="""You are an Active Recall Coach, a helpful tutor designed to help users learn concepts effectively.
            
            You have three modes of operation:
            1. **Learn Mode**: You explain concepts clearly and concisely.
            2. **Quiz Mode**: You ask questions to test the user's knowledge.
            3. **Teach-Back Mode**: You ask the user to explain a concept back to you, then provide feedback.
            
            Your current mode is: LEARN.
            
            Always stay in character for the current mode.
            - In LEARN mode: Be informative, patient, and clear. Use analogies.
            - In QUIZ mode: Be encouraging but challenging. Ask one question at a time.
            - In TEACH-BACK mode: Be a curious listener. Ask the user to explain, then give constructive feedback.
            
            When the user wants to switch modes, use the `switch_mode` tool.
            When the user wants to learn about a specific topic, use `select_concept` or just explain it if you know it.
            
            Start by greeting the user, listing the available topics, and asking which mode they'd like to start in.
            """,
        )
        self.room = room
        self.tts = tts
        self.current_mode = "learn"
        self.current_concept = None
        
        # Voice mapping
        self.voices = {
            "learn": "en-US-matthew-falcon",
            "quiz": "en-US-alicia-falcon",
            "teach_back": "en-US-ken-falcon"
        }

    @function_tool
    async def switch_mode(self, context: RunContext, mode: str):
        """Switch the agent's operating mode.
        
        Args:
            mode: The mode to switch to. Must be one of: 'learn', 'quiz', 'teach_back'.
        """
        mode = mode.lower()
        if mode not in self.voices:
            return "Invalid mode. Please choose learn, quiz, or teach_back."
        
        self.current_mode = mode
        
        # Update voice
        # Note: We are modifying the voice attribute of the TTS instance.
        # This assumes the TTS plugin checks this attribute on each synthesis.
        if hasattr(self.tts, "voice"):
            self.tts.voice = self.voices[mode]
            logger.info(f"Switched voice to {self.voices[mode]} for mode {mode}")
        else:
            logger.warning("Could not update TTS voice: 'voice' attribute not found")

        # Update instructions context
        self.instructions = f"""You are an Active Recall Coach in {mode.upper()} mode.
        
        Current Concept: {self.current_concept.get('title') if self.current_concept else 'None selected'}
        
        Behavior for {mode.upper()} mode:
        """
        
        if mode == "learn":
            self.instructions += """
            - Explain the current concept clearly.
            - Use the summary and key points from the content.
            - Ask if the user understands or wants to move to quiz/teach-back.
            """
        elif mode == "quiz":
            self.instructions += """
            - Ask the sample question for the current concept.
            - Wait for the user's answer.
            - Evaluate if they are correct based on the concept summary.
            """
        elif mode == "teach_back":
            self.instructions += """
            - Ask the user to explain the current concept to you.
            - Listen carefully.
            - Give feedback on what they missed or explained well.
            """
            
        return f"Switched to {mode} mode. I am now ready."

    @function_tool
    async def select_concept(self, context: RunContext, topic: str):
        """Select a concept to focus on.
        
        Args:
            topic: The name or keyword of the concept to select.
        """
        concept = tutor_utils.find_concept_by_keyword(topic)
        if not concept:
            return f"I couldn't find a concept matching '{topic}'. Available topics are: {tutor_utils.get_concept_list_text()}"
        
        self.current_concept = concept
        logger.info(f"Selected concept: {concept['title']}")
        
        # Trigger appropriate response based on mode
        if self.current_mode == "learn":
            explanation = tutor_utils.format_concept_for_learning(concept)
            return f"Selected {concept['title']}. {explanation}"
        elif self.current_mode == "quiz":
            question = tutor_utils.format_concept_for_quiz(concept)
            return f"Selected {concept['title']}. {question}"
        elif self.current_mode == "teach_back":
            prompt = tutor_utils.format_concept_for_teachback(concept)
            return f"Selected {concept['title']}. {prompt}"
            
        return f"Selected {concept['title']}."

    @function_tool
    async def list_concepts(self, context: RunContext):
        """List all available learning concepts."""
        return tutor_utils.get_concept_list_text()

    @function_tool
    async def evaluate_teach_back(self, context: RunContext, user_explanation: str):
        """Evaluate the user's explanation in teach-back mode.
        
        Args:
            user_explanation: The explanation provided by the user.
        """
        if not self.current_concept:
            return "No concept selected. Please select a concept first."
            
        # This tool is mainly for the LLM to explicitly mark that it's evaluating.
        # The actual evaluation logic is done by the LLM generating the response.
        # We just return the reference material to help the LLM.
        
        return f"""
        User explanation: {user_explanation}
        
        Reference Concept:
        Title: {self.current_concept['title']}
        Summary: {self.current_concept['summary']}
        Key Points: {', '.join(self.current_concept.get('key_points', []))}
        
        Please provide qualitative feedback. Did they cover the key points? Was it accurate?
        """

def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()

async def entrypoint(ctx: JobContext):
    # Logging setup
    ctx.log_context_fields = {
        "room": ctx.room.name,
    }

    # Initialize TTS with default voice (Learn mode)
    # We keep a reference to it to change voices later
    murf_tts = murf.TTS(
        voice="en-US-matthew-falcon",
        style="Conversation",
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
    # Pass the TTS instance to the agent so it can modify it
    agent = TutorAgent(room=ctx.room, tts=murf_tts)
    
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
