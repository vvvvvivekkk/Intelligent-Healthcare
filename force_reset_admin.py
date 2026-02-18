import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.utils.database import execute_db, query_db, init_db
from werkzeug.security import generate_password_hash, check_password_hash

def force_reset():
    print("Forcing Admin Reset with default hash method...")
    init_db()
    
    # Generate hash using default method (safest compatibility)
    pwd_hash = generate_password_hash('admin123')
    print(f"Generated hash: {pwd_hash}")
    
    # Delete existing
    execute_db("DELETE FROM admins WHERE username='admin'")
    
    # Insert new
    try:
        execute_db("INSERT INTO admins (username, password_hash) VALUES (?, ?)", ('admin', pwd_hash))
        print("Admin user recreated successfully.")
    except Exception as e:
        print(f"Error creating admin: {e}")

    # Verify immediately
    admin = query_db("SELECT * FROM admins WHERE username='admin'", one=True)
    if admin:
        print(f"Stored hash: {admin['password_hash']}")
        is_valid = check_password_hash(admin['password_hash'], 'admin123')
        print(f"Immediate verification check: {is_valid}")
    else:
        print("Admin verification failed: User not found!")

if __name__ == '__main__':
    force_reset()
