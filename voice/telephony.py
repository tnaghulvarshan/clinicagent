"""
LiveKit SIP Telephony Integration Module.
Handles incoming telephone calls, caller ID extraction from SIP trunk metadata,
and documents provider configuration for real phone numbers.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional
from livekit import rtc

logger = logging.getLogger(__name__)


class TelephonyManager:
    """
    Manages telephone callers arriving via LiveKit SIP Inbound Trunks.
    Extracts caller phone numbers, call metadata, and routes to the voice agent.
    """

    @staticmethod
    def extract_caller_phone(participant: rtc.RemoteParticipant) -> Optional[str]:
        """
        Extract the calling party's phone number from LiveKit SIP participant metadata.
        Standard LiveKit SIP trunks populate participant identity or attributes:
        - `participant.attributes.get('sip.phoneNumber')`
        - `participant.identity` (often formatted as `sip_+919876543210` or `+919876543210`)
        """
        # 1. Check SIP participant attributes
        if hasattr(participant, "attributes") and participant.attributes:
            sip_num = (
                participant.attributes.get("sip.phoneNumber")
                or participant.attributes.get("phone")
                or participant.attributes.get("caller_id")
            )
            if sip_num:
                logger.info("Extracted caller phone from SIP attributes: %s", sip_num)
                return str(sip_num).strip()

        # 2. Check participant identity
        identity = participant.identity or ""
        if identity.startswith("sip_"):
            num = identity[4:]
            logger.info("Extracted caller phone from SIP identity: %s", num)
            return num

        # If identity is a phone number with country code (e.g. +91...)
        if identity.startswith("+") and len(identity) >= 10:
            return identity

        return None

    @staticmethod
    def is_sip_call(participant: rtc.RemoteParticipant) -> bool:
        """Determines if the participant joined through a telephony/SIP trunk."""
        if hasattr(participant, "attributes") and participant.attributes:
            if "sip.callID" in participant.attributes or "sip.trunkID" in participant.attributes:
                return True
        return participant.identity.startswith("sip_") if participant.identity else False

    @staticmethod
    def get_telephony_setup_guide() -> Dict[str, Any]:
        """
        Returns structured documentation on configuring a real phone number
        using LiveKit SIP with providers like Twilio, Telnyx, or Plivo.
        """
        return {
            "milestone": "Real Phone Calls via LiveKit SIP",
            "prerequisites": [
                "A LiveKit Cloud project or self-hosted LiveKit Server with SIP service enabled.",
                "A phone number purchased from a telephony provider (e.g. Twilio, Telnyx, Plivo, Tata Tele).",
                "SIP Trunk configured to forward incoming calls to your LiveKit SIP URI.",
            ],
            "setup_steps": [
                {
                    "step": 1,
                    "title": "Create Inbound SIP Trunk in LiveKit",
                    "command": "lk sip inbound create inbound-trunk.json",
                    "sample_config": {
                        "name": "Kaveri Hospital Telephony Inbound",
                        "numbers": ["+914424991000", "+18005550199"],
                    },
                },
                {
                    "step": 2,
                    "title": "Create LiveKit SIP Dispatch Rule",
                    "description": "Routes incoming phone calls to a dedicated room for the receptionist agent.",
                    "command": "lk sip dispatch-rule create dispatch-rule.json",
                    "sample_config": {
                        "name": "hospital-voice-dispatch",
                        "rule": {
                            "dispatchRuleIndividual": {
                                "roomPrefix": "hospital-call-"
                            }
                        },
                    },
                },
                {
                    "step": 3,
                    "title": "Configure Telephony Provider (e.g., Twilio SIP Termination)",
                    "description": "Point your purchased phone number's SIP Termination URI to your LiveKit project SIP endpoint (e.g., sip.livekit.cloud).",
                },
                {
                    "step": 4,
                    "title": "Start LiveKit Agent Worker",
                    "description": "Run the agent worker to automatically accept room calls created by the dispatch rule.",
                    "command": "python voice/livekit_agent.py start",
                },
            ],
            "cost_notes": "LiveKit Cloud offers free tiers for development. Telephony numbers and SIP trunk termination are paid by the respective telephony carrier (Twilio/Telnyx).",
        }
