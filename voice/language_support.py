"""
Language detection, bilingual conversation helpers, and phonetic speech formatters
for Tamil (தமிழ்), English, and Tanglish (Tamil in Latin script).
"""

from __future__ import annotations

import re
from typing import Dict, List, Tuple

# Distinctive phonetic Tamil words written in Latin script
TANGLISH_KEYWORDS = {
    "vanakkam", "vanakam", "naalaiku", "nalaiku", "inniku", "enaku", "enakku",
    "pannanum", "paakanum", "pakkanum", "venum", "kedaikuma", "irukka", "eppo",
    "enga", "romba", "vali", "kaachal", "evvalavu", "sari", "seri", "mudiyuma",
    "solreengala", "illai", "aama", "varuvaaru", "kooda", "theriyuma", "irukku",
    "panna", "paaka", "podhum", "mattum", "unga", "nalla",
}

TAMIL_MONTHS = {
    1: "ஜனவரி",
    2: "பிப்ரவரி",
    3: "மார்ச்",
    4: "ஏப்ரல்",
    5: "மே",
    6: "ஜூன்",
    7: "ஜூலை",
    8: "ஆகஸ்ட்",
    9: "செப்டம்பர்",
    10: "அக்டோபர்",
    11: "நவம்பர்",
    12: "டிசம்பர்",
}

TAMIL_NUMBERS = {
    1: "ஒன்று", 2: "இரண்டு", 3: "மூன்று", 4: "நான்கு", 5: "ஐந்து",
    6: "ஆறு", 7: "ஏழு", 8: "எட்டு", 9: "ஒன்பது", 10: "பத்து",
    11: "பதினொன்று", 12: "பன்னிரண்டு", 13: "பதிமூன்று", 14: "பதினான்கு",
    15: "பதினைந்து", 16: "பதினாறு", 17: "பதினேழு", 18: "பதினெட்டு",
    19: "பத்தொன்பது", 20: "இருபது", 21: "இருபத்தொன்று", 22: "இருபத்திரண்டு",
    23: "இருபத்து மூன்று", 24: "இருபத்து நான்கு", 25: "இருபத்தைந்து",
    26: "இருபத்தாறு", 27: "இருபத்தேழு", 28: "இருபத்தெட்டு", 29: "இருபத்தொன்பது",
    30: "முப்பது", 31: "முப்பத்தொன்று",
}


def detect_language(text: str) -> str:
    """
    Detects whether the input text is in Tamil script, Tanglish, or English.
    Returns: 'ta' (Tamil script), 'tanglish' (Tamil in Latin), or 'en' (English).
    """
    if not text or not text.strip():
        return "en"

    # 1. Check for Tamil Unicode characters (\u0B80 to \u0BFF)
    tamil_chars = len(re.findall(r"[\u0B80-\u0BFF]", text))
    if tamil_chars > 2:
        return "ta"

    # 2. Check for distinct phonetic Tamil words written in Latin script
    words = set(re.findall(r"[a-zA-Z]+", text.lower()))
    if any(w in TANGLISH_KEYWORDS for w in words):
        return "tanglish"

    return "en"


def format_date_for_speech(date_str: str, language: str = "en") -> str:
    """
    Format a YYYY-MM-DD date into natural spoken language.
    Avoids robotic "two zero two six dash ten dash two three".
    """
    try:
        parts = date_str.split("-")
        year = int(parts[0])
        month = int(parts[1])
        day = int(parts[2])

        if language == "ta" or language == "tanglish":
            month_name = TAMIL_MONTHS.get(month, str(month))
            day_spoken = TAMIL_NUMBERS.get(day, str(day))
            return f"{month_name} {day_spoken}-ஆம் தேதி"
        else:
            # English spoken date
            suffixes = {1: "st", 2: "nd", 3: "rd", 21: "st", 22: "nd", 23: "rd", 31: "st"}
            suffix = suffixes.get(day, "th")
            month_names_en = [
                "", "January", "February", "March", "April", "May", "June",
                "July", "August", "September", "October", "November", "December",
            ]
            return f"{month_names_en[month]} {day}{suffix}, {year}"
    except Exception:
        return date_str


def format_time_for_speech(time_str: str, language: str = "en") -> str:
    """
    Format HH:MM time into spoken conversational speech.
    """
    try:
        hour, minute = map(int, time_str.split(":"))
        is_pm = hour >= 12
        disp_hour = hour if hour <= 12 else hour - 12
        if disp_hour == 0:
            disp_hour = 12

        period_en = "PM" if is_pm else "AM"
        period_ta = "மாலை" if hour >= 16 else ("மதியம்" if hour >= 12 else "காலை")

        if language in ("ta", "tanglish"):
            min_str = f" {minute} நிமிடம்" if minute > 0 else ""
            if minute == 30:
                min_str = " அரை"
            return f"{period_ta} {disp_hour}{min_str} மணி"
        else:
            min_str = f":{minute:02d}" if minute > 0 else ""
            return f"{disp_hour}{min_str} {period_en}"
    except Exception:
        return time_str


def format_appointment_id_for_speech(apt_id: str) -> str:
    """
    Format appointment ID for phonetic speech synthesis (separates letters and digits).
    E.g. 'APT-20261023-A1B2' -> 'A P T, 2 0 2 6 1 0 2 3, A 1 B 2'.
    """
    if not apt_id:
        return ""
    parts = apt_id.split("-")
    spoken_parts = []
    for part in parts:
        spoken_parts.append(" ".join(list(part)))
    return ", ".join(spoken_parts)


# Conversational acknowledgments
NATURAL_FILLERS = {
    "ta": ["சரிங்க.", "கண்டிப்பா பார்க்கிறேன்.", "ஒரு நிமிடம் பொறுங்க.", "சரி."],
    "en": ["Sure.", "Let me check that right away.", "Certainly.", "One moment please."],
    "tanglish": ["Seri, kandippa check panren.", "Oru nimisham hold pannunga."],
}
