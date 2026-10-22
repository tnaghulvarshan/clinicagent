"""
Human handoff and emergency escalation tools for Google ADK agents.
"""

from __future__ import annotations

import secrets
from typing import Any, Dict
from services.handoff_service import HandoffService

_service = HandoffService()


def escalate_to_human(
    reason: str,
    stated_concern: str,
    urgency_level: str = "ROUTINE",
    patient_phone: str = "",
    patient_name: str = "",
    session_id: str = "",
) -> Dict[str, Any]:
    """
    Escalate a patient conversation to a human receptionist or emergency care coordinator.
    Always use this when the patient requests human assistance, has complex unverified questions,
    or presents an urgent or emergency situation.

    Args:
        reason: Summary reason for handoff (e.g. 'Patient requested human', 'Unverified clinical question', 'Emergency symptoms').
        stated_concern: Patient's verbatim or summarized concern.
        urgency_level: 'ROUTINE', 'URGENT', or 'EMERGENCY'.
        patient_phone: Optional phone number of the patient.
        patient_name: Optional name of the patient.
        session_id: Optional conversation session identifier.

    Returns:
        Dict containing handoff reference ID, destination phone number, and instructions.
    """
    sid = session_id.strip() or f"SES-{secrets.token_hex(3).upper()}"
    return _service.record_handoff(
        session_id=sid,
        reason=reason,
        stated_concern=stated_concern,
        urgency_level=urgency_level,
        patient_phone=patient_phone if patient_phone else None,
        patient_name=patient_name if patient_name else None,
    )


def get_emergency_contact() -> Dict[str, Any]:
    """
    Immediately retrieve 24x7 emergency contacts, ambulance numbers, and trauma center location.
    Use immediately when patient mentions life-threatening symptoms (chest pain, severe breathlessness, stroke, severe bleeding).

    Returns:
        Dict with 24x7 emergency phone numbers, ambulance line (108), and immediate guidance.
    """
    return _service.get_emergency_contacts()
