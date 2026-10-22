"""
Seed data generator with realistic synthetic demo doctors, slots, and FAQ content.
Uses synthetic data only (no real patient identifiers).
"""

from __future__ import annotations

import datetime
import logging
from pathlib import Path
from typing import Optional, Union

from database.connection import create_connection, get_db_path, transaction
from database.initialization import init_db

logger = logging.getLogger(__name__)

DEMO_DOCTORS = [
    {
        "name": "Dr. Priya Raman",
        "department": "General Medicine",
        "qualification": "MBBS, MD (General Medicine)",
        "languages": "Tamil, English",
        "consultation_fee": 500,
        "room_number": "Room 101",
    },
    {
        "name": "Dr. Rajesh Kumar",
        "department": "General Medicine",
        "qualification": "MBBS, DNB (Internal Medicine)",
        "languages": "Tamil, English, Hindi",
        "consultation_fee": 500,
        "room_number": "Room 102",
    },
    {
        "name": "Dr. Ananya Sundaram",
        "department": "Cardiology",
        "qualification": "MBBS, MD, DM (Cardiology)",
        "languages": "Tamil, English",
        "consultation_fee": 800,
        "room_number": "Room 205 (Cardio Clinic)",
    },
    {
        "name": "Dr. Karthik Subramanian",
        "department": "Pediatrics",
        "qualification": "MBBS, MD (Pediatrics), DCH",
        "languages": "Tamil, English",
        "consultation_fee": 600,
        "room_number": "Room 108 (Child Health)",
    },
    {
        "name": "Dr. Meenakshi Venkat",
        "department": "Orthopedics",
        "qualification": "MBBS, MS (Orthopedics)",
        "languages": "Tamil, English",
        "consultation_fee": 700,
        "room_number": "Room 304",
    },
    {
        "name": "Dr. Suresh Balaji",
        "department": "ENT",
        "qualification": "MBBS, MS (ENT)",
        "languages": "Tamil, English",
        "consultation_fee": 550,
        "room_number": "Room 112",
    },
    {
        "name": "Dr. Kavitha Natarajan",
        "department": "Gynecology & Obstetrics",
        "qualification": "MBBS, DGO, MS (OG)",
        "languages": "Tamil, English",
        "consultation_fee": 700,
        "room_number": "Room 210",
    },
]

DEMO_FAQS = [
    {
        "category": "address",
        "question_en": "Where is the hospital located and what is the address?",
        "question_ta": "மருத்துவமனை எங்கு அமைந்துள்ளது, முகவரி என்ன?",
        "answer_en": "Kaveri Multispeciality Hospital is located at No. 45, Anna Salai, Teynampet, Chennai 600018, opposite the Teynampet Signal, near SIET College.",
        "answer_ta": "காவேரி பல்நோக்கு மருத்துவமனை எண் 45, அண்ணா சாலை, தேனாம்பேட்டை, சென்னை 600018-ல் அமைந்துள்ளது (தேனாம்பேட்டை சிக்னல் எதிரில், SIET கல்லூரி அருகில்).",
        "keywords": "address location where route landmark chennai teynampet முகவரி இடம் எங்கு அண்ணா சாலை தேனாம்பேட்டை",
    },
    {
        "category": "timings",
        "question_en": "What are the hospital outpatient (OPD) and emergency timings?",
        "question_ta": "OPD ஆலோசனை மற்றும் அவசர சிகிச்சை நேரங்கள் என்ன?",
        "answer_en": "Outpatient (OPD) consultations run Monday to Saturday from 8:00 AM to 8:00 PM, and Sunday 9:00 AM to 1:00 PM. Emergency services and in-house pharmacy operate 24 hours a day, 7 days a week.",
        "answer_ta": "OPD ஆலோசனை திங்கள் முதல் சனி வரை காலை 8:00 மணி முதல் இரவு 8:00 மணி வரையிலும், ஞாயிற்றுக்கிழமை காலை 9:00 முதல் மதியம் 1:00 வரையிலும் செயல்படுகிறது. அவசர சிகிச்சை பிரிவு (Emergency) மற்றும் மருந்தகம் 24 மணி நேரமும் செயல்படுகிறது.",
        "keywords": "timing hours open opd emergency sunday timings நேரம் எப்போது திறந்திருக்கும் அவசர சிகிச்சை ஞாயிறு",
    },
    {
        "category": "contacts",
        "question_en": "What are the contact numbers for reception and emergency?",
        "question_ta": "வரவேற்பறை மற்றும் அவசர சிகிச்சை தொடர்பு எண்கள் என்ன?",
        "answer_en": "You can reach Reception at +91-44-2499-1000, Appointment Desk at +91-44-2499-1001, Emergency Care at +91-44-2499-1066, and Ambulance at 108.",
        "answer_ta": "வரவேற்பறை எண்: +91-44-2499-1000, முன்பதிவு எண்: +91-44-2499-1001, அவசர சிகிச்சை எண்: +91-44-2499-1066, ஆம்புலன்ஸ்: 108.",
        "keywords": "contact phone number emergency telephone reception call தொடர்பு தொலைபேசி போன் எண் அவசர எண்",
    },
    {
        "category": "payments",
        "question_en": "What payment methods and health insurances are accepted?",
        "question_ta": "எந்தெந்த கட்டண முறைகள் மற்றும் காப்பீடுகள் (Insurance) ஏற்றுக்கொள்ளப்படுகின்றன?",
        "answer_en": "We accept Cash, UPI (GPay, PhonePe), Debit/Credit cards, major private health insurances (Star Health, ICICI Lombard, HDFC ERGO), and the Tamil Nadu CMCHIS government insurance scheme.",
        "answer_ta": "ரொக்கம், UPI (GPay, PhonePe), டெபிட்/கிரெடிட் கார்டுகள், முன்னணி தனியார் காப்பீடுகள் (Star Health, ICICI, HDFC ERGO) மற்றும் தமிழ்நாடு முதலமைச்சரின் விரிவான மருத்துவக் காப்பீட்டுத் திட்டம் (CMCHIS) ஏற்றுக்கொள்ளப்படுகின்றன.",
        "keywords": "payment fees cost insurance cmchis card upi gpay கட்டணம் காப்பீடு இன்சூரன்ஸ் கார்டு கூகுள்பே",
    },
    {
        "category": "preparation",
        "question_en": "What preparation is needed for fasting blood tests or ultrasound?",
        "question_ta": "இரத்தப் பரிசோதனை அல்லது அல்ட்ராசவுண்ட் ஸ்கேன் செய்ய என்ன முன்னெச்சரிக்கை தேவை?",
        "answer_en": "Fasting blood tests (glucose, lipid profile) require 8 to 12 hours of overnight fasting (water is allowed). Abdominal ultrasound requires 6 hours of fasting and drinking 3-4 glasses of water 1 hour prior for a full bladder.",
        "answer_ta": "இரத்தப் பரிசோதனைக்கு 8 முதல் 12 மணி நேரம் சாப்பிடாமல் இருக்க வேண்டும் (தண்ணீர் குடிக்கலாம்). வயிற்றுப்பகுதி அல்ட்ராசவுண்ட் ஸ்கேன் செய்ய 6 மணி நேரம் சாப்பிடாமல் இருக்க வேண்டும் மற்றும் ஸ்கேன் செய்வதற்கு ஒரு மணி நேரம் முன் 3-4 டம்ளர் தண்ணீர் குடிக்க வேண்டும்.",
        "keywords": "preparation fasting blood test ultrasound scan test instructions பரிசோதனை ரத்த டெஸ்ட் வெறும் வயிறு ஸ்கேன்",
    },
    {
        "category": "departments",
        "question_en": "What departments and specialties are available at the hospital?",
        "question_ta": "மருத்துவமனையில் உள்ள சிறப்பு மருத்துவத் துறைகள் யாவை?",
        "answer_en": "We offer General Medicine, Cardiology, Pediatrics, Orthopedics, ENT (Ear Nose Throat), Gynecology & Obstetrics, and a 24x7 Emergency and Trauma department.",
        "answer_ta": "பொது மருத்துவம், இதயவியல், குழந்தைகள் நலம், எலும்பு மூட்டு சிகிச்சை, காது-மூக்கு-தொண்டை (ENT), மகப்பேறு-மகளிர் நலம் மற்றும் 24 மணி நேர அவசர சிகிச்சைப் பிரிவு ஆகியவை செயல்படுகின்றன.",
        "keywords": "departments specialties doctors list services துறைகள் மருத்துவர்கள் பிரிவுகள் என்ன டாக்டர்",
    },
]


def seed_database(
    db_path: Optional[Union[str, Path]] = None, days_ahead: int = 7
) -> None:
    """
    Populates the database with demo doctors, slots, and FAQ entries.
    Safe to run repeatedly; inserts only missing records.
    """
    target_path = init_db(db_path)
    conn = create_connection(target_path)

    try:
        with transaction(conn):
            # 1. Seed Doctors
            doctor_ids = {}
            for doc in DEMO_DOCTORS:
                cur = conn.execute(
                    """
                    SELECT id FROM doctors WHERE name = ? AND department = ?
                    """,
                    (doc["name"], doc["department"]),
                )
                row = cur.fetchone()
                if row:
                    doctor_ids[doc["name"]] = row["id"]
                else:
                    cur = conn.execute(
                        """
                        INSERT INTO doctors (name, department, qualification, languages, consultation_fee, room_number, is_active)
                        VALUES (?, ?, ?, ?, ?, ?, 1)
                        """,
                        (
                            doc["name"],
                            doc["department"],
                            doc["qualification"],
                            doc["languages"],
                            doc["consultation_fee"],
                            doc["room_number"],
                        ),
                    )
                    doctor_ids[doc["name"]] = cur.lastrowid

            # 2. Seed Doctor Schedules
            days_of_week = [
                "Monday",
                "Tuesday",
                "Wednesday",
                "Thursday",
                "Friday",
                "Saturday",
            ]
            for doc_name, doc_id in doctor_ids.items():
                for day in days_of_week:
                    conn.execute(
                        """
                        INSERT OR IGNORE INTO doctor_schedules (doctor_id, day_of_week, start_time, end_time, slot_duration_minutes)
                        VALUES (?, ?, '09:00', '13:00', 30)
                        """,
                        (doc_id, day),
                    )
                    conn.execute(
                        """
                        INSERT OR IGNORE INTO doctor_schedules (doctor_id, day_of_week, start_time, end_time, slot_duration_minutes)
                        VALUES (?, ?, '16:00', '19:00', 30)
                        """,
                        (doc_id, day),
                    )

            # 3. Seed Slots for today and the next N days
            today = datetime.date.today()
            standard_slots = [
                ("09:00", "09:30"),
                ("09:30", "10:00"),
                ("10:00", "10:30"),
                ("10:30", "11:00"),
                ("11:00", "11:30"),
                ("11:30", "12:00"),
                ("12:00", "12:30"),
                ("16:00", "16:30"),
                ("16:30", "17:00"),
                ("17:00", "17:30"),
                ("17:30", "18:00"),
                ("18:00", "18:30"),
            ]

            for offset in range(days_ahead + 1):
                target_date = (today + datetime.timedelta(days=offset)).isoformat()
                # Skip Sunday slots for routine doctor schedules (except emergency)
                day_num = (today + datetime.timedelta(days=offset)).weekday()
                if day_num == 6:  # Sunday
                    continue

                for doc_name, doc_id in doctor_ids.items():
                    for start_t, end_t in standard_slots:
                        conn.execute(
                            """
                            INSERT OR IGNORE INTO slots (doctor_id, slot_date, start_time, end_time, is_available)
                            VALUES (?, ?, ?, ?, 1)
                            """,
                            (doc_id, target_date, start_t, end_t),
                        )

            # 4. Seed FAQ Entries
            for faq in DEMO_FAQS:
                cur = conn.execute(
                    "SELECT id FROM faq_entries WHERE category = ?", (faq["category"],)
                )
                if not cur.fetchone():
                    conn.execute(
                        """
                        INSERT INTO faq_entries (category, question_en, question_ta, answer_en, answer_ta, keywords)
                        VALUES (?, ?, ?, ?, ?, ?)
                        """,
                        (
                            faq["category"],
                            faq["question_en"],
                            faq["question_ta"],
                            faq["answer_en"],
                            faq["answer_ta"],
                            faq["keywords"],
                        ),
                    )

            # 5. Seed one synthetic demo patient & appointment for verification testing
            cur = conn.execute(
                "SELECT id FROM patients WHERE phone = '+919876543210'"
            )
            demo_patient_row = cur.fetchone()
            if not demo_patient_row:
                cur = conn.execute(
                    """
                    INSERT INTO patients (name, phone, preferred_language)
                    VALUES ('Karthik Muthu (Demo)', '+919876543210', 'Tamil')
                    """
                )
                demo_patient_id = cur.lastrowid
            else:
                demo_patient_id = demo_patient_row["id"]

            # Book a demo slot for tomorrow
            tomorrow = (today + datetime.timedelta(days=1)).isoformat()
            demo_doc_id = doctor_ids.get("Dr. Priya Raman", 1)
            slot_cur = conn.execute(
                """
                SELECT id FROM slots
                WHERE doctor_id = ? AND slot_date = ? AND start_time = '09:00' AND is_available = 1
                """,
                (demo_doc_id, tomorrow),
            )
            slot_row = slot_cur.fetchone()
            if slot_row:
                slot_id = slot_row["id"]
                demo_apt_id = "APT-DEMO-20261023-0001"
                conn.execute(
                    """
                    INSERT OR IGNORE INTO appointments (id, patient_id, doctor_id, slot_id, appointment_date, start_time, end_time, reason, status)
                    VALUES (?, ?, ?, ?, ?, '09:00', '09:30', 'Routine Health Checkup', 'BOOKED')
                    """,
                    (demo_apt_id, demo_patient_id, demo_doc_id, slot_id, tomorrow),
                )
                conn.execute(
                    "UPDATE slots SET is_available = 0 WHERE id = ?", (slot_id,)
                )

        logger.info("Successfully seeded database with doctors, schedules, slots, and FAQs.")
    finally:
        conn.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    seed_database()
