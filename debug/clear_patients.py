"""
Clear all patient accounts except the test patient:
  patient@medsync.com | patient123 | PAT-TEST0001

Run from project root: python debug/clear_patients.py
"""
import os
import sys

# Project root = parent of debug/
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

DB_PATH = os.path.join(PROJECT_ROOT, os.environ.get('DATABASE_PATH', 'medsync.db'))

KEEP_EMAIL = 'patient@medsync.com'
KEEP_PATIENT_ID = 'PAT-TEST0001'


def clear_patients():
    import sqlite3
    if not os.path.exists(DB_PATH):
        print(f"Database not found: {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    cur = conn.cursor()

    # Resolve kept user id
    cur.execute("SELECT id FROM users WHERE email = ? AND patient_id = ?", (KEEP_EMAIL, KEEP_PATIENT_ID))
    row = cur.fetchone()
    if not row:
        print(f"Test patient not found ({KEEP_EMAIL} / {KEEP_PATIENT_ID}). Nothing to do.")
        conn.close()
        return

    keep_id = row[0]

    # Delete in order (respect foreign keys)
    cur.execute("DELETE FROM appointments WHERE patient_id != ?", (keep_id,))
    apt = cur.rowcount
    cur.execute("DELETE FROM chat_history WHERE user_id != ?", (keep_id,))
    chat = cur.rowcount
    cur.execute("DELETE FROM notifications WHERE recipient_type = 'patient' AND user_id != ?", (keep_id,))
    notif = cur.rowcount
    cur.execute("DELETE FROM account_verifications WHERE user_id != ?", (keep_id,))
    av = cur.rowcount
    # Clear registration OTP for any other emails (kept patient is already registered)
    try:
        cur.execute("DELETE FROM registration_otp WHERE email != ?", (KEEP_EMAIL,))
        rotp = cur.rowcount
    except sqlite3.OperationalError:
        rotp = 0  # table may not exist in old DBs
    cur.execute("DELETE FROM users WHERE id != ?", (keep_id,))
    users = cur.rowcount

    conn.commit()
    conn.close()

    print(f"Cleared: {users} patient(s), {apt} appointment(s), {chat} chat row(s), {notif} notification(s), {av} verification(s), {rotp} registration OTP(s).")
    print(f"Kept: {KEEP_EMAIL} ({KEEP_PATIENT_ID})")


if __name__ == '__main__':
    clear_patients()
