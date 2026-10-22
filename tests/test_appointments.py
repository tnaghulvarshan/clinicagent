"""
Automated unit tests for doctor listings, slot availability, booking,
double-booking prevention, rescheduling, and cancellation.
"""

from __future__ import annotations

import datetime
from pathlib import Path
import pytest
from services.appointment_service import AppointmentService


def test_list_doctors_all(appointment_service: AppointmentService):
    """Listing doctors without filter returns all active doctors."""
    docs = appointment_service.list_doctors()
    assert len(docs) >= 5
    names = [d["name"] for d in docs]
    assert "Dr. Priya Raman" in names
    assert "Dr. Ananya Sundaram" in names


def test_list_doctors_by_department(appointment_service: AppointmentService):
    """Filter doctors by department or specialty."""
    cardio = appointment_service.list_doctors(department="Cardiology")
    assert len(cardio) >= 1
    assert all("Cardiology" in d["department"] for d in cardio)

    pediatric = appointment_service.list_doctors(department="Pediatrics")
    assert len(pediatric) >= 1
    assert "Pediatrics" in pediatric[0]["department"]

    # Non-existent department
    none_found = appointment_service.list_doctors(department="Neuro-Astronautics")
    assert len(none_found) == 0


def test_get_available_slots_valid(appointment_service: AppointmentService):
    """Check slots for a valid doctor on tomorrow's date."""
    docs = appointment_service.list_doctors(department="General Medicine")
    doc_id = docs[0]["id"]
    tomorrow = (datetime.date.today() + datetime.timedelta(days=1)).isoformat()

    result = appointment_service.get_available_slots(doctor_id=doc_id, date_str=tomorrow)
    assert result["success"] is True
    assert result["doctor_name"] == docs[0]["name"]
    assert result["available_slots_count"] > 0
    assert len(result["slots"]) > 0


def test_get_available_slots_invalid_inputs(appointment_service: AppointmentService):
    """Error handling for invalid dates and non-existent doctors."""
    # Invalid date
    res1 = appointment_service.get_available_slots(doctor_id=1, date_str="not-a-date")
    assert res1["success"] is False
    assert "Invalid date" in res1["error"]

    # Non-existent doctor
    tomorrow = (datetime.date.today() + datetime.timedelta(days=1)).isoformat()
    res2 = appointment_service.get_available_slots(doctor_id=9999, date_str=tomorrow)
    assert res2["success"] is False
    assert "not found" in res2["error"]


def test_book_appointment_success(appointment_service: AppointmentService):
    """Successful appointment booking with generated ID and slot locking."""
    docs = appointment_service.list_doctors(department="General Medicine")
    doc_id = docs[0]["id"]
    tomorrow = (datetime.date.today() + datetime.timedelta(days=1)).isoformat()

    # Find an available slot
    slots_res = appointment_service.get_available_slots(doctor_id=doc_id, date_str=tomorrow)
    available_time = slots_res["slots"][-1]["start_time"]

    booking = appointment_service.book_appointment(
        patient_name="Senthil Nathan",
        patient_phone="+919840123456",
        doctor_id=doc_id,
        date_str=tomorrow,
        start_time=available_time,
        reason="Fever and headache",
        preferred_language="Tamil",
    )

    assert booking["success"] is True
    assert booking["appointment_id"].startswith("APT-")
    assert booking["patient_name"] == "Senthil Nathan"
    assert booking["status"] == "BOOKED"
    assert "முன்பதிவு உறுதியானது" in booking["confirmation_message_ta"]

    # Slot must now be marked unavailable
    updated_slots = appointment_service.get_available_slots(doctor_id=doc_id, date_str=tomorrow)
    remaining_times = [s["start_time"] for s in updated_slots["slots"]]
    assert available_time not in remaining_times


def test_prevent_double_booking(appointment_service: AppointmentService):
    """Double-booking the same slot must fail and offer genuine alternatives."""
    docs = appointment_service.list_doctors()
    doc_id = docs[0]["id"]
    tomorrow = (datetime.date.today() + datetime.timedelta(days=1)).isoformat()

    slots_res = appointment_service.get_available_slots(doctor_id=doc_id, date_str=tomorrow)
    target_time = slots_res["slots"][0]["start_time"]

    # First booking succeeds
    first = appointment_service.book_appointment(
        patient_name="Patient One",
        patient_phone="+919111111111",
        doctor_id=doc_id,
        date_str=tomorrow,
        start_time=target_time,
    )
    assert first["success"] is True

    # Second booking for the exact same slot must be rejected
    second = appointment_service.book_appointment(
        patient_name="Patient Two",
        patient_phone="+919222222222",
        doctor_id=doc_id,
        date_str=tomorrow,
        start_time=target_time,
    )
    assert second["success"] is False
    assert "already booked" in second["error"]
    assert "available_alternatives" in second
    assert target_time not in second["available_alternatives"]


def test_book_appointment_missing_patient_details(appointment_service: AppointmentService):
    """Validation: rejects bookings with missing name or phone."""
    tomorrow = (datetime.date.today() + datetime.timedelta(days=1)).isoformat()

    # Empty name
    res1 = appointment_service.book_appointment(
        patient_name="",
        patient_phone="+919876543210",
        doctor_id=1,
        date_str=tomorrow,
        start_time="10:00",
    )
    assert res1["success"] is False
    assert "name is required" in res1["error"]

    # Short / invalid phone
    res2 = appointment_service.book_appointment(
        patient_name="Test Patient",
        patient_phone="123",
        doctor_id=1,
        date_str=tomorrow,
        start_time="10:00",
    )
    assert res2["success"] is False
    assert "phone number is required" in res2["error"]


def test_reschedule_appointment_success(appointment_service: AppointmentService):
    """Rescheduling frees the old slot and books the new slot atomically."""
    docs = appointment_service.list_doctors()
    doc_id = docs[1]["id"]
    tomorrow = (datetime.date.today() + datetime.timedelta(days=1)).isoformat()

    slots_res = appointment_service.get_available_slots(doctor_id=doc_id, date_str=tomorrow)
    initial_slot = slots_res["slots"][0]["start_time"]
    target_new_slot = slots_res["slots"][1]["start_time"]

    # Book initial
    booking = appointment_service.book_appointment(
        patient_name="Ravi Kumar",
        patient_phone="+919841098765",
        doctor_id=doc_id,
        date_str=tomorrow,
        start_time=initial_slot,
    )
    apt_id = booking["appointment_id"]

    # Reschedule
    reschedule_res = appointment_service.reschedule_appointment(
        appointment_id=apt_id,
        new_date=tomorrow,
        new_start_time=target_new_slot,
        patient_phone="+919841098765",
    )
    assert reschedule_res["success"] is True
    assert reschedule_res["status"] == "RESCHEDULED"
    assert reschedule_res["new_time"] == target_new_slot

    # Verify initial slot is now available again!
    check_slots = appointment_service.get_available_slots(doctor_id=doc_id, date_str=tomorrow)
    available_times = [s["start_time"] for s in check_slots["slots"]]
    assert initial_slot in available_times
    assert target_new_slot not in available_times


def test_cancel_appointment_success(appointment_service: AppointmentService):
    """Cancelling an appointment frees the slot and updates status."""
    docs = appointment_service.list_doctors()
    doc_id = docs[0]["id"]
    tomorrow = (datetime.date.today() + datetime.timedelta(days=1)).isoformat()

    slots_res = appointment_service.get_available_slots(doctor_id=doc_id, date_str=tomorrow)
    target_slot = slots_res["slots"][0]["start_time"]

    booking = appointment_service.book_appointment(
        patient_name="Meena Kumari",
        patient_phone="+919888877777",
        doctor_id=doc_id,
        date_str=tomorrow,
        start_time=target_slot,
    )
    apt_id = booking["appointment_id"]

    # Cancel
    cancel_res = appointment_service.cancel_appointment(
        appointment_id=apt_id,
        patient_phone="+919888877777",
        reason="Patient recovered",
    )
    assert cancel_res["success"] is True
    assert cancel_res["status"] == "CANCELLED"

    # Verify slot is free again
    check_slots = appointment_service.get_available_slots(doctor_id=doc_id, date_str=tomorrow)
    available_times = [s["start_time"] for s in check_slots["slots"]]
    assert target_slot in available_times


def test_get_appointment_privacy_verification(appointment_service: AppointmentService):
    """Patient phone check protects appointment details from unauthorized callers."""
    docs = appointment_service.list_doctors()
    tomorrow = (datetime.date.today() + datetime.timedelta(days=1)).isoformat()
    slots_res = appointment_service.get_available_slots(doctor_id=docs[0]["id"], date_str=tomorrow)

    booking = appointment_service.book_appointment(
        patient_name="Secret Patient",
        patient_phone="+919999900000",
        doctor_id=docs[0]["id"],
        date_str=tomorrow,
        start_time=slots_res["slots"][0]["start_time"],
    )
    apt_id = booking["appointment_id"]

    # Correct phone -> success
    res_ok = appointment_service.get_appointment(apt_id, patient_phone="+919999900000")
    assert res_ok["success"] is True
    assert res_ok["appointment"]["patient_name"] == "Secret Patient"

    # Wrong phone -> security failure
    res_fail = appointment_service.get_appointment(apt_id, patient_phone="+911111122222")
    assert res_fail["success"] is False
    assert "verification failed" in res_fail["error"]
