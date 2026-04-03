import sqlite3
import os

# Use same location as app: project root + DATABASE_PATH or 'medsync.db'
PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
DB_PATH = os.path.join(PROJECT_ROOT, os.environ.get('DATABASE_PATH', 'medsync.db'))


def update_schema():
    conn = sqlite3.connect(DB_PATH)
    try:
        # Add is_verified to users
        try:
            conn.execute("ALTER TABLE users ADD COLUMN is_verified INTEGER DEFAULT 0")
            print("Added is_verified column to users table.")
        except sqlite3.OperationalError as e:
            if "duplicate column" in str(e).lower():
                print("is_verified column already exists.")
            else:
                print(f"Error adding column: {e}")

        # Create account_verifications table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS account_verifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                token TEXT UNIQUE,
                otp_code TEXT,
                expires_at TIMESTAMP,
                attempts INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        print("Created account_verifications table.")

        # Registration OTP table (pre-account email verification)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS registration_otp (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                otp_hash TEXT NOT NULL,
                expires_at TIMESTAMP NOT NULL,
                attempts INTEGER DEFAULT 0,
                verified_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("Created registration_otp table.")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_registration_otp_email ON registration_otp(email)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_registration_otp_expires ON registration_otp(expires_at)")
        print("Created registration_otp indexes.")

        conn.execute("""
            CREATE TABLE IF NOT EXISTS doctor_availability_rules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                doctor_id INTEGER NOT NULL,
                weekday INTEGER NOT NULL CHECK(weekday BETWEEN 0 AND 6),
                start_time TEXT NOT NULL,
                end_time TEXT NOT NULL,
                slot_duration_minutes INTEGER DEFAULT 30,
                active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (doctor_id) REFERENCES doctors(id) ON DELETE CASCADE,
                UNIQUE(doctor_id, weekday, start_time)
            )
        """)
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_doctor_availability_rules_doctor_weekday ON doctor_availability_rules(doctor_id, weekday)"
        )
        print("Created doctor_availability_rules table and index.")

        # Backfill recurring rules from existing slots so older databases can adopt the new flow.
        existing_rule_count = conn.execute("SELECT COUNT(*) FROM doctor_availability_rules").fetchone()[0]
        if existing_rule_count == 0:
            rows = conn.execute(
                """
                SELECT doctor_id,
                       CAST(strftime('%w', slot_date) AS INTEGER) AS weekday,
                       start_time,
                       end_time
                FROM slots
                GROUP BY doctor_id, CAST(strftime('%w', slot_date) AS INTEGER), start_time, end_time
                ORDER BY doctor_id, weekday, start_time
                """
            ).fetchall()
            for doctor_id, weekday, start_time, end_time in rows:
                conn.execute(
                    """
                    INSERT OR IGNORE INTO doctor_availability_rules
                    (doctor_id, weekday, start_time, end_time, slot_duration_minutes, active)
                    VALUES (?, ?, ?, ?, 30, 1)
                    """,
                    (doctor_id, weekday, start_time, end_time)
                )
            if rows:
                print(f"Backfilled {len(rows)} recurring availability rules from existing slots.")

        conn.commit()
    except Exception as e:
        print(f"Update failed: {e}")
    finally:
        conn.close()


if __name__ == '__main__':
    if os.path.exists(DB_PATH):
        update_schema()
        print("Done.")
    else:
        print(f"Database not found at {DB_PATH}")
