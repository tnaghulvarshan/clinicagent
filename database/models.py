"""
Database schemas, table definitions, and data models for Hospital AI Agent.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

SCHEMA_SQL = """
-- 1. Doctors table
CREATE TABLE IF NOT EXISTS doctors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    department TEXT NOT NULL,
    qualification TEXT NOT NULL,
    languages TEXT NOT NULL DEFAULT 'Tamil, English',
    consultation_fee INTEGER NOT NULL DEFAULT 500,
    room_number TEXT NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_doctors_department ON doctors(department);
CREATE INDEX IF NOT EXISTS idx_doctors_active ON doctors(is_active);

-- 2. Doctor Schedules table (weekly template)
CREATE TABLE IF NOT EXISTS doctor_schedules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    doctor_id INTEGER NOT NULL,
    day_of_week TEXT NOT NULL,
    start_time TEXT NOT NULL, -- HH:MM
    end_time TEXT NOT NULL,   -- HH:MM
    slot_duration_minutes INTEGER NOT NULL DEFAULT 30,
    FOREIGN KEY (doctor_id) REFERENCES doctors(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_schedules_doctor_day ON doctor_schedules(doctor_id, day_of_week);

-- 3. Available and Booked Slots
CREATE TABLE IF NOT EXISTS slots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    doctor_id INTEGER NOT NULL,
    slot_date TEXT NOT NULL,   -- YYYY-MM-DD
    start_time TEXT NOT NULL,  -- HH:MM
    end_time TEXT NOT NULL,    -- HH:MM
    is_available BOOLEAN NOT NULL DEFAULT 1,
    FOREIGN KEY (doctor_id) REFERENCES doctors(id) ON DELETE CASCADE,
    CONSTRAINT uq_doctor_slot UNIQUE (doctor_id, slot_date, start_time)
);

CREATE INDEX IF NOT EXISTS idx_slots_query ON slots(doctor_id, slot_date, is_available);
CREATE INDEX IF NOT EXISTS idx_slots_date ON slots(slot_date);

-- 4. Patients table (minimal data required for booking)
CREATE TABLE IF NOT EXISTS patients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    phone TEXT NOT NULL UNIQUE,
    preferred_language TEXT NOT NULL DEFAULT 'Tamil',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_patients_phone ON patients(phone);

-- 5. Appointments table
CREATE TABLE IF NOT EXISTS appointments (
    id TEXT PRIMARY KEY, -- e.g. APT-20261023-A1B2
    patient_id INTEGER NOT NULL,
    doctor_id INTEGER NOT NULL,
    slot_id INTEGER, -- Associated slot, enforced unique for active bookings
    appointment_date TEXT NOT NULL,
    start_time TEXT NOT NULL,
    end_time TEXT NOT NULL,
    reason TEXT DEFAULT '',
    status TEXT NOT NULL DEFAULT 'BOOKED', -- BOOKED, RESCHEDULED, CANCELLED, COMPLETED
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_id) REFERENCES patients(id),
    FOREIGN KEY (doctor_id) REFERENCES doctors(id),
    FOREIGN KEY (slot_id) REFERENCES slots(id)
);

-- Partial unique index: strictly prevents double booking among active appointments
CREATE UNIQUE INDEX IF NOT EXISTS uq_active_appointment_slot ON appointments(slot_id) WHERE status NOT IN ('CANCELLED');
CREATE INDEX IF NOT EXISTS idx_appointments_patient ON appointments(patient_id);
CREATE INDEX IF NOT EXISTS idx_appointments_doctor ON appointments(doctor_id);
CREATE INDEX IF NOT EXISTS idx_appointments_date ON appointments(appointment_date);
CREATE INDEX IF NOT EXISTS idx_appointments_status ON appointments(status);

-- 6. Hospital FAQ Entries
CREATE TABLE IF NOT EXISTS faq_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category TEXT NOT NULL,
    question_en TEXT NOT NULL,
    question_ta TEXT NOT NULL,
    answer_en TEXT NOT NULL,
    answer_ta TEXT NOT NULL,
    keywords TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_faq_category ON faq_entries(category);

-- 7. Follow-up & Reminder records
CREATE TABLE IF NOT EXISTS followup_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    appointment_id TEXT NOT NULL,
    reminder_type TEXT NOT NULL, -- PRE_APPOINTMENT, POST_VISIT_FEEDBACK
    scheduled_for TEXT NOT NULL, -- ISO timestamp
    message_text_en TEXT,
    message_text_ta TEXT,
    status TEXT NOT NULL DEFAULT 'PENDING', -- PENDING, SENT, CANCELLED, FAILED
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (appointment_id) REFERENCES appointments(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_followup_status ON followup_records(status);

-- 8. Human Handoff Escalation Requests
CREATE TABLE IF NOT EXISTS human_handoff_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    patient_phone TEXT,
    patient_name TEXT,
    reason TEXT NOT NULL,
    stated_concern TEXT NOT NULL,
    urgency_level TEXT NOT NULL DEFAULT 'ROUTINE', -- ROUTINE, URGENT, EMERGENCY
    handoff_destination TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'RECORDED', -- RECORDED, ATTENDED, RESOLVED
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_handoff_urgency ON human_handoff_requests(urgency_level);

-- 9. Audit Events (compliance and traceability)
CREATE TABLE IF NOT EXISTS audit_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type TEXT NOT NULL,
    entity_type TEXT,
    entity_id TEXT,
    details TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_audit_event_type ON audit_events(event_type);
"""


@dataclass
class Doctor:
    id: int
    name: str
    department: str
    qualification: str
    languages: str = "Tamil, English"
    consultation_fee: int = 500
    room_number: str = "Room 101"
    is_active: bool = True


@dataclass
class Slot:
    id: int
    doctor_id: int
    slot_date: str
    start_time: str
    end_time: str
    is_available: bool = True


@dataclass
class Patient:
    id: int
    name: str
    phone: str
    preferred_language: str = "Tamil"


@dataclass
class Appointment:
    id: str
    patient_id: int
    doctor_id: int
    slot_id: int
    appointment_date: str
    start_time: str
    end_time: str
    reason: str = ""
    status: str = "BOOKED"
    patient_name: Optional[str] = None
    patient_phone: Optional[str] = None
    doctor_name: Optional[str] = None
    department: Optional[str] = None


@dataclass
class HumanHandoffRequest:
    session_id: str
    reason: str
    stated_concern: str
    urgency_level: str = "ROUTINE"
    patient_phone: Optional[str] = None
    patient_name: Optional[str] = None
    handoff_destination: str = "+91-44-2499-1000"
    status: str = "RECORDED"
    id: Optional[int] = None
    created_at: Optional[str] = None
