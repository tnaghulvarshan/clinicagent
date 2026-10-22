"""
LiveKit Voice Agent for Kaveri Multispeciality Hospital.
Provides real-time conversational voice in Tamil, English, and Tanglish.
Integrates directly with the Google ADK business services and database transactions.
"""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

# Add project root to sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from config.settings import settings
from voice.adk_bridge import ADKVoiceBridge, LIVEKIT_BRIDGED_TOOLS
from voice.telephony import TelephonyManager

from livekit.agents import (
    AutoSubscribe,
    JobContext,
    WorkerOptions,
    cli,
)
from livekit.agents.voice import Agent, AgentSession
from livekit.agents.voice.turn import EndpointingOptions, TurnHandlingOptions
from livekit.plugins.google.realtime import RealtimeModel

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("livekit_voice_agent")

LIVEKIT_VOICE_INSTRUCTIONS = """You are the Real-time Voice Receptionist for Kaveri Multispeciality Hospital, Chennai.
You speak fluent spoken Tamil (தமிழ்), English, and Tanglish (Tamil-English conversational speech).

VOICE RULES (CRITICAL FOR NATURAL SPEECH):
1. SHORT CONVERSATIONAL TURNS:
   - Speak in short, natural spoken sentences (1 to 2 sentences per turn).
   - Avoid long paragraphs, bullet lists, or tables.
   - Wait for the caller to respond before giving more details.

2. BILINGUAL CAPABILITY:
   - If the caller speaks Tamil, respond in natural Tamil ("வணக்கம்! கண்டிப்பா பார்க்கலாம். எந்த doctor-ஐ பார்க்கணும்?").
   - If the caller speaks English, respond in clear professional English.
   - If the caller speaks Tanglish ("Naalaiku doctor appointment book pannanum"), respond in polite, clear Tamil or English.
   - Seamlessly switch languages whenever the caller switches.

3. STRICT HEALTHCARE SAFETY:
   - NEVER diagnose diseases or evaluate symptoms clinically.
   - NEVER prescribe medicines, home remedies, or dosages.
   - If caller mentions chest pain, severe breathlessness, stroke signs, or severe trauma:
     IMMEDIATELY call `get_emergency_contact()` or `escalate_to_human(urgency_level='EMERGENCY')`
     and instruct them to call 108 or our 24x7 Emergency line (+91-44-2499-1066). DO NOT DELAY.

4. REAL DATABASE ACTIONS:
   - Use `list_doctors` to find doctors.
   - Use `get_available_slots` to check genuine database slots. Never fabricate slots.
   - Ask for: Patient Name, Phone Number, Doctor preference, Date.
   - ALWAYS confirm verbally before calling `book_appointment`:
     "டாக்டர் [Name] அவர்களிடம் [Date] [Time] மணிக்கு [Patient] பெயரில் முன்பதிவு செய்யவா?"
   - Read the appointment ID clearly when confirmed.

5. VERIFIED HOSPITAL INFO:
   - Answer location, timings, payments, and prep instructions using `get_hospital_info` and `search_faq`.
   - If information is not in verified records, state that you cannot verify it and provide the human reception number (+91-44-2499-1000). Never guess.
"""


def validate_environment() -> bool:
    """Pre-flight check for required credentials."""
    missing = []
    if not settings.google_api_key:
        missing.append("GEMINI_API_KEY / GOOGLE_API_KEY")
    if not settings.livekit_url or "your-project" in settings.livekit_url:
        missing.append("LIVEKIT_URL")
    if not settings.livekit_api_key or "your_" in settings.livekit_api_key:
        missing.append("LIVEKIT_API_KEY")
    if not settings.livekit_api_secret or "your_" in settings.livekit_api_secret:
        missing.append("LIVEKIT_API_SECRET")

    if missing:
        logger.warning(
            "\n"
            "======================================================================\n"
            "LIVEKIT VOICE AGENT - CONFIGURATION NOTICE:\n"
            "Missing or placeholder credentials in .env:\n"
            "  * %s\n\n"
            "For local testing with microphone, configure LIVEKIT_URL, LIVEKIT_API_KEY,\n"
            "LIVEKIT_API_SECRET, and GOOGLE_API_KEY in your .env file.\n"
            "You can test ADK agents right now without LiveKit using: adk web hospital_agents\n"
            "======================================================================\n",
            "\n  * ".join(missing),
        )
        return False
    return True


async def entrypoint(ctx: JobContext) -> None:
    """LiveKit agent worker entrypoint called when a room session connects."""
    logger.info("Connecting to room: %s", ctx.room.name)
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)

    # Initialize bridge context
    bridge = ADKVoiceBridge(session_id=ctx.room.name)

    # Inspect for telephone / SIP participant
    for participant in ctx.room.remote_participants.values():
        if TelephonyManager.is_sip_call(participant):
            phone = TelephonyManager.extract_caller_phone(participant)
            if phone:
                bridge.set_caller_info(phone=phone)
                logger.info("Incoming telephone caller detected: %s", phone)

    from google.genai import types

    # Configure Gemini Realtime Multimodal Voice Model with zero thinking delay
    model = RealtimeModel(
        model=settings.gemini_realtime_model,
        api_key=settings.google_api_key,
        voice="Aoede",  # Warm, clear voice supporting natural Tamil & English
        temperature=0.3,
        thinking_config=types.ThinkingConfig(thinking_budget=0),  # Eliminate silent thinking latency
    )

    # Initialize LiveKit Voice Agent with ADK bridged tools
    agent = Agent(
        instructions=LIVEKIT_VOICE_INSTRUCTIONS,
        llm=model,
        tools=LIVEKIT_BRIDGED_TOOLS,
        allow_interruptions=True,
    )

    # Start the voice session with responsive endpointing (detects speech end quickly)
    session = AgentSession(
        turn_handling=TurnHandlingOptions(
            endpointing=EndpointingOptions(min_delay=0.4, max_delay=1.5),
        ),
    )
    await session.start(agent, room=ctx.room)

    # Trigger initial warm bilingual spoken greeting from the Gemini Realtime model
    caller_intro = f" (Calling from {bridge.caller_phone})" if bridge.caller_phone else ""
    logger.info("Starting voice conversation for caller%s", caller_intro)

    await session.generate_reply(
        instructions=(
            "Greet the caller warmly in Tamil and English as the AI Receptionist of Kaveri Hospital. "
            "Say: 'வணக்கம்! காவேரி மருத்துவமனைக்கு உங்களை வரவேற்கிறோம். நான் உங்கள் AI உதவியாளர். "
            "Hello! Welcome to Kaveri Hospital. How may I assist you today?'"
        )
    )


def main() -> None:
    """Main CLI runner for LiveKit Voice Agent."""
    logger.info("Initializing Hospital LiveKit Voice Agent...")
    ready = validate_environment()

    # Pass LiveKit credentials to LiveKit CLI environment
    if settings.livekit_url:
        os.environ["LIVEKIT_URL"] = settings.livekit_url
    if settings.livekit_api_key:
        os.environ["LIVEKIT_API_KEY"] = settings.livekit_api_key
    if settings.livekit_api_secret:
        os.environ["LIVEKIT_API_SECRET"] = settings.livekit_api_secret

    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            agent_name="kaveri_hospital_receptionist",
        )
    )


if __name__ == "__main__":
    main()
