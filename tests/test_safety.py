"""
Healthcare safety, triage guardrails, and emergency escalation tests.
"""

from __future__ import annotations

import pytest
from services.handoff_service import HandoffService
from config.settings import Settings, settings


def test_emergency_triage_escalation(handoff_service: HandoffService):
    """Emergency symptoms must trigger emergency escalation to hotline and ambulance."""
    handoff = handoff_service.record_handoff(
        session_id="EMERG-TEST-001",
        reason="Severe chest pain radiating to left arm",
        stated_concern="I feel severe tightness in chest and difficulty breathing",
        urgency_level="EMERGENCY",
        patient_phone="+919840199999",
        patient_name="Anand Kumar",
    )

    assert handoff["success"] is True
    assert handoff["urgency_level"] == "EMERGENCY"
    assert "108" in handoff["message_en"]
    assert "2499-1066" in handoff["destination"]
    assert "அவசர மருத்துவ உதவி" in handoff["message_ta"]


def test_routine_handoff_recording(handoff_service: HandoffService):
    """Routine patient concerns are recorded with reference and receptionist number."""
    handoff = handoff_service.record_handoff(
        session_id="ROUTINE-TEST-002",
        reason="Patient requested human discussion",
        stated_concern="Want to know if wheelchair ramp is near Gate 2",
        urgency_level="ROUTINE",
        patient_phone="+919840188888",
    )

    assert handoff["success"] is True
    assert handoff["urgency_level"] == "ROUTINE"
    assert handoff["destination"] == settings.receptionist_phone
    assert handoff["status"] == "RECORDED"


def test_settings_validation_errors():
    """Missing required credentials raise helpful informative errors."""
    s = Settings()
    s.google_api_key = ""  # simulate missing key

    with pytest.raises(ValueError) as exc:
        s.validate_gemini()
    assert "GEMINI_API_KEY" in str(exc.value)

    s.livekit_url = ""
    with pytest.raises(ValueError) as exc2:
        s.validate_livekit()
    assert "LIVEKIT_URL" in str(exc2.value)


def test_no_api_key_leak_in_repr():
    """Settings string representation never prints actual API keys."""
    s = Settings()
    s.google_api_key = "AIzaSySuperSecretKey12345"
    s.livekit_api_secret = "VerySecretLiveKitSecret999"

    repr_str = repr(s)
    assert "AIzaSy" not in repr_str
    assert "SuperSecret" not in repr_str
    assert "VerySecret" not in repr_str
    assert "has_gemini_key=True" in repr_str
