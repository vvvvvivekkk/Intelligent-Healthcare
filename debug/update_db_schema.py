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
