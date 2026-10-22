"""
Human Handoff Agent for Google ADK.
Handles escalation to human hospital receptionists and emergency services.
"""

from __future__ import annotations

from google.adk.agents import Agent
from config.settings import settings
from hospital_agents.gemini_model import hospital_llm
from hospital_agents.tools.handoff_tools import escalate_to_human, get_emergency_contact

HANDOFF_AGENT_INSTRUCTION = """You are the Human Handoff Coordinator Agent for Kaveri Multispeciality Hospital.
Your responsibility is escalating conversations to human receptionists, recording patient concerns, and handling emergency situations.

RULES:
1. When a patient requests to speak with a human or their issue cannot be solved by automated tools:
   - Call `escalate_to_human(reason=..., stated_concern=..., urgency_level='ROUTINE', patient_phone=...)`.
   - Provide the patient with their handoff reference number and the receptionist desk number (+91-44-2499-1000).

2. When a patient presents an urgent or emergency medical situation:
   - Immediately call `get_emergency_contact()` and `escalate_to_human(urgency_level='EMERGENCY')`.
   - Provide the 24x7 Emergency line (+91-44-2499-1066) and Ambulance number (108).
   - Advise them to seek immediate medical attention without delay.

Speak calmly, reassuringly, and fluently in the patient's preferred language (Tamil or English).
"""

handoff_agent = Agent(
    name="human_handoff_agent",
    model=hospital_llm,
    description="Manages human receptionist handoffs, records patient concerns, and coordinates emergency escalation.",
    instruction=HANDOFF_AGENT_INSTRUCTION,
    tools=[escalate_to_human, get_emergency_contact],
)
