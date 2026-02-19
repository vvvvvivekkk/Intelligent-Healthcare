import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.services.auth_service import AuthService
from backend.utils.database import init_db

def verify_login():
    print("Verifying Admin Login via Service...")
    
    # Try login
    user, err = AuthService.login_admin('admin', 'admin123')
    if err:
        print(f"Login failed: {err}")
    else:
        print(f"Login successful! User: {user}")

if __name__ == '__main__':
    verify_login()
