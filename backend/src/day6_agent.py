import logging
import json
from datetime import datetime
from pathlib import Path
from typing import Optional

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

logger = logging.getLogger("day6_agent")

load_dotenv(".env.local")

# Paths
FRAUD_CASES_FILE = Path(__file__).parent.parent / "fraud_cases.json"


class FraudAlertAgent(Agent):
    def __init__(self, room: rtc.Room) -> None:
        super().__init__(
            instructions="""You are a fraud detection representative for SecureBank, a trusted financial institution.
            
            **Your Role:**
            You are calling customers to verify suspicious transactions detected on their accounts.
            
            **Your Tone:**
            - Professional, calm, and reassuring
            - Clear and concise
            - Patient and understanding
            - Never alarming or creating panic
            
            **Call Flow:**
            1. **Introduction**: Clearly introduce yourself and SecureBank's fraud department.
            2. **Explanation**: Explain you are calling about a suspicious transaction.
            3. **Verification**: Ask the customer for their security identifier to verify their identity.
            4. **Transaction Details**: Read out the suspicious transaction details (merchant, amount, masked card, time, location).
            5. **Confirmation**: Ask if they made this transaction.
            6. **Resolution**: Based on their answer:
               - If YES → Mark as safe and reassure them.
               - If NO → Mark as fraudulent, explain that their card will be blocked and a dispute will be raised.
            7. **Closing**: Thank them and end the call.
            
            **Important Security Rules:**
            - NEVER ask for full card numbers
            - NEVER ask for PINs or passwords
            - NEVER ask for CVV codes
            - Only use the security identifier for verification
            
            **Current State:**
            - Customer verification: NOT VERIFIED
            - Fraud case: NOT LOADED
            
            Start by introducing yourself and explaining why you are calling.
            """,
        )
        self.room = room
        self.fraud_case = None
        self.is_verified = False
        self.call_completed = False

    def _load_all_cases(self):
        """Load all fraud cases from the database."""
        try:
            if not FRAUD_CASES_FILE.exists():
                logger.error(f"Fraud cases file not found: {FRAUD_CASES_FILE}")
                return []
            
            with open(FRAUD_CASES_FILE, "r") as f:
                cases = json.load(f)
            
            logger.info(f"Loaded {len(cases)} fraud cases from database")
            return cases
        except Exception as e:
            logger.error(f"Error loading fraud cases: {e}")
            return []

    def _save_all_cases(self, cases):
        """Save all fraud cases back to the database."""
        try:
            with open(FRAUD_CASES_FILE, "w") as f:
                json.dump(cases, f, indent=2)
            logger.info(f"Saved {len(cases)} fraud cases to database")
        except Exception as e:
            logger.error(f"Error saving fraud cases: {e}")

    @function_tool
    async def load_fraud_case(
        self, 
        context: RunContext, 
        username: str
    ):
        """Load a fraud case from the database for a specific customer.
        
        Args:
            username: The customer's name to look up their fraud case.
        """
        all_cases = self._load_all_cases()
        
        # Find matching case (case-insensitive)
        matching_case = None
        for case in all_cases:
            if case.get("userName", "").lower() == username.lower():
                matching_case = case
                break
        
        if not matching_case:
            return f"I couldn't find a fraud case for '{username}'. Please verify the name."
        
        if matching_case.get("status") != "pending_review":
            return f"This fraud case has already been processed. Status: {matching_case.get('status')}"
        
        self.fraud_case = matching_case
        logger.info(f"Loaded fraud case for {username}: Case ID {self.fraud_case.get('id')}")
        
        return f"Fraud case loaded for {self.fraud_case['userName']}. Transaction of ${self.fraud_case['transactionAmount']} at {self.fraud_case['transactionName']}."

    @function_tool
    async def verify_customer(
        self, 
        context: RunContext, 
        security_identifier: str
    ):
        """Verify the customer's identity using their security identifier.
        
        Args:
            security_identifier: The security identifier provided by the customer.
        """
        if not self.fraud_case:
            return "Please load a fraud case first before verifying the customer."
        
        if self.is_verified:
            return "Customer has already been verified."
        
        # Check if the security identifier matches
        if security_identifier == self.fraud_case.get("securityIdentifier"):
            self.is_verified = True
            logger.info(f"Customer {self.fraud_case['userName']} verified successfully")
            return "Identity verified successfully. I can now proceed with the fraud investigation."
        else:
            logger.warning(f"Verification failed for {self.fraud_case['userName']}")
            return "I'm sorry, but the security identifier you provided doesn't match our records. For security reasons, I cannot proceed with this call. Please contact our customer service directly."

    @function_tool
    async def get_transaction_details(self, context: RunContext):
        """Get the details of the suspicious transaction.
        
        This tool retrieves the transaction information to read out to the customer.
        """
        if not self.fraud_case:
            return "No fraud case loaded. Please load a case first."
        
        if not self.is_verified:
            return "Customer must be verified before sharing transaction details."
        
        case = self.fraud_case
        details = f"""
        Here are the details of the suspicious transaction:
        
        - Amount: ${case['transactionAmount']} {case['transactionCurrency']}
        - Merchant: {case['transactionName']}
        - Card ending in: {case['cardEnding']}
        - Category: {case['transactionCategory']}
        - Location: {case['transactionLocation']}
        - Transaction source: {case['transactionSource']}
        - Time: {case['transactionTime']}
        """
        
        return details.strip()

    @function_tool
    async def mark_transaction_safe(self, context: RunContext):
        """Mark the transaction as safe (customer confirmed they made it).
        
        Call this when the customer confirms they made the transaction.
        """
        if not self.fraud_case:
            return "No fraud case loaded."
        
        if not self.is_verified:
            return "Customer must be verified first."
        
        # Update the case in memory
        self.fraud_case["status"] = "confirmed_safe"
        self.fraud_case["outcomeNote"] = f"Customer confirmed transaction as legitimate on {datetime.now().isoformat()}"
        
        # Save to database
        all_cases = self._load_all_cases()
        for i, case in enumerate(all_cases):
            if case.get("id") == self.fraud_case.get("id"):
                all_cases[i] = self.fraud_case
                break
        
        self._save_all_cases(all_cases)
        self.call_completed = True
        
        logger.info(f"Transaction marked as SAFE for case ID {self.fraud_case['id']}")
        
        return f"""
        Thank you for confirming. I've marked this transaction as legitimate in our system.
        Your card ending in {self.fraud_case['cardEnding']} is secure and no action is needed.
        Thank you for your time, and have a great day!
        """

    @function_tool
    async def mark_transaction_fraudulent(self, context: RunContext):
        """Mark the transaction as fraudulent (customer did not make it).
        
        Call this when the customer denies making the transaction.
        """
        if not self.fraud_case:
            return "No fraud case loaded."
        
        if not self.is_verified:
            return "Customer must be verified first."
        
        # Update the case in memory
        self.fraud_case["status"] = "confirmed_fraud"
        self.fraud_case["outcomeNote"] = f"Customer denied transaction. Card blocked and dispute initiated on {datetime.now().isoformat()}"
        
        # Save to database
        all_cases = self._load_all_cases()
        for i, case in enumerate(all_cases):
            if case.get("id") == self.fraud_case.get("id"):
                all_cases[i] = self.fraud_case
                break
        
        self._save_all_cases(all_cases)
        self.call_completed = True
        
        logger.info(f"Transaction marked as FRAUDULENT for case ID {self.fraud_case['id']}")
        
        return f"""
        I understand. For your protection, I have immediately:
        1. Blocked your card ending in {self.fraud_case['cardEnding']}
        2. Raised a dispute for the ${self.fraud_case['transactionAmount']} transaction
        3. Flagged this as fraudulent activity
        
        You will receive a new card within 5-7 business days. You will not be charged for this fraudulent transaction.
        Is there anything else I can help you with today?
        """

    @function_tool
    async def end_call(self, context: RunContext):
        """End the fraud alert call.
        
        Use this when the conversation is complete.
        """
        if not self.call_completed and self.fraud_case:
            # Mark as verification failed if we didn't complete
            self.fraud_case["status"] = "verification_failed"
            self.fraud_case["outcomeNote"] = f"Call ended without resolution on {datetime.now().isoformat()}"
            
            all_cases = self._load_all_cases()
            for i, case in enumerate(all_cases):
                if case.get("id") == self.fraud_case.get("id"):
                    all_cases[i] = self.fraud_case
                    break
            
            self._save_all_cases(all_cases)
            logger.info(f"Call ended without resolution for case ID {self.fraud_case['id']}")
        
        return "Thank you for your time. Goodbye!"


def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()


async def entrypoint(ctx: JobContext):
    # Logging setup
    ctx.log_context_fields = {
        "room": ctx.room.name,
    }

    # Initialize TTS
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
    agent = FraudAlertAgent(room=ctx.room)
    
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
