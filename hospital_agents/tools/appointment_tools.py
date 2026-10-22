"""
Appointment scheduling and management tools for Google ADK agents.
"""

from __future__ import annotations

from typing import Any, Dict, Optional
from services.appointment_service import AppointmentService

_service = AppointmentService()


def get_available_slots(doctor_id: int, date: str) -> Dict[str, Any]:
    """
    Check real database availability for a doctor on a specific date. Never invents slots.

    Args:
        doctor_id: The ID of the doctor (obtained from list_doctors).
        date: The date to check in YYYY-MM-DD format (e.g., '2026-10-23').

    Returns:
        Dict containing doctor details, date, and list of genuinely available time slots.
    """
    return _service.get_available_slots(doctor_id=doctor_id, date_str=date)


def book_appointment(
    patient_name: str,
    patient_phone: str,
    doctor_id: int,
    date: str,
    start_time: str,
    reason: str = "",
    preferred_language: str = "Tamil",
) -> Dict[str, Any]:
    """
    Book an appointment after checking genuine slot availability and patient confirmation.
    Uses atomic database transactions to guarantee against double booking.

    Args:
        patient_name: Full name of the patient.
        patient_phone: Phone number of the patient (e.g. '+919876543210' or '9876543210').
        doctor_id: Doctor's integer ID.
        date: Date in YYYY-MM-DD format.
        start_time: Desired slot start time in HH:MM format (e.g. '09:00', '10:30').
        reason: Optional brief reason for consultation (e.g. 'fever', 'joint pain').
        preferred_language: 'Tamil' or 'English'.

    Returns:
        Dict with booking status, unique appointment ID, doctor details, and bilingual confirmation.
    """
    return _service.book_appointment(
        patient_name=patient_name,
        patient_phone=patient_phone,
        doctor_id=doctor_id,
        date_str=date,
        start_time=start_time,
        reason=reason,
        preferred_language=preferred_language,
    )


def get_appointment(appointment_id: str, patient_phone: str = "") -> Dict[str, Any]:
    """
    Retrieve details of an existing appointment.
    Verifies patient phone if provided to protect patient privacy.

    Args:
        appointment_id: The unique appointment ID (e.g. 'APT-20261023-A1B2').
        patient_phone: Optional patient phone number for identity verification.

    Returns:
        Dict containing appointment date, time, doctor, room number, and booking status.
    """
    return _service.get_appointment(
        appointment_id=appointment_id,
        patient_phone=patient_phone if patient_phone else None,
    )


def reschedule_appointment(
    appointment_id: str,
    new_date: str,
    new_start_time: str,
    patient_phone: str = "",
) -> Dict[str, Any]:
    """
    Reschedule an existing appointment to a new date and time.
    Frees the previous slot and reserves the new slot atomically.

    Args:
        appointment_id: The appointment ID to reschedule.
        new_date: Desired new date in YYYY-MM-DD format.
        new_start_time: Desired new start time in HH:MM format.
        patient_phone: Optional patient phone number for identity verification.

    Returns:
        Dict with updated appointment confirmation or available alternatives if slot was taken.
    """
    return _service.reschedule_appointment(
        appointment_id=appointment_id,
        new_date=new_date,
        new_start_time=new_start_time,
        patient_phone=patient_phone if patient_phone else None,
    )


def cancel_appointment(
    appointment_id: str,
    patient_phone: str = "",
    reason: str = "",
) -> Dict[str, Any]:
    """
    Cancel an existing appointment and release the slot for other patients.

    Args:
        appointment_id: The appointment ID to cancel.
        patient_phone: Optional patient phone number for identity verification.
        reason: Optional reason for cancellation.

    Returns:
        Dict confirming cancellation and slot release.
    """
    return _service.cancel_appointment(
        appointment_id=appointment_id,
        patient_phone=patient_phone if patient_phone else None,
        reason=reason,
    )
