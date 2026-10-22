"""
LiveKit-to-ADK Integration Bridge.
Exposes validated Google ADK tools to LiveKit Voice Agents.
Guarantees that all appointment booking, slot checks, and emergency handoffs
go through the validated ADK backend services and database transactions.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from livekit.agents import llm

from services.appointment_service import AppointmentService
from services.faq_service import FAQService
from services.handoff_service import HandoffService
from voice.language_support import (
    format_date_for_speech,
    format_time_for_speech,
    format_appointment_id_for_speech,
)

logger = logging.getLogger(__name__)

# Shared validated services
_apt_service = AppointmentService()
_faq_service = FAQService()
_handoff_service = HandoffService()


class ADKVoiceBridge:
    """
    Manages caller context, identity, and tool delegation between
    the real-time LiveKit audio session and the Google ADK business services.
    """

    def __init__(self, session_id: str, caller_phone: Optional[str] = None) -> None:
        self.session_id = session_id
        self.caller_phone = caller_phone
        self.patient_name: Optional[str] = None
        self.selected_doctor_id: Optional[int] = None
        self.selected_date: Optional[str] = None
        self.selected_time: Optional[str] = None
        self.detected_language: str = "en"

    def set_caller_info(self, name: Optional[str] = None, phone: Optional[str] = None) -> None:
        if name:
            self.patient_name = name.strip()
        if phone:
            self.caller_phone = phone.strip()


# ==============================================================================
# LiveKit Function Tools bridged directly to ADK Services
# ==============================================================================

@llm.function_tool(
    name="list_doctors",
    description="List doctors available at the hospital, optionally filtered by medical department or specialty (General Medicine, Cardiology, Pediatrics, Orthopedics, ENT, Gynecology).",
)
def voice_list_doctors(department: str = "") -> Dict[str, Any]:
    """List doctors by department from the verified hospital database."""
    logger.info("Voice tool called: list_doctors(department='%s')", department)
    doctors = _apt_service.list_doctors(department=department)
    return {
        "success": True,
        "count": len(doctors),
        "department": department,
        "doctors": doctors,
    }


@llm.function_tool(
    name="get_available_slots",
    description="Check real database availability for a doctor on a specific date (YYYY-MM-DD). Never fabricates slots.",
)
def voice_get_available_slots(doctor_id: int, date: str) -> Dict[str, Any]:
    """Check actual available appointment slots in the hospital database."""
    logger.info("Voice tool called: get_available_slots(doctor_id=%d, date='%s')", doctor_id, date)
    result = _apt_service.get_available_slots(doctor_id=doctor_id, date_str=date)

    if result.get("success") and result.get("slots"):
        # Enrich slot times with spoken representations for natural TTS playback
        for slot in result["slots"]:
            slot["spoken_time_ta"] = format_time_for_speech(slot["start_time"], "ta")
            slot["spoken_time_en"] = format_time_for_speech(slot["start_time"], "en")

    return result


@llm.function_tool(
    name="book_appointment",
    description="Atomically book an appointment in the hospital database after patient confirmation. Prevents double-booking.",
)
def voice_book_appointment(
    patient_name: str,
    patient_phone: str,
    doctor_id: int,
    date: str,
    start_time: str,
    reason: str = "",
    preferred_language: str = "Tamil",
) -> Dict[str, Any]:
    """Atomically books the appointment in the database."""
    logger.info(
        "Voice tool called: book_appointment(name='%s', phone='%s', doctor_id=%d, date='%s', time='%s')",
        patient_name,
        patient_phone,
        doctor_id,
        date,
        start_time,
    )
    result = _apt_service.book_appointment(
        patient_name=patient_name,
        patient_phone=patient_phone,
        doctor_id=doctor_id,
        date_str=date,
        start_time=start_time,
        reason=reason,
        preferred_language=preferred_language,
    )

    if result.get("success"):
        # Add phonetic appointment ID for clear speech synthesis
        result["spoken_appointment_id"] = format_appointment_id_for_speech(
            result["appointment_id"]
        )

    return result


@llm.function_tool(
    name="get_appointment",
    description="Look up an existing appointment by appointment ID and verify patient phone number.",
)
def voice_get_appointment(appointment_id: str, patient_phone: str = "") -> Dict[str, Any]:
    """Look up an existing appointment with patient privacy verification."""
    logger.info("Voice tool called: get_appointment(id='%s')", appointment_id)
    return _apt_service.get_appointment(
        appointment_id=appointment_id,
        patient_phone=patient_phone if patient_phone else None,
    )


@llm.function_tool(
    name="reschedule_appointment",
    description="Reschedule an existing appointment to a new date and time slot atomically.",
)
def voice_reschedule_appointment(
    appointment_id: str,
    new_date: str,
    new_start_time: str,
    patient_phone: str = "",
) -> Dict[str, Any]:
    """Atomically reschedules appointment in the database."""
    logger.info(
        "Voice tool called: reschedule_appointment(id='%s', date='%s', time='%s')",
        appointment_id,
        new_date,
        new_start_time,
    )
    return _apt_service.reschedule_appointment(
        appointment_id=appointment_id,
        new_date=new_date,
        new_start_time=new_start_time,
        patient_phone=patient_phone if patient_phone else None,
    )


@llm.function_tool(
    name="cancel_appointment",
    description="Cancel an appointment and release the time slot back to the hospital schedule.",
)
def voice_cancel_appointment(
    appointment_id: str,
    patient_phone: str = "",
    reason: str = "",
) -> Dict[str, Any]:
    """Atomically cancels appointment and releases the slot."""
    logger.info("Voice tool called: cancel_appointment(id='%s')", appointment_id)
    return _apt_service.cancel_appointment(
        appointment_id=appointment_id,
        patient_phone=patient_phone if patient_phone else None,
        reason=reason,
    )


@llm.function_tool(
    name="get_hospital_info",
    description="Retrieve approved administrative information (address, timings, contacts, departments, payments, preparation).",
)
def voice_get_hospital_info(topic: str = "general") -> Dict[str, Any]:
    """Retrieve approved hospital administrative information."""
    logger.info("Voice tool called: get_hospital_info(topic='%s')", topic)
    return _faq_service.get_hospital_info(topic=topic)


@llm.function_tool(
    name="search_faq",
    description="Search approved hospital FAQs. Returns verified=False if answer is unverified without guessing.",
)
def voice_search_faq(query: str) -> Dict[str, Any]:
    """Search approved hospital FAQs."""
    logger.info("Voice tool called: search_faq(query='%s')", query)
    return _faq_service.search_faq(query=query)


@llm.function_tool(
    name="escalate_to_human",
    description="Escalate call to a human receptionist or record an escalation request.",
)
def voice_escalate_to_human(
    reason: str,
    stated_concern: str,
    urgency_level: str = "ROUTINE",
    patient_phone: str = "",
    patient_name: str = "",
    session_id: str = "",
) -> Dict[str, Any]:
    """Escalate to human receptionist."""
    logger.info("Voice tool called: escalate_to_human(urgency='%s')", urgency_level)
    return _handoff_service.record_handoff(
        session_id=session_id or "VOICE-CALL",
        reason=reason,
        stated_concern=stated_concern,
        urgency_level=urgency_level,
        patient_phone=patient_phone if patient_phone else None,
        patient_name=patient_name if patient_name else None,
    )


@llm.function_tool(
    name="get_emergency_contact",
    description="Get immediate 24x7 emergency and ambulance contact lines for life-threatening symptoms.",
)
def voice_get_emergency_contact() -> Dict[str, Any]:
    """Retrieve emergency contact information."""
    logger.info("Voice tool called: get_emergency_contact")
    return _handoff_service.get_emergency_contacts()


# Master list of bridged voice tools for the LiveKit voice agent
LIVEKIT_BRIDGED_TOOLS = [
    voice_list_doctors,
    voice_get_available_slots,
    voice_book_appointment,
    voice_get_appointment,
    voice_reschedule_appointment,
    voice_cancel_appointment,
    voice_get_hospital_info,
    voice_search_faq,
    voice_escalate_to_human,
    voice_get_emergency_contact,
]
