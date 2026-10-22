"""
Doctor lookup tools for Google ADK agents.
"""

from __future__ import annotations

from typing import Any, Dict, List
from services.appointment_service import AppointmentService

_service = AppointmentService()


def list_doctors(department: str = "") -> Dict[str, Any]:
    """
    List doctors available at the hospital, optionally filtered by medical department or specialty.

    Args:
        department: Optional department name to filter by (e.g. 'General Medicine', 'Cardiology',
                    'Pediatrics', 'Orthopedics', 'ENT', 'Gynecology'). Leave empty to list all doctors.

    Returns:
        Dict with list of doctors, their specialties, qualifications, languages, consultation fees, and room numbers.
    """
    doctors = _service.list_doctors(department=department)
    return {
        "success": True,
        "count": len(doctors),
        "department_filter": department,
        "doctors": doctors,
    }
