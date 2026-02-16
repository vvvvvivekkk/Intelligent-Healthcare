-- MedSync AI Database Schema
-- Normalized, with foreign keys and indexes

PRAGMA foreign_keys = ON;

-- Users table (patients)
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id TEXT UNIQUE NOT NULL,
    full_name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    phone TEXT,
    password_hash TEXT NOT NULL,
    role TEXT DEFAULT 'patient' CHECK(role IN ('patient', 'admin')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Doctors table
CREATE TABLE IF NOT EXISTS doctors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    doctor_id TEXT UNIQUE NOT NULL,
    full_name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    phone TEXT,
    password_hash TEXT NOT NULL,
    specialization TEXT NOT NULL,
    experience_years INTEGER DEFAULT 0,
    hospital TEXT,
    bio TEXT,
    verified INTEGER DEFAULT 0,
    rating REAL DEFAULT 0.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Slots table
CREATE TABLE IF NOT EXISTS slots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    doctor_id INTEGER NOT NULL,
    slot_date TEXT NOT NULL,
    start_time TEXT NOT NULL,
    end_time TEXT NOT NULL,
    is_booked INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (doctor_id) REFERENCES doctors(id) ON DELETE CASCADE,
    UNIQUE(doctor_id, slot_date, start_time)
);

-- Appointments table
CREATE TABLE IF NOT EXISTS appointments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    appointment_id TEXT UNIQUE NOT NULL,
    patient_id INTEGER NOT NULL,
    doctor_id INTEGER NOT NULL,
    slot_id INTEGER NOT NULL,
    status TEXT DEFAULT 'scheduled' CHECK(status IN (
        'scheduled', 'completed', 'cancelled',
        'emergency_cancelled', 'rescheduled', 'otp_pending'
    )),
    reason TEXT,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (doctor_id) REFERENCES doctors(id) ON DELETE CASCADE,
    FOREIGN KEY (slot_id) REFERENCES slots(id) ON DELETE CASCADE
);

-- Chat history table
CREATE TABLE IF NOT EXISTS chat_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    session_id TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('user', 'assistant', 'system')),
    message TEXT NOT NULL,
    metadata TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Disease-specialization mapping
CREATE TABLE IF NOT EXISTS disease_specialization_mapping (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    disease TEXT NOT NULL,
    specialization TEXT NOT NULL,
    description TEXT,
    UNIQUE(disease, specialization)
);

-- OTP verification table
CREATE TABLE IF NOT EXISTS otp_verification (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    appointment_id INTEGER NOT NULL,
    otp_code TEXT NOT NULL,
    is_verified INTEGER DEFAULT 0,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (appointment_id) REFERENCES appointments(id) ON DELETE CASCADE
);

-- Notifications table
CREATE TABLE IF NOT EXISTS notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    doctor_id INTEGER,
    recipient_type TEXT NOT NULL CHECK(recipient_type IN ('patient', 'doctor')),
    title TEXT NOT NULL,
    message TEXT NOT NULL,
    notification_type TEXT DEFAULT 'info' CHECK(notification_type IN (
        'info', 'reminder', 'cancellation', 'emergency', 'otp', 'booking'
    )),
    is_read INTEGER DEFAULT 0,
    related_appointment_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
    FOREIGN KEY (doctor_id) REFERENCES doctors(id) ON DELETE SET NULL,
    FOREIGN KEY (related_appointment_id) REFERENCES appointments(id) ON DELETE SET NULL
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_patient_id ON users(patient_id);
CREATE INDEX IF NOT EXISTS idx_doctors_email ON doctors(email);
CREATE INDEX IF NOT EXISTS idx_doctors_specialization ON doctors(specialization);
CREATE INDEX IF NOT EXISTS idx_slots_doctor_date ON slots(doctor_id, slot_date);
CREATE INDEX IF NOT EXISTS idx_appointments_patient ON appointments(patient_id);
CREATE INDEX IF NOT EXISTS idx_appointments_doctor ON appointments(doctor_id);
CREATE INDEX IF NOT EXISTS idx_appointments_status ON appointments(status);
CREATE INDEX IF NOT EXISTS idx_chat_history_user ON chat_history(user_id);
CREATE INDEX IF NOT EXISTS idx_chat_history_session ON chat_history(session_id);
CREATE INDEX IF NOT EXISTS idx_notifications_user ON notifications(user_id);
CREATE INDEX IF NOT EXISTS idx_notifications_doctor ON notifications(doctor_id);
CREATE INDEX IF NOT EXISTS idx_otp_appointment ON otp_verification(appointment_id);
