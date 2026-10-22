"""
Hospital FAQ and administrative information tools for Google ADK agents.
"""

from __future__ import annotations

from typing import Any, Dict
from services.faq_service import FAQService

_service = FAQService()


def get_hospital_info(topic: str = "general") -> Dict[str, Any]:
    """
    Retrieve approved administrative information about the hospital.

    Args:
        topic: The topic of inquiry. Supported values:
               - 'address' / 'location' / 'landmark': Physical location and address.
               - 'timings' / 'hours': OPD, Sunday, emergency, and pharmacy timings.
               - 'contacts': Reception, emergency, ambulance, and appointment phone numbers.
               - 'departments': List of medical departments and services offered.
               - 'payments' / 'insurance': Accepted payment methods and health insurance schemes.
               - 'preparation': Preparation guidelines for fasting blood tests and ultrasounds.
               - 'general': General overview of the hospital.

    Returns:
        Dict with verified information from hospital records.
    """
    return _service.get_hospital_info(topic=topic)


def search_faq(query: str) -> Dict[str, Any]:
    """
    Search approved hospital FAQ entries by user question or keywords.
    If the question is not covered in verified records, returns verified=False and suggests human handoff.

    Args:
        query: Patient's question or search terms (in English, Tamil, or Tanglish).

    Returns:
        Dict with verified answers or human handoff recommendation.
    """
    return _service.search_faq(query=query)
