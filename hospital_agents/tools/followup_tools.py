"""
Follow-up and appointment reminder tools for Google ADK agents.
"""

from __future__ import annotations

from typing import Any, Dict, List
from database.connection import create_connection, get_db_path, transaction


def get_upcoming_reminders(limit: int = 10) -> Dict[str, Any]:
    """
    Retrieve upcoming scheduled appointment reminders from the database.

    Args:
        limit: Maximum number of reminder records to retrieve (default 10).

    Returns:
        Dict with list of pending reminders, appointment IDs, scheduled times, and bilingual message texts.
    """
    conn = create_connection(get_db_path())
    try:
        cur = conn.execute(
            """
            SELECT f.id, f.appointment_id, f.reminder_type, f.scheduled_for,
                   f.message_text_en, f.message_text_ta, f.status,
                   a.appointment_date, a.start_time, p.name as patient_name, p.phone as patient_phone,
                   d.name as doctor_name
            FROM followup_records f
            JOIN appointments a ON f.appointment_id = a.id
            JOIN patients p ON a.patient_id = p.id
            JOIN doctors d ON a.doctor_id = d.id
            WHERE f.status = 'PENDING'
            ORDER BY f.scheduled_for ASC
            LIMIT ?
            """,
            (max(1, min(limit, 50)),),
        )
        rows = [dict(r) for r in cur.fetchall()]
        return {
            "success": True,
            "count": len(rows),
            "reminders": rows,
        }
    finally:
        conn.close()


def record_reminder_status(reminder_id: int, status: str) -> Dict[str, Any]:
    """
    Update the status of a reminder record.
    Supported statuses: 'SENT', 'FAILED', 'CANCELLED'.

    Args:
        reminder_id: The ID of the followup record.
        status: The new status string.

    Returns:
        Dict with update confirmation.
    """
    clean_status = status.strip().upper()
    if clean_status not in ("SENT", "FAILED", "CANCELLED", "PENDING"):
        return {"success": False, "error": f"Invalid status '{status}'."}

    conn = create_connection(get_db_path())
    try:
        with transaction(conn):
            cur = conn.execute(
                "UPDATE followup_records SET status = ? WHERE id = ?",
                (clean_status, reminder_id),
            )
            if cur.rowcount == 0:
                return {
                    "success": False,
                    "error": f"Reminder ID {reminder_id} not found.",
                }
        return {
            "success": True,
            "reminder_id": reminder_id,
            "status": clean_status,
        }
    finally:
        conn.close()
