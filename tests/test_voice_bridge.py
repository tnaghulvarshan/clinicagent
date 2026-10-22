"""
Tests for LiveKit voice bridge, language support, and telephony integration.
"""

from __future__ import annotations

import pytest
from voice.language_support import (
    detect_language,
    format_date_for_speech,
    format_time_for_speech,
    format_appointment_id_for_speech,
)
from voice.adk_bridge import LIVEKIT_BRIDGED_TOOLS, ADKVoiceBridge
from voice.telephony import TelephonyManager


def test_language_detection():
    """Detects Tamil script, Tanglish, and English accurately."""
    # Tamil script
    assert detect_language("வணக்கம், நாளைக்கு டாக்டர் appointment கிடைக்குமா?") == "ta"
    assert detect_language("பொது மருத்துவர் அறை எண் என்ன?") == "ta"

    # Tanglish
    assert detect_language("Naalaiku doctor appointment book pannanum") == "tanglish"
    assert detect_language("Vanakkam, doctor eppo varuvaaru?") == "tanglish"

    # English
    assert detect_language("I want to book an appointment for tomorrow.") == "en"
    assert detect_language("What are the OPD consultation hours?") == "en"


def test_date_formatting_for_speech():
    """Date is formatted naturally for spoken voice in Tamil and English."""
    # English
    en_spoken = format_date_for_speech("2026-10-23", "en")
    assert "October 23rd, 2026" in en_spoken

    # Tamil
    ta_spoken = format_date_for_speech("2026-10-23", "ta")
    assert "அக்டோபர்" in ta_spoken
    assert "இருபத்து மூன்று" in ta_spoken


def test_time_formatting_for_speech():
    """Time is formatted naturally for spoken voice in Tamil and English."""
    # Morning
    assert "9:30 AM" in format_time_for_speech("09:30", "en")
    assert "காலை" in format_time_for_speech("09:30", "ta")

    # Afternoon / Evening
    assert "4:30 PM" in format_time_for_speech("16:30", "en")
    assert "மாலை" in format_time_for_speech("16:30", "ta")


def test_appointment_id_phonetic_speech():
    """Appointment ID is spaced out phonetically for TTS clarity."""
    phonetic = format_appointment_id_for_speech("APT-20261023-A1B2")
    assert "A P T" in phonetic
    assert "A 1 B 2" in phonetic


def test_livekit_bridged_tools_count_and_names():
    """LiveKit bridged tools list contains all 10 verified tools."""
    tool_names = [t.info.name for t in LIVEKIT_BRIDGED_TOOLS]
    expected_tools = [
        "list_doctors",
        "get_available_slots",
        "book_appointment",
        "get_appointment",
        "reschedule_appointment",
        "cancel_appointment",
        "get_hospital_info",
        "search_faq",
        "escalate_to_human",
        "get_emergency_contact",
    ]
    for expected in expected_tools:
        assert expected in tool_names


def test_telephony_setup_guide():
    """Telephony guide returns structured milestone 3 instructions."""
    guide = TelephonyManager.get_telephony_setup_guide()
    assert guide["milestone"] == "Real Phone Calls via LiveKit SIP"
    assert len(guide["setup_steps"]) >= 4


@pytest.mark.asyncio
async def test_livekit_bridged_tools_are_awaitable():
    """LiveKit tools must be coroutines to prevent 'TypeError: object dict can't be used in await expression'."""
    from voice.adk_bridge import (
        voice_list_doctors,
        voice_get_hospital_info,
        voice_search_faq,
        voice_get_emergency_contact,
        voice_get_available_slots,
    )

    # 1. list_doctors
    docs_result = await voice_list_doctors(department="Cardiology")
    assert isinstance(docs_result, dict)
    assert docs_result["success"] is True
    assert len(docs_result["doctors"]) > 0

    # 2. get_hospital_info
    info_result = await voice_get_hospital_info(topic="visiting hours")
    assert isinstance(info_result, dict)
    assert info_result["success"] is True
    assert "visiting" in info_result.get("answer_en", "").lower() or info_result["topic"] == "timings"

    # 3. search_faq
    faq_result = await voice_search_faq(query="emergency")
    assert isinstance(faq_result, dict)

    # 4. get_emergency_contact
    emg_result = await voice_get_emergency_contact()
    assert isinstance(emg_result, dict)
    assert "108" in emg_result["ambulance"]

    # 5. get_available_slots
    slots_result = await voice_get_available_slots(doctor_id=1, date="2026-10-23")
    assert isinstance(slots_result, dict)

