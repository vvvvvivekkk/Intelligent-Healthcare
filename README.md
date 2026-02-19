# MedSync AI – Intelligent Healthcare Appointment & Consultation Platform

A full-stack AI-powered healthcare platform with symptom analysis, doctor recommendations, appointment booking, OTP verification, and emergency rescheduling.

## Tech Stack

- **Backend**: Python Flask with Blueprints, SQLite
- **Frontend**: Vanilla HTML/CSS/JavaScript
- **AI**: OpenRouter API (Meta Llama 3.3 70B)
- **Auth**: Session-based with role-based access control

## Features

- 🤖 AI chatbot for symptom analysis & doctor recommendations
- 👨‍⚕️ Doctor search by name, specialization, or disease
- 📅 Appointment booking with time slot management
- 🔒 OTP verification for consultations
- 🚨 Emergency cancellation & rescheduling
- 🔔 Notification system
- 👨‍💼 Separate patient & doctor portals

## Setup

### 1. Install Dependencies

```bash
cd healthcare
pip install -r requirements.txt
```

### 2. Configure Environment

Edit `.env` and set your OpenRouter API key:

```
OPENROUTER_API_KEY=your_key_here
```

Get a free key at [openrouter.ai](https://openrouter.ai)

### 3. Initialize Database & Seed Data

```bash
python seed_data.py
```

This creates the SQLite database with schema, 12 doctors, 46 disease mappings, and a test patient account.

### 4. Run the Application

```bash
python app.py
```

Open **http://localhost:5000** in your browser.

## Test Credentials

> **Note:** The system uses strict role-based access control (RBAC) for Patients, Doctors, and Admins.

### 🛡️ Admin Account (Max 2 Allowed)

| Username | Password       | Role        |
|----------|----------------|-------------|
| admin    | admin123       | Admin       |
| sysadmin | secureStrong!23| System Admin|

**Login at:** [http://localhost:5000/admin/login](http://localhost:5000/admin/login)

### 🧑‍🤒 Patient Account

| Email                  | Password     | Patient ID    |
|------------------------|-------------- |---------------|
| patient@medsync.com    | patient123   | PAT-TEST0001  |

**Login at:** [http://localhost:5000/login](http://localhost:5000/login)

### 👨‍⚕️ Doctor Accounts (All use password: `doctor123`)

| #  | Name                  | Email                            | Specialization    | Hospital                     | Doctor ID    |
|----|----------------------|----------------------------------|-------------------|------------------------------|--------------|
| 1  | Dr. Sarah Mitchell    | sarah.mitchell@medsync.com       | Cardiology        | City Heart Hospital          | DOC-CARD001  |
| 2  | Dr. James Chen        | james.chen@medsync.com           | Neurology         | NeuroHealth Center           | DOC-NEUR001  |
| 3  | Dr. Priya Sharma      | priya.sharma@medsync.com         | Dermatology       | SkinCare Clinic              | DOC-DERM001  |
| 4  | Dr. Michael Brown     | michael.brown@medsync.com        | Orthopedics       | Joint & Spine Center         | DOC-ORTH001  |
| 5  | Dr. Emily Davis       | emily.davis@medsync.com          | Pediatrics        | Children's Wellness Clinic   | DOC-PEDI001  |
| 6  | Dr. Robert Wilson     | robert.wilson@medsync.com        | Gastroenterology  | Digestive Health Institute   | DOC-GAST001  |
| 7  | Dr. Lisa Anderson     | lisa.anderson@medsync.com        | Pulmonology       | Breathing Care Center        | DOC-PULM001  |
| 8  | Dr. Raj Patel         | raj.patel@medsync.com            | Endocrinology     | Diabetes & Hormone Center    | DOC-ENDO001  |
| 9  | Dr. Amanda Foster     | amanda.foster@medsync.com        | Psychiatry        | Mental Wellness Institute    | DOC-PSYC001  |
| 10 | Dr. David Kim         | david.kim@medsync.com            | Ophthalmology     | Vision Care Center           | DOC-OPTH001  |
| 11 | Dr. Maria Garcia      | maria.garcia@medsync.com         | ENT               | Ear Nose Throat Specialists  | DOC-ENT001   |
| 12 | Dr. Thomas Lee        | thomas.lee@medsync.com           | General Medicine  | HealthFirst Primary Care     | DOC-GENM001  |

**Login at:** [http://localhost:5000/doctor/login](http://localhost:5000/doctor/login)

## Project Structure

```
healthcare/
├── app.py                  # Flask entry point
├── seed_data.py            # Database seeder
├── requirements.txt
├── .env
├── backend/
│   ├── config.py           # App configuration
│   ├── blueprints/
│   │   ├── auth.py         # Auth routes
│   │   ├── doctors.py      # Doctor routes
│   │   ├── appointments.py # Appointment routes
│   │   └── chatbot.py      # AI chatbot routes
│   ├── services/
│   │   ├── auth_service.py
│   │   ├── doctor_service.py
│   │   ├── appointment_service.py
│   │   ├── chatbot_service.py
│   │   ├── otp_service.py
│   │   └── notification_service.py
│   └── utils/
│       ├── database.py     # SQLite helpers
│       └── helpers.py      # Decorators & validators
└── frontend/
    ├── css/style.css
    ├── js/app.js           # API integration layer
    └── pages/
        ├── index.html
        ├── login.html
        ├── register.html
        ├── doctor_login.html
        ├── doctor_register.html
        ├── patient_dashboard.html
        ├── patient_appointments.html
        ├── doctor_dashboard.html
        ├── browse_doctors.html
        └── chatbot.html
```

## API Endpoints

### Auth (`/api/auth`)
- `POST /register/patient` – Register patient
- `POST /register/doctor` – Register doctor
- `POST /login/patient` – Patient login
- `POST /login/doctor` – Doctor login
- `POST /logout` – Logout
- `GET /me` – Current user info
- `GET /session` – Session check

### Doctors (`/api/doctors`)
- `GET /all` – All doctors
- `GET /search?q=` – Search doctors
- `GET /specializations` – List specializations
- `GET /by-specialization/<spec>` – Filter by specialization
- `GET /disease-mapping` – Disease-to-specialization map
- `POST /recommend` – Get recommendations by specialization

### Appointments (`/api/appointments`)
- `POST /book` – Book appointment
- `POST /slots` – Create slot (doctor)
- `GET /slots/doctor/<id>` – Get doctor slots
- `POST /<id>/cancel` – Cancel appointment
- `POST /<id>/reschedule` – Reschedule
- `POST /<id>/emergency-cancel` – Emergency cancel
- `POST /<id>/otp/generate` – Generate OTP
- `POST /<id>/otp/verify` – Verify OTP

### Chatbot (`/api/chatbot`)
- `POST /message` – Send message to AI
- `POST /new-session` – Start new chat
- `GET /history` – Chat history
- `GET /sessions` – All sessions
"# Intelligent-Healthcare"


