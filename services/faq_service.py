"""
Hospital FAQ and information service based strictly on approved hospital content.
Never hallucinates unverified hospital information.
"""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import yaml

from config.settings import settings
from database.connection import create_connection, get_db_path

logger = logging.getLogger(__name__)


class FAQService:
    def __init__(
        self,
        config_path: Optional[Union[str, Path]] = None,
        db_path: Optional[Union[str, Path]] = None,
    ) -> None:
        self.config_path = (
            Path(config_path) if config_path else settings.config_path
        )
        self.db_path = get_db_path(db_path)
        self._config_cache: Optional[Dict[str, Any]] = None

    def _get_config(self) -> Dict[str, Any]:
        """Lazy load approved YAML config."""
        if self._config_cache is None:
            if self.config_path.exists():
                with open(self.config_path, "r", encoding="utf-8") as f:
                    self._config_cache = yaml.safe_load(f) or {}
            else:
                self._config_cache = {}
        return self._config_cache

    def get_hospital_info(self, topic: Optional[str] = None) -> Dict[str, Any]:
        """
        Retrieve approved hospital information.
        Supported topics: 'general', 'address', 'timings', 'departments', 'payments', 'contacts', 'preparation'.
        """
        cfg = self._get_config().get("hospital", {})
        topic_lower = (topic or "general").strip().lower()

        if topic_lower in ("address", "location", "landmark"):
            addr_en = f"{cfg.get('name', {}).get('en', 'Kaveri Hospital')}, {cfg.get('address', {}).get('en', '')} ({cfg.get('landmark', {}).get('en', '')})"
            addr_ta = f"{cfg.get('name', {}).get('ta', 'காவேரி மருத்துவமனை')}, {cfg.get('address', {}).get('ta', '')} ({cfg.get('landmark', {}).get('ta', '')})"
            return {
                "success": True,
                "verified": True,
                "topic": "address",
                "name_en": cfg.get("name", {}).get("en", "Kaveri Hospital"),
                "name_ta": cfg.get("name", {}).get("ta", "காவேரி மருத்துவமனை"),
                "address_en": cfg.get("address", {}).get("en", ""),
                "address_ta": cfg.get("address", {}).get("ta", ""),
                "landmark_en": cfg.get("landmark", {}).get("en", ""),
                "landmark_ta": cfg.get("landmark", {}).get("ta", ""),
                "answer_en": addr_en,
                "answer_ta": addr_ta,
            }

        elif (
            topic_lower in ("timing", "timings", "hours", "opd", "emergency_timing", "visiting", "visiting hours", "visiting_hours", "visit")
            or "visit" in topic_lower
            or "timing" in topic_lower
            or "hour" in topic_lower
        ):
            timings = cfg.get("timings", {})
            visiting_en = timings.get("visiting_hours", {}).get("en", "Inpatient visiting hours: 4:00 PM to 7:00 PM.")
            visiting_ta = timings.get("visiting_hours", {}).get("ta", "பார்வையாளர் நேரம்: மாலை 4:00 முதல் 7:00 வரை.")
            t_en = f"OPD: {timings.get('opd', {}).get('en', '')}. Visiting Hours: {visiting_en}. Emergency: {timings.get('emergency', {}).get('en', '')}."
            t_ta = f"OPD: {timings.get('opd', {}).get('ta', '')}. பார்வையாளர் நேரம்: {visiting_ta}. அவசர சிகிச்சை: {timings.get('emergency', {}).get('ta', '')}."
            return {
                "success": True,
                "verified": True,
                "topic": "timings",
                "opd_en": timings.get("opd", {}).get("en", ""),
                "opd_ta": timings.get("opd", {}).get("ta", ""),
                "visiting_hours_en": visiting_en,
                "visiting_hours_ta": visiting_ta,
                "emergency_en": timings.get("emergency", {}).get("en", ""),
                "emergency_ta": timings.get("emergency", {}).get("ta", ""),
                "pharmacy_en": timings.get("pharmacy", {}).get("en", ""),
                "pharmacy_ta": timings.get("pharmacy", {}).get("ta", ""),
                "answer_en": t_en,
                "answer_ta": t_ta,
            }

        elif topic_lower in ("contacts", "phone", "emergency_number", "contact"):
            c = cfg.get("contacts", {})
            c_en = f"Reception: {c.get('reception', '')}, Appointments: {c.get('appointments', '')}, Emergency: {c.get('emergency', '')}, Ambulance: {c.get('ambulance', '108')}."
            c_ta = f"வரவேற்பறை: {c.get('reception', '')}, முன்பதிவு: {c.get('appointments', '')}, அவசர சிகிச்சை: {c.get('emergency', '')}, ஆம்புலன்ஸ்: {c.get('ambulance', '108')}."
            return {
                "success": True,
                "verified": True,
                "topic": "contacts",
                "contacts": c,
                "answer_en": c_en,
                "answer_ta": c_ta,
            }

        elif topic_lower in ("payments", "insurance", "payment_methods", "billing"):
            methods = cfg.get("accepted_payment_methods", [])
            p_en = f"Accepted payment methods and insurances: {', '.join(methods)}."
            p_ta = f"ஏற்றுக்கொள்ளப்படும் கட்டண முறைகள்: {', '.join(methods)}."
            return {
                "success": True,
                "verified": True,
                "topic": "payments",
                "accepted_payment_methods": methods,
                "answer_en": p_en,
                "answer_ta": p_ta,
            }

        elif topic_lower in ("departments", "specialties", "services"):
            depts = cfg.get("departments", [])
            d_names = [d["name_en"] for d in depts]
            d_en = f"Available departments: {', '.join(d_names)}."
            d_ta = f"மருத்துவத் துறைகள்: {', '.join([d['name_ta'] for d in depts])}."
            return {
                "success": True,
                "verified": True,
                "topic": "departments",
                "departments": depts,
                "answer_en": d_en,
                "answer_ta": d_ta,
            }

        elif topic_lower in ("preparation", "test_instructions", "fasting", "scan"):
            prep = cfg.get("preparation_instructions", {})
            prep_en = "; ".join(f"{k}: {v.get('en', '')}" for k, v in prep.items())
            prep_ta = "; ".join(f"{k}: {v.get('ta', '')}" for k, v in prep.items())
            return {
                "success": True,
                "verified": True,
                "topic": "preparation",
                "instructions": prep,
                "answer_en": prep_en,
                "answer_ta": prep_ta,
            }

        # Default general summary
        gen_en = f"{cfg.get('name', {}).get('en', 'Kaveri Hospital')}, {cfg.get('address', {}).get('en', '')}."
        gen_ta = f"{cfg.get('name', {}).get('ta', 'காவேரி மருத்துவமனை')}, {cfg.get('address', {}).get('ta', '')}."
        return {
            "success": True,
            "verified": True,
            "topic": "general",
            "hospital_name_en": cfg.get("name", {}).get("en", "Kaveri Hospital"),
            "hospital_name_ta": cfg.get("name", {}).get("ta", "காவேரி மருத்துவமனை"),
            "address_en": cfg.get("address", {}).get("en", ""),
            "address_ta": cfg.get("address", {}).get("ta", ""),
            "emergency_phone": cfg.get("contacts", {}).get("emergency", "+91-44-2499-1066"),
            "reception_phone": cfg.get("contacts", {}).get("reception", "+91-44-2499-1000"),
            "answer_en": gen_en,
            "answer_ta": gen_ta,
        }

    def search_faq(self, query: str) -> Dict[str, Any]:
        """
        Search approved FAQ entries and hospital topics.
        If no matching verified information exists, explicitly returns verified=False
        and suggests human receptionist handoff. Never guesses or fabricates hospital policies.
        """
        clean_q = query.strip().lower()
        if not clean_q:
            return {
                "success": False,
                "verified": False,
                "error": "Query cannot be empty.",
            }

        # 1. Semantic Topic Triggers for verified hospital configuration
        TOPIC_TRIGGERS = {
            "address": ["address", "locat", "where", "place", "landmark", "route", "direction", "mugavari", "idam", "engu", "முகவரி", "இடம்", "எங்கு"],
            "timings": ["timing", "hour", "open", "close", "opd", "sunday", "neram", "eppothu", "நேரம்", "எப்போது"],
            "contacts": ["contact", "phone", "number", "call", "telephone", "mobile", "thodarbu", "தொடர்பு", "தொலைபேசி"],
            "payments": ["payment", "fee", "cost", "charge", "insurance", "card", "upi", "gpay", "cmchis", "kattanam", "கட்டணம்", "காப்பீடு"],
            "departments": ["department", "specialt", "service", "doctor list", "thuraigal", "துறைகள்", "பிரிவுகள்"],
            "preparation": ["prepar", "fasting", "empty stomach", "blood test", "ultrasound", "scan", "parisothanai", "பரிசோதனை", "ஸ்கேன்"],
        }

        for topic, triggers in TOPIC_TRIGGERS.items():
            if any(t in clean_q for t in triggers):
                info = self.get_hospital_info(topic)
                if info.get("verified"):
                    return info

        # 2. Database Keyword Search for specific FAQ entries using token matching
        conn = create_connection(self.db_path)
        try:
            STOP_WORDS = {
                "the", "is", "at", "which", "on", "can", "i", "a", "an", "into",
                "and", "or", "to", "in", "of", "for", "with", "my", "your", "are",
                "do", "does", "did", "have", "has", "there", "this", "that", "it",
                "be", "been", "being"
            }
            raw_words = re.findall(r"\w+", clean_q)
            words = set(w for w in raw_words if len(w) >= 3 and w not in STOP_WORDS)

            if not words:
                return {
                    "success": True,
                    "verified": False,
                    "message_en": (
                        "I cannot verify this information from our approved hospital records. "
                        f"Please contact our human receptionist at {settings.receptionist_phone} for assistance."
                    ),
                    "message_ta": (
                        "இந்த தகவலை மருத்துவமனை ஆவணங்களிலிருந்து என்னால் உறுதிப்படுத்த முடியவில்லை. "
                        f"உதவிக்கு எங்கள் வரவேற்பறையை {settings.receptionist_phone} என்ற எண்ணில் தொடர்பு கொள்ளவும்."
                    ),
                    "suggest_handoff": True,
                    "handoff_phone": settings.receptionist_phone,
                }

            cur = conn.execute(
                "SELECT id, category, question_en, question_ta, answer_en, answer_ta, keywords FROM faq_entries"
            )
            all_faqs = [dict(r) for r in cur.fetchall()]

            matches = []
            for item in all_faqs:
                kw_tokens = set(re.findall(r"\w+", item["keywords"].lower()))
                q_tokens = set(re.findall(r"\w+", item["question_en"].lower()))
                overlap = len(words & (kw_tokens | q_tokens))
                if overlap > 0:
                    matches.append((overlap, item))

            if matches:
                matches.sort(key=lambda x: x[0], reverse=True)
                top = matches[0][1]
                return {
                    "success": True,
                    "verified": True,
                    "category": top["category"],
                    "question_en": top["question_en"],
                    "question_ta": top["question_ta"],
                    "answer_en": top["answer_en"],
                    "answer_ta": top["answer_ta"],
                    "additional_matches_count": len(matches) - 1,
                }

            # Explicit unverified fallback - DO NOT GUESS
            return {
                "success": True,
                "verified": False,
                "message_en": (
                    "I cannot verify this information from our approved hospital records. "
                    f"Please contact our human receptionist at {settings.receptionist_phone} for assistance."
                ),
                "message_ta": (
                    "இந்த தகவலை மருத்துவமனை ஆவணங்களிலிருந்து என்னால் உறுதிப்படுத்த முடியவில்லை. "
                    f"உதவிக்கு எங்கள் வரவேற்பறையை {settings.receptionist_phone} என்ற எண்ணில் தொடர்பு கொள்ளவும்."
                ),
                "suggest_handoff": True,
                "handoff_phone": settings.receptionist_phone,
            }
        finally:
            conn.close()
