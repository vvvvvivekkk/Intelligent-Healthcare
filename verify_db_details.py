import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.utils.database import query_db

def inspect_db():
    print("Inspecting admins table...")
    admin = query_db("SELECT * FROM admins WHERE username='admin'", one=True)
    if admin:
        print(f"ID: {admin['id']}")
        print(f"Username: '{admin['username']}'")
        print(f"Password Hash: '{admin['password_hash']}'")
        
        # Verify hash manually if werkzeug available
        try:
            from werkzeug.security import check_password_hash
            is_valid = check_password_hash(admin['password_hash'], 'admin123')
            print(f"Testing check_password_hash('admin123'): {is_valid}")
        except ImportError:
            print("Werkzeug check_password_hash unavailable.")
    else:
        print("Admin user not found!")

if __name__ == '__main__':
    inspect_db()
