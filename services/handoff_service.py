"""
Human handoff and emergency escalation service.
Records escalation requests with reasons, patient concern, timestamps, and status.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, Optional, Union

from config.settings import settings
from database.connection import create_connection, get_db_path, transaction

logger = logging.getLogger(__name__)


class HandoffService:
    def __init__(self, db_path: Optional[Union[str, Path]] = None) -> None:
        self.db_path = get_db_path(db_path)

    def record_handoff(
        self,
        session_id: str,
        reason: str,
        stated_concern: str,
        urgency_level: str = "ROUTINE",
        patient_phone: Optional[str] = None,
        patient_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Record a human handoff request in SQLite and log an audit event.
        Urgency levels: 'ROUTINE', 'URGENT', 'EMERGENCY'.
        """
        clean_urgency = urgency_level.strip().upper()
        if clean_urgency not in ("ROUTINE", "URGENT", "EMERGENCY"):
            clean_urgency = "ROUTINE"

        destination = (
            settings.emergency_hotline
            if clean_urgency == "EMERGENCY"
            else settings.receptionist_phone
        )

        conn = create_connection(self.db_path)
        try:
            with transaction(conn):
                cur = conn.execute(
                    """
                    INSERT INTO human_handoff_requests
                    (session_id, patient_phone, patient_name, reason, stated_concern, urgency_level, handoff_destination, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, 'RECORDED')
                    """,
                    (
                        session_id,
                        patient_phone,
                        patient_name,
                        reason,
                        stated_concern,
                        clean_urgency,
                        destination,
                    ),
                )
                handoff_id = cur.lastrowid

                conn.execute(
                    """
                    INSERT INTO audit_events (event_type, entity_type, entity_id, details)
                    VALUES ('HUMAN_HANDOFF', 'handoff_request', ?, ?)
                    """,
                    (
                        str(handoff_id),
                        f"Urgency: {clean_urgency}. Reason: {reason}. Concern: {stated_concern[:100]}",
                    ),
                )

            if clean_urgency == "EMERGENCY":
                msg_en = (
                    f"EMERGENCY ESCALATION: Please call our 24x7 Emergency Care immediately at {destination} "
                    f"or call Ambulance at 108. Do not wait. Handoff Ref: #{handoff_id}."
                )
                msg_ta = (
                    f"அவசர மருத்துவ உதவி: தாமதிக்காமல் உடனே எங்கள் 24 மணி நேர அவசர சிகிச்சை பிரிவை "
                    f"{destination} அல்லது ஆம்புலன்ஸ் 108 எண்ணில் அழைக்கவும். குறிப்பு எண்: #{handoff_id}."
                )
            else:
                msg_en = (
                    f"I have recorded your request (Ref: #{handoff_id}). A human receptionist will assist you. "
                    f"You may also call our reception desk directly at {destination}."
                )
                msg_ta = (
                    f"தங்கள் கோரிக்கை பதிவு செய்யப்பட்டது (எண்: #{handoff_id}). எங்கள் வரவேற்பாளர் உங்களுக்கு உதவுவார். "
                    f"வரவேற்பறையை {destination} என்ற எண்ணிலும் தொடர்பு கொள்ளலாம்."
                )

            return {
                "success": True,
                "handoff_id": handoff_id,
                "session_id": session_id,
                "urgency_level": clean_urgency,
                "destination": destination,
                "status": "RECORDED",
                "message_en": msg_en,
                "message_ta": msg_ta,
            }
        finally:
            conn.close()

    def get_emergency_contacts(self) -> Dict[str, Any]:
        """Return immediate emergency numbers and ambulance lines."""
        return {
            "emergency_hotline": settings.emergency_hotline,
            "ambulance": "108",
            "hospital_address": "No. 45, Anna Salai, Teynampet, Chennai 600018",
            "message_en": (
                f"For immediate medical emergencies, call 108 or our Emergency Unit at {settings.emergency_hotline}. "
                "Our Emergency Department is open 24 hours a day at No. 45, Anna Salai, Teynampet."
            ),
            "message_ta": (
                f"உடனடி அவசர மருத்துவ தேவைக்கு 108 அல்லது எங்களின் அவசர சிகிச்சை எண் {settings.emergency_hotline}-ஐ அழைக்கவும். "
                "எங்கள் அவசர சிகிச்சைப் பிரிவு 24 மணி நேரமும் எண் 45, அண்ணா சாலை, தேனாம்பேட்டையில் செயல்படுகிறது."
            ),
        }
