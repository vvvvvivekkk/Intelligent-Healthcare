"""
Reset a patient's password and set verified so they can log in.
Use this if you created an account but cannot sign in.

Usage: python debug/set_patient_password.py <email> [new_password]

Example:
  python debug/set_patient_password.py 1102005vivekreddy@gmail.com
  python debug/set_patient_password.py 1102005vivekreddy@gmail.com mynewpass123

If new_password is omitted, defaults to "patient123".
"""
import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)
DB_PATH = os.path.join(PROJECT_ROOT, os.environ.get('DATABASE_PATH', 'medsync.db'))


def main():
    if len(sys.argv) < 2:
        print("Usage: python debug/set_patient_password.py <email> [new_password]")
        print("Example: python debug/set_patient_password.py 1102005vivekreddy@gmail.com patient123")
        return
    email = sys.argv[1].strip().lower()
    new_password = (sys.argv[2] if len(sys.argv) > 2 else "patient123").strip()
    if not new_password or len(new_password) < 6:
        new_password = "patient123"
    if not email or "@" not in email:
        print("Please provide a valid email address.")
        return

    import sqlite3
    from werkzeug.security import generate_password_hash

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

    user_id, full_name, was_verified = row[0], row[1], row[2]
    password_hash = generate_password_hash(new_password, method='pbkdf2:sha256')

    cur.execute("UPDATE users SET password_hash = ?, is_verified = 1 WHERE id = ?", (password_hash, user_id))
    conn.commit()
    conn.close()

    print(f"Updated {email} ({full_name}): password set, account marked verified.")
    print(f"Log in with password: {new_password}")


if __name__ == '__main__':
    main()
