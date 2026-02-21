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
- 📧 **Patient registration with OTP email verification** (verify email before account creation)
- 🔒 **Consultation OTP** – Generated at booking; patients view and share with doctor to complete the visit
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

Edit `.env` with:

```
OPENROUTER_API_KEY=your_key_here
```

Get a free key at [openrouter.ai](https://openrouter.ai)

**Email (for registration OTP & notifications):** To send verification codes and emails, set:

```
GMAIL_SENDER=your@gmail.com
GMAIL_PASSWORD=your_app_password
```

Use a [Gmail App Password](https://support.google.com/accounts/answer/185833) (Google Account → Security → 2-Step Verification → App passwords). If these are not set, registration OTP emails will fail to send.

**Test without email:** Add `MAIL_DEBUG_OTP_TO_CONSOLE=true` to `.env` and restart the app. When you click "Verify Email", the 6-digit OTP will be printed in the server console so you can complete registration without configuring Gmail.

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

### 5. (Optional) Migrate Existing Database

If you have an existing database from before the OTP registration flow, run once to add the `registration_otp` table:

```bash
python debug/update_db_schema.py
```

## Patient Registration Flow (OTP Verification)

New patients must verify their email with a 6-digit OTP before creating an account:

1. On **Register**, enter **Full Name** and **Email**, then click **Verify Email**.
2. A code is sent to the email (expires in 5 minutes). Enter the code and click **Verify OTP**.
3. After successful verification, **Password** and **Confirm Password** unlock; complete the form and click **Create Account**.

- OTP is stored hashed; max **3** verification attempts per code; **Resend code** is available if the email didn’t arrive.
- The account is created only after OTP verification, and the user can sign in immediately (no separate verification link).

### Can't log in after registering?

If you created an account but get "Invalid email or password" or "Login failed", reset the password and mark the account verified:

```bash
python debug/set_patient_password.py your@email.com
```

Then log in with password `patient123` (or pass a second argument to set a different password).

## Consultation OTP (Appointments)

When a patient books an appointment, a **consultation OTP** is created automatically (valid 24 hours). The patient can:

- See it in **My Appointments** → **View OTP** for that appointment
- Share the OTP with the doctor during the visit; the doctor enters it to verify and mark the appointment completed

For appointments booked before this feature, the OTP is generated the first time the patient clicks **View OTP**.

## Debug Scripts

Run from the project root (`healthcare/`):

| Script | Purpose |
|--------|---------|
| `python debug/update_db_schema.py` | Add missing tables (e.g. `registration_otp`) to an existing database |
| `python debug/set_patient_password.py <email> [password]` | Reset a patient’s password and set account verified (default password: `patient123`) |
| `python debug/mark_patient_verified.py <email>` | Mark a patient as verified so they can log in |
| `python debug/clear_patients.py` | Remove all patients except the test patient (`patient@medsync.com` / PAT-TEST0001) |

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
├── debug/
│   ├── update_db_schema.py    # Migrate DB (e.g. registration_otp table)
│   ├── set_patient_password.py # Reset patient password & set verified
│   ├── mark_patient_verified.py # Mark patient verified for login
│   └── clear_patients.py      # Keep only test patient
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
│   │   ├── notification_service.py
│   │   ├── email_service.py           # Sends OTP & verification emails
│   │   ├── registration_otp_service.py # Pre-registration email OTP
│   │   └── account_verification_service.py # Legacy link verification
│   └── utils/
│       ├── database.py     # SQLite helpers
│       └── helpers.py      # Decorators & validators
└── frontend/
    ├── css/style.css
    ├── js/app.js           # API integration layer
    └── pages/
        ├── index.html
        ├── login.html
        ├── register.html              # OTP verification before account creation
        ├── verify_otp.html             # Legacy email-link OTP page
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
- `POST /send-registration-otp` – Send 6-digit OTP to email (before registration)
- `POST /verify-registration-otp` – Verify OTP; required before creating patient account
- `POST /register/patient` – Register patient (email must be OTP-verified first)
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
- `POST /book` – Book appointment (consultation OTP is created automatically)
- `POST /slots` – Create slot (doctor)
- `GET /slots/doctor/<id>` – Get doctor slots
- `GET /<id>/otp/status` – Get consultation OTP for an appointment (patient view)
- `POST /<id>/cancel` – Cancel appointment
- `POST /<id>/reschedule` – Reschedule
- `POST /<id>/emergency-cancel` – Emergency cancel
- `POST /<id>/otp/generate` – Generate OTP (on demand)
- `POST /<id>/otp/verify` – Verify OTP (doctor completes consultation)

### Chatbot (`/api/chatbot`)
- `POST /message` – Send message to AI
- `POST /new-session` – Start new chat
- `GET /history` – Chat history
- `GET /sessions` – All sessions


