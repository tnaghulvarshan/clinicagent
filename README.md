# Multilingual Hospital Receptionist AI System
### Built with Google Agent Development Kit (ADK), Gemini API, Python, and LiveKit Agents

An intelligent, modular, voice-enabled **Multi-Agent Hospital Receptionist System** designed for healthcare clinics and hospitals. The system communicates fluently with patients in **Tamil (தமிழ்)**, **English**, and **Tanglish** (Tamil-English conversational speech), checking actual availability in an SQLite database, safely routing medical inquiries, executing real appointments, and offering human receptionist or emergency escalation.

---

## 1. System Architecture

The architecture separates conversational voice streaming, agent reasoning, and transactional business logic:

```
                                  [ Patient Caller ]
                                          │
                     ┌────────────────────┴────────────────────┐
                     │                                         │
               (Voice / SIP)                             (Text / Web UI)
                     │                                         │
                     ▼                                         ▼
         ┌───────────────────────┐                 ┌───────────────────────┐
         │  LiveKit Voice Agent  │                 │    Google ADK Web     │
         │  (Realtime Audio I/O) │                 │      (FastAPI)        │
         └───────────┬───────────┘                 └───────────┬───────────┘
                     │                                         │
                     ▼                                         │
         ┌───────────────────────┐                             │
         │    ADK Voice Bridge   │                             │
         │   (Language & Tools)  │                             │
         └───────────┬───────────┘                             │
                     │                                         │
                     └────────────────────┬────────────────────┘
                                          │
                                          ▼
                      ┌───────────────────────────────────────┐
                      │    Hospital Receptionist Root Agent   │
                      │             (Google ADK)              │
                      └───────────────────┬───────────────────┘
                                          │ Delegations
         ┌──────────────────┬─────────────┼─────────────┬──────────────────┐
         ▼                  ▼             ▼             ▼                  ▼
┌─────────────────┐ ┌───────────────┐ ┌───────┐ ┌───────────────┐ ┌────────────────┐
│ Intent & Safety │ │  Appointment  │ │  FAQ  │ │   Follow-up   │ │ Human Handoff  │
│     Agent       │ │     Agent     │ │ Agent │ │     Agent     │ │     Agent      │
└────────┬────────┘ └───────┬───────┘ └───┬───┘ └───────┬───────┘ └───────┬────────┘
         │                  │             │             │                 │
         └──────────────────┴──────┬──────┴─────────────┴─────────────────┘
                                   │
                                   ▼
                   ┌───────────────────────────────┐
                   │    Transactional Services     │
                   │ (Appointment, FAQ, Handoff)   │
                   └───────────────┬───────────────┘
                                   │
                                   ▼
                   ┌───────────────────────────────┐
                   │ SQLite Database (hospital.db) │
                   │  - Doctors & Schedules        │
                   │  - Real Available Slots       │
                   │  - Patients & Appointments    │
                   │  - Approved Hospital FAQs     │
                   │  - Follow-up Records          │
                   │  - Audit Events & Handoffs    │
                   └───────────────────────────────┘
```

### Specialist Multi-Agent Breakdown (Google ADK)

1. **Hospital Receptionist (Root Agent)**: Welcomes patients, detects language (Tamil, English, Tanglish), maintains conversation flow, communicates tool results naturally, and delegates to specialist agents.
2. **Intent & Safety Agent**: Categorizes intent and enforces healthcare guardrails. **Never diagnoses**, **never prescribes**, and immediately escalates life-threatening emergencies to 108 / Emergency line without administrative delays.
3. **Appointment Scheduling Agent**: Manages doctors, schedules, and slots. Tools: `list_doctors`, `get_available_slots`, `book_appointment`, `get_appointment`, `reschedule_appointment`, `cancel_appointment`. Guarantees against double booking via database transactions.
4. **Hospital FAQ Agent**: Answers administrative queries strictly from approved hospital configuration (address, timings, departments, insurance, test preparation). Never guesses unverified policies.
5. **Follow-up Agent**: Inspects upcoming reminders and generates bilingual reminder communications.
6. **Human Handoff Agent**: Coordinates escalation to human receptionists (+91-44-2499-1000) or emergency care (+91-44-2499-1066).

---

## 2. Technology Stack & Pinned Dependencies

- **Language:** Python 3.11+ (verified on Python 3.13 on Windows 11).
- **Multi-Agent Framework:** Google Agent Development Kit (`google-adk==2.11.0`).
- **LLM:** Google Gemini (`gemini-2.5-flash` / `gemini-3.5-flash`) via `google-genai>=2.30.1`.
- **Voice Communication:** LiveKit Agents (`livekit-agents>=1.8.8`, `livekit-plugins-google>=1.8.8`).
- **Database:** SQLite with WAL mode, transactions, uniqueness constraints, and foreign keys.
- **Testing:** `pytest>=8.0.0`, `pytest-asyncio>=0.23.0`.
- **Timezone:** `Asia/Kolkata` (Indian Standard Time).

---

## 3. Project Directory Structure

```
hospital_ai_agent/
├── .env.example                    # Environment variable template
├── .gitignore                      # Git ignore rules for venv, DB, caches
├── pyproject.toml                  # Python package specification
├── requirements.txt                # Pinned dependencies
├── README.md                       # Complete documentation & commands
├── config/
│   ├── __init__.py
│   ├── settings.py                 # Central config validation & secrets protection
│   └── hospital_config.yaml        # Approved bilingual hospital information
├── database/
│   ├── __init__.py
│   ├── connection.py               # SQLite connection & transaction context manager
│   ├── models.py                   # SQL DDL schemas & data structures
│   ├── initialization.py           # Database setup routines
│   └── seed_data.py                # Synthetic demo doctors, slots, and FAQs
├── services/
│   ├── __init__.py
│   ├── appointment_service.py      # Transactional booking, slots, reschedule, cancel
│   ├── faq_service.py              # Approved FAQ & topic lookup service
│   └── handoff_service.py          # Human escalation & audit recording
├── hospital_agents/
│   ├── __init__.py
│   ├── agent.py                    # Root Receptionist Agent (discovered by ADK Web)
│   ├── sub_agents/
│   │   ├── __init__.py
│   │   ├── intent_safety_agent.py  # Safety guardrails & emergency triage
│   │   ├── appointment_agent.py    # Appointment specialist agent
│   │   ├── faq_agent.py            # Hospital FAQ agent
│   │   ├── followup_agent.py       # Follow-up & reminders agent
│   │   └── handoff_agent.py        # Human handoff agent
│   └── tools/
│       ├── __init__.py
│       ├── doctor_tools.py         # list_doctors
│       ├── appointment_tools.py    # get_available_slots, book, reschedule, cancel
│       ├── faq_tools.py            # get_hospital_info, search_faq
│       ├── handoff_tools.py        # escalate_to_human, get_emergency_contact
│       └── followup_tools.py       # get_upcoming_reminders, record_reminder_status
├── voice/
│   ├── __init__.py
│   ├── language_support.py         # Tamil/English/Tanglish detection & phonetic speech formatters
│   ├── adk_bridge.py               # LiveKit FunctionTool bridge to ADK services
│   ├── livekit_agent.py            # Real-time voice agent entrypoint
│   └── telephony.py                # LiveKit SIP telephony caller ID & trunk dispatch
├── scripts/
│   ├── __init__.py
│   └── initialize_db.py            # CLI database reset and seeding utility
└── tests/
    ├── __init__.py
    ├── conftest.py                 # Isolated temporary DB fixtures
    ├── test_appointments.py        # Slot check, booking, double booking, cancel tests
    ├── test_agent_tools.py         # ADK tool callable execution tests
    ├── test_safety.py              # Clinical guardrails & emergency escalation tests
    └── test_voice_bridge.py        # Language detection & voice bridge tests
```

---

## 4. Windows 11 Quickstart Guide

Open PowerShell in the project directory (`d:\agentic ai projects\hospital agents`).

### Step 1: Create and Activate Virtual Environment
```powershell
# Create virtual environment
python -m venv --system-site-packages .venv

# Allow PowerShell script execution if restricted
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process

# Activate virtual environment
.\.venv\Scripts\Activate.ps1
```

### Step 2: Install Dependencies
```powershell
pip install -r requirements.txt
```

### Step 3: Configure Environment Variables
Copy `.env.example` to `.env`:
```powershell
Copy-Item .env.example .env
```
Edit `.env` and insert your Gemini API Key:
```env
GOOGLE_API_KEY=AIzaSyYourActualGeminiApiKeyHere
GEMINI_API_KEY=AIzaSyYourActualGeminiApiKeyHere
GEMINI_MODEL=gemini-2.5-flash
```

### Step 4: Initialize the Database and Seed Demo Records
```powershell
python scripts/initialize_db.py
```
This initializes `hospital.db` with 7 demo doctors across departments (General Medicine, Cardiology, Pediatrics, Orthopedics, ENT, Gynecology) and generates available slots for today, tomorrow, and subsequent days.

### Step 5: Run Automated Tests
```powershell
pytest tests/ -v
```
All 27 automated tests will pass without requiring external API credits.

---

## 5. Development Interfaces & Testing

### Milestone 1: Run Google ADK Web Interface

Google ADK provides a dedicated local development Web UI to inspect agents, test dialogues, and observe tool execution:

```powershell
# Run ADK Web targeting the hospital_agents package
adk web hospital_agents
```
*(Or alternatively using the python module: `python -m google.adk.cli web hospital_agents`)*

1. Open your browser and navigate to: **`http://127.0.0.1:8000`**
2. In the dropdown, select **`hospital_agents`**.
3. You can test interactive conversations in Tamil or English:
   - Patient: `"வணக்கம், நாளைக்கு General Physician appointment கிடைக்குமா?"`
   - Patient: `"I need an appointment with Dr. Priya Raman tomorrow at 10 AM."`
   - Patient: `"What are your hospital outpatient timings?"`
   - Patient: `"I have severe chest pain and left arm numbness."` *(triggers immediate emergency escalation!)*

---

### Milestone 2: Run Real-time Voice Session (Microphone-based)

To run conversational voice with your microphone and headphones via LiveKit:

1. Obtain your free credentials from [LiveKit Cloud](https://cloud.livekit.io/) or run a local LiveKit server.
2. In `.env`, configure:
   ```env
   LIVEKIT_URL=wss://your-project.livekit.cloud
   LIVEKIT_API_KEY=your_api_key
   LIVEKIT_API_SECRET=your_api_secret
   ```
3. In a separate terminal with `.venv` activated, run:
   ```powershell
   python voice/livekit_agent.py dev
   ```
4. Click the playground URL printed in the terminal (e.g., `https://agents-playground.livekit.io/`) to connect your microphone.
5. Speak in Tamil or English. The agent responds naturally with interruptible real-time voice, executing genuine database bookings.

---

### Milestone 3: Real Phone Calls via LiveKit SIP Telephony

To connect ordinary phone calls to the AI receptionist, LiveKit's SIP bridge is utilized:

1. **Purchase a Telephone Number** from a supported carrier (Twilio, Telnyx, Plivo, or Tata Telephony).
2. **Create a LiveKit SIP Inbound Trunk**:
   ```json
   {
     "name": "Kaveri Hospital SIP Trunk",
     "numbers": ["+914424991000"]
   }
   ```
3. **Create a SIP Dispatch Rule**:
   Routes inbound telephone callers into an agent room prefix:
   ```json
   {
     "name": "hospital-dispatch",
     "rule": {
       "dispatchRuleIndividual": {
         "roomPrefix": "hospital-phone-call-"
       }
     }
   }
   ```
4. **Point Carrier to LiveKit SIP URI**:
   In your Twilio or Telnyx console, set the SIP Termination URI to your LiveKit SIP domain.
5. **Start the Production Worker**:
   ```powershell
   python voice/livekit_agent.py start
   ```
When a patient dials the phone number, the telephone carrier forwards audio to LiveKit, `TelephonyManager.extract_caller_phone()` automatically extracts the caller ID, and the agent greets the caller in their language.

---

## 6. Local Development vs. External Paid Services

| Feature | Local Development (Free) | Requires External / Paid Account |
| :--- | :--- | :--- |
| **ADK Web Agent Testing** | **Yes** (Free local FastAPI interface) | Only requires standard Gemini API key |
| **Doctor Availability & Slot Checks** | **Yes** (Real local SQLite DB) | None |
| **Appointment Booking & Double-booking Prevention** | **Yes** (Transactional SQLite) | None |
| **Hospital FAQs (Tamil & English)** | **Yes** (YAML & SQLite) | None |
| **Emergency Triage & Human Handoff** | **Yes** (Recorded in DB) | None |
| **Automated Unit Tests** | **Yes** (`pytest tests/`) | None (Uses mocked/local fixtures) |
| **LiveKit Voice (Browser Microphone)** | **Yes** (LiveKit free tier + Gemini API) | Free LiveKit Cloud account |
| **Inbound Phone Numbers (SIP Trunking)** | No | Paid Carrier (Twilio/Telnyx) & SIP Trunk |

---

## 7. Medical Safety Guardrails & Compliance

> [!CAUTION]
> **Clinical Disclaimer**: This application is a hospital administrative demonstration assistant and is NOT certified as a medical device. It must not be deployed in production clinical environments without formal operational, privacy (HIPAA/DISHA), and clinical safety reviews.

1. **Strict No-Diagnosis Rule**: The agent instructions strictly forbid making clinical diagnoses or interpreting patient symptoms as confirmed pathology.
2. **No-Prescription Rule**: The agent never recommends, alters, or prescribes medications or dosages.
3. **Emergency Priority Triage**: If patient speech contains red-flag emergency symptoms (acute chest pain, stroke symptoms, uncontrolled bleeding, severe breathing distress), routine scheduling is bypassed immediately and emergency hotline guidance (+91-44-2499-1066 / 108) is provided.
4. **Patient Privacy & Verification**: Looking up or modifying existing appointment details requires confirming the caller's phone number against the record.
5. **No Hallucinated Hospital Information**: If hospital policies, fees, or department procedures are not in approved records, the agent explicitly discloses that it cannot verify the detail and provides the human reception contact.

---

## 8. Troubleshooting

### 1. PowerShell Script Execution Error
```
File .venv\Scripts\Activate.ps1 cannot be loaded because running scripts is disabled
```
**Fix:** Run this in PowerShell before activating:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
```

### 2. Windows Unicode / Character Encoding Notice
If you notice encoding errors when running scripts on Windows cp1252 consoles:
**Fix:** Set Python UTF-8 mode in PowerShell:
```powershell
$env:PYTHONUTF8=1
$env:PYTHONIOENCODING="utf-8"
```

### 3. Missing Gemini API Key
```
ValueError: Missing GEMINI_API_KEY or GOOGLE_API_KEY in environment or .env file.
```
**Fix:** Add your Google AI Studio key to `.env` (`GOOGLE_API_KEY=AIzaSy...`) and re-run.

### 4. Port 8000 in Use by Another Application
If port 8000 is taken when starting ADK Web:
**Fix:** Specify a custom port:
```powershell
adk web --port 8080 hospital_agents
```
