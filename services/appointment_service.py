"""
Appointment management service handling doctor lookup, slot availability,
atomic booking, rescheduling, and cancellation with transaction safety.
"""

from __future__ import annotations

import datetime
import logging
import secrets
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from database.connection import create_connection, get_db_path, transaction

logger = logging.getLogger(__name__)


def generate_appointment_id(date_str: str) -> str:
    """Generate a unique human-friendly appointment ID, e.g. APT-20261023-7F3A."""
    clean_date = date_str.replace("-", "")
    suffix = secrets.token_hex(2).upper()
    return f"APT-{clean_date}-{suffix}"


class AppointmentService:
    def __init__(self, db_path: Optional[Union[str, Path]] = None) -> None:
        self.db_path = get_db_path(db_path)

    def list_doctors(self, department: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List active doctors, optionally filtered by medical department or specialty.
        Returns empty list if department is not found.
        """
        conn = create_connection(self.db_path)
        try:
            if department and department.strip():
                dept_query = f"%{department.strip()}%"
                cur = conn.execute(
                    """
                    SELECT id, name, department, qualification, languages, consultation_fee, room_number
                    FROM doctors
                    WHERE is_active = 1 AND (department LIKE ? OR name LIKE ?)
                    ORDER BY id ASC
                    """,
                    (dept_query, dept_query),
                )
            else:
                cur = conn.execute(
                    """
                    SELECT id, name, department, qualification, languages, consultation_fee, room_number
                    FROM doctors
                    WHERE is_active = 1
                    ORDER BY department ASC, name ASC
                    """
                )
            rows = cur.fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def get_doctor_by_id(self, doctor_id: int) -> Optional[Dict[str, Any]]:
        """Retrieve doctor details by primary key."""
        conn = create_connection(self.db_path)
        try:
            cur = conn.execute(
                """
                SELECT id, name, department, qualification, languages, consultation_fee, room_number
                FROM doctors WHERE id = ? AND is_active = 1
                """,
                (doctor_id,),
            )
            row = cur.fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def get_available_slots(
        self, doctor_id: int, date_str: str
    ) -> Dict[str, Any]:
        """
        Check actual database slot availability for a doctor on a given date (YYYY-MM-DD).
        Never returns fabricated slots.
        """
        # Validate date format
        try:
            parsed_date = datetime.date.fromisoformat(date_str.strip())
        except ValueError:
            return {
                "success": False,
                "error": f"Invalid date format '{date_str}'. Please use YYYY-MM-DD.",
                "slots": [],
            }

        # Check doctor exists
        doctor = self.get_doctor_by_id(doctor_id)
        if not doctor:
            return {
                "success": False,
                "error": f"Doctor ID {doctor_id} not found or inactive.",
                "slots": [],
            }

        conn = create_connection(self.db_path)
        try:
            cur = conn.execute(
                """
                SELECT id as slot_id, start_time, end_time, is_available
                FROM slots
                WHERE doctor_id = ? AND slot_date = ? AND is_available = 1
                ORDER BY start_time ASC
                """,
                (doctor_id, parsed_date.isoformat()),
            )
            rows = cur.fetchall()
            available = [
                {
                    "slot_id": r["slot_id"],
                    "start_time": r["start_time"],
                    "end_time": r["end_time"],
                }
                for r in rows
            ]

            return {
                "success": True,
                "doctor_id": doctor_id,
                "doctor_name": doctor["name"],
                "department": doctor["department"],
                "date": parsed_date.isoformat(),
                "available_slots_count": len(available),
                "slots": available,
            }
        finally:
            conn.close()

    def book_appointment(
        self,
        patient_name: str,
        patient_phone: str,
        doctor_id: int,
        date_str: str,
        start_time: str,
        reason: str = "",
        preferred_language: str = "Tamil",
    ) -> Dict[str, Any]:
        """
        Atomically books an appointment.
        Prevents double-booking via database transactions and uniqueness constraints.
        Returns genuine booking status with appointment ID.
        """
        # Validate patient inputs
        clean_name = patient_name.strip()
        clean_phone = patient_phone.strip()
        clean_time = start_time.strip()
        clean_date = date_str.strip()

        if not clean_name or len(clean_name) < 2:
            return {"success": False, "error": "Valid patient name is required."}

        if not clean_phone or len(clean_phone) < 8:
            return {
                "success": False,
                "error": "Valid patient contact phone number is required.",
            }

        try:
            parsed_date = datetime.date.fromisoformat(clean_date)
        except ValueError:
            return {
                "success": False,
                "error": f"Invalid date '{clean_date}'. Use YYYY-MM-DD format.",
            }

        conn = create_connection(self.db_path)
        try:
            with transaction(conn):
                # 1. Verify doctor
                doc_cur = conn.execute(
                    "SELECT id, name, department, consultation_fee, room_number FROM doctors WHERE id = ? AND is_active = 1",
                    (doctor_id,),
                )
                doc_row = doc_cur.fetchone()
                if not doc_row:
                    return {
                        "success": False,
                        "error": f"Doctor ID {doctor_id} does not exist or is inactive.",
                    }

                # 2. Check and lock slot
                slot_cur = conn.execute(
                    """
                    SELECT id, start_time, end_time, is_available
                    FROM slots
                    WHERE doctor_id = ? AND slot_date = ? AND start_time = ?
                    """,
                    (doctor_id, parsed_date.isoformat(), clean_time),
                )
                slot_row = slot_cur.fetchone()

                if not slot_row:
                    # Slot doesn't exist on schedule
                    # Fetch genuinely available alternative slots
                    alt_cur = conn.execute(
                        """
                        SELECT start_time FROM slots
                        WHERE doctor_id = ? AND slot_date = ? AND is_available = 1
                        ORDER BY start_time ASC LIMIT 4
                        """,
                        (doctor_id, parsed_date.isoformat()),
                    )
                    alternatives = [r["start_time"] for r in alt_cur.fetchall()]
                    return {
                        "success": False,
                        "error": f"Slot {clean_time} on {parsed_date.isoformat()} does not exist on schedule.",
                        "available_alternatives": alternatives,
                    }

                if not slot_row["is_available"]:
                    # Already booked
                    alt_cur = conn.execute(
                        """
                        SELECT start_time FROM slots
                        WHERE doctor_id = ? AND slot_date = ? AND is_available = 1
                        ORDER BY start_time ASC LIMIT 4
                        """,
                        (doctor_id, parsed_date.isoformat()),
                    )
                    alternatives = [r["start_time"] for r in alt_cur.fetchall()]
                    return {
                        "success": False,
                        "error": f"The slot at {clean_time} on {parsed_date.isoformat()} is already booked.",
                        "available_alternatives": alternatives,
                    }

                slot_id = slot_row["id"]
                end_time = slot_row["end_time"]

                # 3. Upsert patient
                pat_cur = conn.execute(
                    "SELECT id FROM patients WHERE phone = ?", (clean_phone,)
                )
                pat_row = pat_cur.fetchone()
                if pat_row:
                    patient_id = pat_row["id"]
                    conn.execute(
                        "UPDATE patients SET name = ?, preferred_language = ? WHERE id = ?",
                        (clean_name, preferred_language, patient_id),
                    )
                else:
                    pat_ins = conn.execute(
                        "INSERT INTO patients (name, phone, preferred_language) VALUES (?, ?, ?)",
                        (clean_name, clean_phone, preferred_language),
                    )
                    patient_id = pat_ins.lastrowid

                # 4. Generate unique appointment ID
                appointment_id = generate_appointment_id(parsed_date.isoformat())

                # 5. Insert appointment
                conn.execute(
                    """
                    INSERT INTO appointments
                    (id, patient_id, doctor_id, slot_id, appointment_date, start_time, end_time, reason, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'BOOKED')
                    """,
                    (
                        appointment_id,
                        patient_id,
                        doctor_id,
                        slot_id,
                        parsed_date.isoformat(),
                        clean_time,
                        end_time,
                        reason,
                    ),
                )

                # 6. Mark slot unavailable
                conn.execute(
                    "UPDATE slots SET is_available = 0 WHERE id = ?", (slot_id,)
                )

                # 7. Audit log
                conn.execute(
                    """
                    INSERT INTO audit_events (event_type, entity_type, entity_id, details)
                    VALUES ('BOOK_APPOINTMENT', 'appointment', ?, ?)
                    """,
                    (
                        appointment_id,
                        f"Booked for {clean_name} ({clean_phone}) with {doc_row['name']} at {clean_time} on {parsed_date.isoformat()}",
                    ),
                )

                # 8. Create scheduled reminder
                reminder_time = (
                    datetime.datetime.combine(
                        parsed_date,
                        datetime.time.fromisoformat(clean_time),
                    )
                    - datetime.timedelta(hours=2)
                ).isoformat()

                msg_en = (
                    f"Reminder: You have an appointment with {doc_row['name']} ({doc_row['department']}) "
                    f"today at {clean_time} at Kaveri Hospital, {doc_row['room_number']}. ID: {appointment_id}."
                )
                msg_ta = (
                    f"நினைவூட்டல்: இன்று {clean_time} மணிக்கு காவேரி மருத்துவமனையில் {doc_row['name']} "
                    f"அவர்களுடன் தங்களுக்கு அப்பாயின்மென்ட் உள்ளது ({doc_row['room_number']}). எண்: {appointment_id}."
                )

                conn.execute(
                    """
                    INSERT INTO followup_records (appointment_id, reminder_type, scheduled_for, message_text_en, message_text_ta, status)
                    VALUES (?, 'PRE_APPOINTMENT', ?, ?, ?, 'PENDING')
                    """,
                    (appointment_id, reminder_time, msg_en, msg_ta),
                )

            return {
                "success": True,
                "appointment_id": appointment_id,
                "patient_name": clean_name,
                "patient_phone": clean_phone,
                "doctor_name": doc_row["name"],
                "department": doc_row["department"],
                "room_number": doc_row["room_number"],
                "consultation_fee": doc_row["consultation_fee"],
                "date": parsed_date.isoformat(),
                "time": clean_time,
                "status": "BOOKED",
                "confirmation_message_en": (
                    f"Appointment confirmed! ID: {appointment_id}. Doctor: {doc_row['name']}, "
                    f"Date: {parsed_date.isoformat()} at {clean_time}, Room: {doc_row['room_number']}."
                ),
                "confirmation_message_ta": (
                    f"முன்பதிவு உறுதியானது! பதிவு எண்: {appointment_id}. மருத்துவர்: {doc_row['name']}, "
                    f"நாள்: {parsed_date.isoformat()} நேரம்: {clean_time}, அறை: {doc_row['room_number']}."
                ),
            }
        finally:
            conn.close()

    def get_appointment(
        self, appointment_id: str, patient_phone: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Retrieve appointment details.
        Verifies patient phone number if provided to protect patient privacy.
        """
        clean_id = appointment_id.strip()
        conn = create_connection(self.db_path)
        try:
            cur = conn.execute(
                """
                SELECT a.id, a.appointment_date, a.start_time, a.end_time, a.reason, a.status,
                       p.name as patient_name, p.phone as patient_phone,
                       d.name as doctor_name, d.department, d.room_number, d.consultation_fee
                FROM appointments a
                JOIN patients p ON a.patient_id = p.id
                JOIN doctors d ON a.doctor_id = d.id
                WHERE a.id = ?
                """,
                (clean_id,),
            )
            row = cur.fetchone()
            if not row:
                return {
                    "success": False,
                    "error": f"Appointment with ID '{clean_id}' was not found.",
                }

            apt_data = dict(row)

            # Privacy protection: if patient_phone provided, verify last 4 digits or exact match
            if patient_phone and patient_phone.strip():
                clean_phone = patient_phone.strip()
                stored_phone = apt_data["patient_phone"]
                if not (
                    clean_phone == stored_phone
                    or stored_phone.endswith(clean_phone[-4:])
                ):
                    return {
                        "success": False,
                        "error": "Security verification failed: Phone number does not match appointment record.",
                    }

            return {"success": True, "appointment": apt_data}
        finally:
            conn.close()

    def reschedule_appointment(
        self,
        appointment_id: str,
        new_date: str,
        new_start_time: str,
        patient_phone: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Atomically reschedules an appointment to a new date and time slot.
        Frees old slot and books new slot within a single transaction.
        """
        clean_id = appointment_id.strip()
        clean_date = new_date.strip()
        clean_time = new_start_time.strip()

        try:
            parsed_new_date = datetime.date.fromisoformat(clean_date)
        except ValueError:
            return {
                "success": False,
                "error": f"Invalid date '{clean_date}'. Format must be YYYY-MM-DD.",
            }

        conn = create_connection(self.db_path)
        try:
            with transaction(conn):
                # 1. Fetch current appointment
                cur = conn.execute(
                    """
                    SELECT a.id, a.doctor_id, a.slot_id, a.appointment_date, a.start_time, a.status,
                           p.phone as patient_phone, p.name as patient_name, d.name as doctor_name, d.room_number
                    FROM appointments a
                    JOIN patients p ON a.patient_id = p.id
                    JOIN doctors d ON a.doctor_id = d.id
                    WHERE a.id = ?
                    """,
                    (clean_id,),
                )
                apt = cur.fetchone()
                if not apt:
                    return {
                        "success": False,
                        "error": f"Appointment '{clean_id}' not found.",
                    }

                if apt["status"] == "CANCELLED":
                    return {
                        "success": False,
                        "error": f"Appointment '{clean_id}' was previously cancelled and cannot be rescheduled.",
                    }

                # Privacy check
                if patient_phone and patient_phone.strip():
                    if not (
                        patient_phone.strip() == apt["patient_phone"]
                        or apt["patient_phone"].endswith(patient_phone.strip()[-4:])
                    ):
                        return {
                            "success": False,
                            "error": "Phone number does not match the appointment record.",
                        }

                doctor_id = apt["doctor_id"]
                old_slot_id = apt["slot_id"]

                # 2. Check and lock new slot
                slot_cur = conn.execute(
                    """
                    SELECT id, end_time, is_available
                    FROM slots
                    WHERE doctor_id = ? AND slot_date = ? AND start_time = ?
                    """,
                    (doctor_id, parsed_new_date.isoformat(), clean_time),
                )
                new_slot = slot_cur.fetchone()

                if not new_slot or not new_slot["is_available"]:
                    # Fetch alternatives
                    alt_cur = conn.execute(
                        """
                        SELECT start_time FROM slots
                        WHERE doctor_id = ? AND slot_date = ? AND is_available = 1
                        ORDER BY start_time ASC LIMIT 4
                        """,
                        (doctor_id, parsed_new_date.isoformat()),
                    )
                    alternatives = [r["start_time"] for r in alt_cur.fetchall()]
                    return {
                        "success": False,
                        "error": f"Slot at {clean_time} on {parsed_new_date.isoformat()} is not available.",
                        "available_alternatives": alternatives,
                    }

                new_slot_id = new_slot["id"]
                new_end_time = new_slot["end_time"]

                # 3. Free old slot
                conn.execute(
                    "UPDATE slots SET is_available = 1 WHERE id = ?", (old_slot_id,)
                )

                # 4. Claim new slot
                conn.execute(
                    "UPDATE slots SET is_available = 0 WHERE id = ?", (new_slot_id,)
                )

                # 5. Update appointment
                conn.execute(
                    """
                    UPDATE appointments
                    SET slot_id = ?, appointment_date = ?, start_time = ?, end_time = ?,
                        status = 'RESCHEDULED', updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                    """,
                    (
                        new_slot_id,
                        parsed_new_date.isoformat(),
                        clean_time,
                        new_end_time,
                        clean_id,
                    ),
                )

                # 6. Audit
                conn.execute(
                    """
                    INSERT INTO audit_events (event_type, entity_type, entity_id, details)
                    VALUES ('RESCHEDULE_APPOINTMENT', 'appointment', ?, ?)
                    """,
                    (
                        clean_id,
                        f"Rescheduled from {apt['appointment_date']} {apt['start_time']} to {parsed_new_date.isoformat()} {clean_time}",
                    ),
                )

            return {
                "success": True,
                "appointment_id": clean_id,
                "patient_name": apt["patient_name"],
                "doctor_name": apt["doctor_name"],
                "room_number": apt["room_number"],
                "new_date": parsed_new_date.isoformat(),
                "new_time": clean_time,
                "status": "RESCHEDULED",
                "message_en": f"Appointment {clean_id} successfully rescheduled to {parsed_new_date.isoformat()} at {clean_time}.",
                "message_ta": f"அப்பாயின்மென்ட் {clean_id} வெற்றிகரமாக {parsed_new_date.isoformat()} அன்று {clean_time} மணிக்கு மாற்றப்பட்டது.",
            }
        finally:
            conn.close()

    def cancel_appointment(
        self,
        appointment_id: str,
        patient_phone: Optional[str] = None,
        reason: str = "",
    ) -> Dict[str, Any]:
        """
        Atomically cancels an appointment and frees the associated time slot.
        """
        clean_id = appointment_id.strip()
        conn = create_connection(self.db_path)
        try:
            with transaction(conn):
                cur = conn.execute(
                    """
                    SELECT a.id, a.slot_id, a.status, a.appointment_date, a.start_time,
                           p.phone as patient_phone, p.name as patient_name, d.name as doctor_name
                    FROM appointments a
                    JOIN patients p ON a.patient_id = p.id
                    JOIN doctors d ON a.doctor_id = d.id
                    WHERE a.id = ?
                    """,
                    (clean_id,),
                )
                apt = cur.fetchone()
                if not apt:
                    return {
                        "success": False,
                        "error": f"Appointment '{clean_id}' was not found.",
                    }

                if apt["status"] == "CANCELLED":
                    return {
                        "success": False,
                        "error": f"Appointment '{clean_id}' is already cancelled.",
                    }

                # Privacy check
                if patient_phone and patient_phone.strip():
                    if not (
                        patient_phone.strip() == apt["patient_phone"]
                        or apt["patient_phone"].endswith(patient_phone.strip()[-4:])
                    ):
                        return {
                            "success": False,
                            "error": "Phone number does not match appointment record.",
                        }

                slot_id = apt["slot_id"]

                # 1. Free the slot
                conn.execute(
                    "UPDATE slots SET is_available = 1 WHERE id = ?", (slot_id,)
                )

                # 2. Update appointment status and release slot reference
                conn.execute(
                    """
                    UPDATE appointments
                    SET status = 'CANCELLED', slot_id = NULL,
                        reason = CASE WHEN ? != '' THEN ? ELSE reason END,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                    """,
                    (reason, reason, clean_id),
                )

                # 3. Cancel any pending reminders
                conn.execute(
                    "UPDATE followup_records SET status = 'CANCELLED' WHERE appointment_id = ?",
                    (clean_id,),
                )

                # 4. Audit
                conn.execute(
                    """
                    INSERT INTO audit_events (event_type, entity_type, entity_id, details)
                    VALUES ('CANCEL_APPOINTMENT', 'appointment', ?, ?)
                    """,
                    (clean_id, f"Cancelled. Reason: {reason or 'Patient request'}"),
                )

            return {
                "success": True,
                "appointment_id": clean_id,
                "patient_name": apt["patient_name"],
                "doctor_name": apt["doctor_name"],
                "date": apt["appointment_date"],
                "time": apt["start_time"],
                "status": "CANCELLED",
                "message_en": f"Appointment {clean_id} has been cancelled. The slot has been released.",
                "message_ta": f"அப்பாயின்மென்ட் {clean_id} வெற்றிகரமாக ரத்து செய்யப்பட்டது.",
            }
        finally:
            conn.close()
