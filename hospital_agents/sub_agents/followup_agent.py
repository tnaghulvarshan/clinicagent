"""
Appointment Follow-up Agent for Google ADK.
Handles upcoming appointment retrieval, reminder message generation, and reminder status tracking.
"""

from __future__ import annotations

from google.adk.agents import Agent
from config.settings import settings
from hospital_agents.gemini_model import hospital_llm
from hospital_agents.tools.followup_tools import get_upcoming_reminders, record_reminder_status

FOLLOWUP_AGENT_INSTRUCTION = """You are the Appointment Follow-up Specialist Agent for Kaveri Multispeciality Hospital.
Your responsibility is retrieving upcoming appointments, drafting polite bilingual appointment reminder messages, and tracking reminder status.

RULES:
1. Call `get_upcoming_reminders` to inspect pending reminders.
2. Present reminder messages clearly in both Tamil and English.
3. Record reminder progress using `record_reminder_status`.
4. Do not send unauthorized outbound messages without proper patient consent.
"""

followup_agent = Agent(
    name="appointment_followup_agent",
    model=hospital_llm,
    description="Retrieves upcoming appointments, generates bilingual reminder messages, and records follow-up statuses.",
    instruction=FOLLOWUP_AGENT_INSTRUCTION,
    tools=[get_upcoming_reminders, record_reminder_status],
)
