import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.utils.database import query_db, execute_db, init_db
from werkzeug.security import generate_password_hash

def force_create_admin():
    print("Forcing admin creation...")
    
    # Ensure table exists
    init_db()
    
    # Check existing
    existing = query_db('SELECT * FROM admins WHERE username = ?', ('admin',), one=True)
    if existing:
        print(f"Admin 'admin' already exists. ID: {existing['id']}")
        # Update password just in case
        pwd_hash = generate_password_hash('admin123', method='pbkdf2:sha256')
        execute_db('UPDATE admins SET password_hash = ? WHERE id = ?', (pwd_hash, existing['id']))
        print("Password updated to 'admin123'")
    else:
        print("Creating admin 'admin'...")
        pwd_hash = generate_password_hash('admin123', method='pbkdf2:sha256')
        try:
            execute_db('INSERT INTO admins (username, password_hash) VALUES (?, ?)', ('admin', pwd_hash))
            print("Admin created successfully.")
        except Exception as e:
            print(f"Error creating admin: {e}")

    # Check all admins
    admins = query_db('SELECT * FROM admins')
    print("Current admins in DB:")
    for a in admins:
        print(f"- {a['username']}")

if __name__ == '__main__':
    force_create_admin()
