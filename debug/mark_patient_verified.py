"""
Mark a patient as verified so they can log in (e.g. after OTP registration).
Usage: python debug/mark_patient_verified.py your@email.com
"""
import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)
DB_PATH = os.path.join(PROJECT_ROOT, os.environ.get('DATABASE_PATH', 'medsync.db'))


def main():
    if len(sys.argv) < 2:
        print("Usage: python debug/mark_patient_verified.py <email>")
        print("Example: python debug/mark_patient_verified.py 1102005vivekreddy@gmail.com")
        return
    email = sys.argv[1].strip().lower()
    if not email or "@" not in email:
        print("Please provide a valid email address.")
        return

    import sqlite3
    if not os.path.exists(DB_PATH):
        print(f"Database not found: {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT id, full_name, is_verified FROM users WHERE email = ?", (email,))
    row = cur.fetchone()
    if not row:
        print(f"No patient found with email: {email}")
        conn.close()
        return

    user_id, full_name, was = row[0], row[1], row[2]
    if was == 1:
        print(f"Patient {email} is already verified. You can log in.")
        conn.close()
        return

    cur.execute("UPDATE users SET is_verified = 1 WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()
    print(f"Marked {email} ({full_name}) as verified. You can log in now.")


if __name__ == '__main__':
    main()
