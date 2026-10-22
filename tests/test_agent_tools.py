"""
Unit tests for all Google ADK agent tool callables.
"""

from __future__ import annotations

import datetime
from pathlib import Path
import pytest

from hospital_agents.tools.doctor_tools import list_doctors
from hospital_agents.tools.appointment_tools import (
    get_available_slots,
    book_appointment,
    get_appointment,
    reschedule_appointment,
    cancel_appointment,
)
from hospital_agents.tools.faq_tools import get_hospital_info, search_faq
from hospital_agents.tools.handoff_tools import escalate_to_human, get_emergency_contact
from hospital_agents.tools.followup_tools import get_upcoming_reminders, record_reminder_status


def test_doctor_tools():
    """Verify list_doctors callable returns active doctors."""
    res = list_doctors()
    assert res["success"] is True
    assert res["count"] >= 5


def test_faq_tools_approved_topics():
    """Verify get_hospital_info returns verified information on approved topics."""
    addr = get_hospital_info(topic="address")
    assert addr["success"] is True
    assert addr["verified"] is True
    assert "Chennai" in addr["address_en"]
    assert "சென்னை" in addr["address_ta"]

    timings = get_hospital_info(topic="timings")
    assert timings["verified"] is True
    assert "24" in timings["emergency_en"]

    payments = get_hospital_info(topic="payments")
    assert payments["verified"] is True
    assert any("UPI" in p for p in payments["accepted_payment_methods"])


def test_faq_tools_search_and_unverified_fallback():
    """Verify search_faq returns verified answers for known topics and safe fallback for unknown."""
    # Known topic query
    res_known = search_faq("Where is the hospital located?")
    assert res_known["success"] is True
    assert res_known["verified"] is True
    assert "Teynampet" in res_known["answer_en"]

    # Unknown topic -> MUST NOT GUESS, offer human receptionist
    res_unknown = search_faq("Can I bring my pet iguana into the surgery theater?")
    assert res_unknown["verified"] is False
    assert res_unknown["suggest_handoff"] is True
    assert "cannot verify" in res_unknown["message_en"]


def test_handoff_tools():
    """Verify escalation and emergency contact retrieval."""
    emerg = get_emergency_contact()
    assert "108" in emerg["ambulance"]
    assert "2499-1066" in emerg["emergency_hotline"]

    handoff = escalate_to_human(
        reason="Complex billing question",
        stated_concern="Patient wants breakdown of international travel insurance cover",
        urgency_level="ROUTINE",
        patient_phone="+919876543210",
    )
    assert handoff["success"] is True
    assert handoff["handoff_id"] is not None
    assert handoff["status"] == "RECORDED"


def test_followup_tools():
    """Verify follow-up reminders retrieval and status updates."""
    reminders = get_upcoming_reminders(limit=5)
    assert reminders["success"] is True
    assert isinstance(reminders["reminders"], list)

    if reminders["reminders"]:
        r_id = reminders["reminders"][0]["id"]
        upd = record_reminder_status(reminder_id=r_id, status="SENT")
        assert upd["success"] is True
        assert upd["status"] == "SENT"

    # Invalid status
    upd_bad = record_reminder_status(reminder_id=1, status="DISAPPEARED")
    assert upd_bad["success"] is False
    assert "Invalid status" in upd_bad["error"]


def test_faq_tamil_queries():
    """Verify search_faq with Tamil queries."""
    res_ta = search_faq("மருத்துவமனை முகவரி என்ன?")
    assert res_ta["success"] is True
    assert res_ta["verified"] is True
    assert "சென்னை" in res_ta["answer_ta"]

    res_timing = search_faq("நேரம் எப்போது?")
    assert res_timing["success"] is True
    assert res_timing["verified"] is True


def test_appointment_tools_end_to_end():
    """Test full cycle: slots -> book -> get -> reschedule -> cancel via tools."""
    docs = list_doctors(department="Pediatrics")
    assert docs["count"] >= 1
    doc_id = docs["doctors"][0]["id"]

    tomorrow = (datetime.date.today() + datetime.timedelta(days=1)).isoformat()
    slots = get_available_slots(doctor_id=doc_id, date=tomorrow)
    assert slots["success"] is True
    assert len(slots["slots"]) >= 2
    time1 = slots["slots"][0]["start_time"]
    time2 = slots["slots"][1]["start_time"]

    # 1. Book
    booking = book_appointment(
        patient_name="Baby Ananya",
        patient_phone="+919444455555",
        doctor_id=doc_id,
        date=tomorrow,
        start_time=time1,
        reason="Routine vaccination",
        preferred_language="Tamil",
    )
    assert booking["success"] is True
    apt_id = booking["appointment_id"]

    # 2. Get
    get_res = get_appointment(apt_id, patient_phone="+919444455555")
    assert get_res["success"] is True
    assert get_res["appointment"]["doctor_name"] == docs["doctors"][0]["name"]

    # 3. Reschedule
    reschedule_res = reschedule_appointment(
        appointment_id=apt_id,
        new_date=tomorrow,
        new_start_time=time2,
        patient_phone="+919444455555",
    )
    assert reschedule_res["success"] is True
    assert reschedule_res["status"] == "RESCHEDULED"

    # 4. Cancel
    cancel_res = cancel_appointment(
        appointment_id=apt_id,
        patient_phone="+919444455555",
        reason="Rescheduled elsewhere",
    )
    assert cancel_res["success"] is True
    assert cancel_res["status"] == "CANCELLED"
