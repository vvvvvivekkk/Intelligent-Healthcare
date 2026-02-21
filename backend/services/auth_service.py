import uuid
import logging
from werkzeug.security import generate_password_hash, check_password_hash
from backend.utils.database import query_db, execute_db

logger = logging.getLogger(__name__)


class AuthService:
    """Service layer for authentication operations."""

    @staticmethod
    def generate_patient_id():
        """Generate unique patient ID."""
        return f"PAT-{uuid.uuid4().hex[:8].upper()}"

    @staticmethod
    def generate_doctor_id():
        """Generate unique doctor ID."""
        return f"DOC-{uuid.uuid4().hex[:8].upper()}"

    @staticmethod
    def register_patient(full_name, email, password, phone=None, is_verified=False):
        """Register a new patient. Use is_verified=True when email was already verified via OTP."""
        existing = query_db('SELECT id, is_verified, patient_id, full_name, email, phone, role FROM users WHERE email = ?', (email,), one=True)
        if existing:
            if not existing['is_verified']:
                return None, 'Email already registered but not verified. Please verify your email or use a different address.'
            return None, 'Email already registered'

        patient_id = AuthService.generate_patient_id()
        password_hash = generate_password_hash(password, method='pbkdf2:sha256')
        verified_int = 1 if is_verified else 0

        try:
            user_id = execute_db(
                '''INSERT INTO users (patient_id, full_name, email, phone, password_hash, role, is_verified)
                   VALUES (?, ?, ?, ?, ?, 'patient', ?)''',
                (patient_id, full_name, email, phone, password_hash, verified_int)
            )
            user = query_db('SELECT id, patient_id, full_name, email, phone, role FROM users WHERE id = ?',
                           (user_id,), one=True)
            return dict(user), None
        except Exception as e:
            logger.error(f"Registration error: {e}")
            return None, 'Registration failed'

    @staticmethod
    def login_patient(email, password):
        """Authenticate a patient."""
        email = (email or '').strip().lower()
        if not email:
            logger.debug("Login: empty email")
            return None, 'Invalid email or password'
        if not (password or password.strip()):
            logger.debug("Login: empty password")
            return None, 'Invalid email or password'

        user_row = query_db('SELECT * FROM users WHERE email = ?', (email,), one=True)
        if not user_row:
            logger.info("Login failed: no user for email %s", email)
            return None, 'Invalid email or password'

        # sqlite3.Row does not support .get(); convert to dict
        user = dict(user_row)
        pwh = user.get('password_hash')
        if not pwh:
            logger.warning("Login: user %s has no password_hash", email)
            return None, 'Invalid email or password'
        try:
            if not check_password_hash(pwh, password):
                logger.info("Login failed: wrong password for %s", email)
                return None, 'Invalid email or password'
        except Exception as e:
            logger.exception("Login: check_password_hash failed for %s: %s", email, e)
            return None, 'Invalid email or password'

        # Treat is_verified as truthy (SQLite may return 0/1 as int)
        is_verified = user.get('is_verified') in (1, True, '1')
        if not is_verified:
            logger.info("Login failed: account not verified for %s", email)
            return None, 'Account not verified. Please check your email.'

        return {
            'id': user['id'],
            'patient_id': user['patient_id'],
            'full_name': user['full_name'],
            'email': user['email'],
            'phone': user['phone'],
            'role': user['role']
        }, None

    @staticmethod
    def register_doctor(full_name, email, password, specialization, 
                        experience_years=0, hospital=None, phone=None, bio=None):
        """Register a new doctor."""
        existing = query_db('SELECT id FROM doctors WHERE email = ?', (email,), one=True)
        if existing:
            return None, 'Email already registered'

        doctor_id = AuthService.generate_doctor_id()
        password_hash = generate_password_hash(password, method='pbkdf2:sha256')

        try:
            doc_id = execute_db(
                '''INSERT INTO doctors (doctor_id, full_name, email, phone, password_hash,
                   specialization, experience_years, hospital, bio, verified)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0)''',
                (doctor_id, full_name, email, phone, password_hash,
                 specialization, experience_years, hospital, bio)
            )
            doctor = query_db(
                '''SELECT id, doctor_id, full_name, email, phone, specialization,
                   experience_years, hospital, bio, verified
                   FROM doctors WHERE id = ?''',
                (doc_id,), one=True
            )
            return dict(doctor), None
        except Exception as e:
            logger.error(f"Doctor registration error: {e}")
            return None, 'Registration failed'

    @staticmethod
    def login_doctor(email, password):
        """Authenticate a doctor."""
        doctor = query_db('SELECT * FROM doctors WHERE email = ?', (email,), one=True)
        if not doctor:
            return None, 'Invalid email or password'
        if not check_password_hash(doctor['password_hash'], password):
            return None, 'Invalid email or password'

        return {
            'id': doctor['id'],
            'doctor_id': doctor['doctor_id'],
            'full_name': doctor['full_name'],
            'email': doctor['email'],
            'phone': doctor['phone'],
            'specialization': doctor['specialization'],
            'experience_years': doctor['experience_years'],
            'hospital': doctor['hospital'],
            'bio': doctor['bio'],
            'verified': doctor['verified']
        }, None

    @staticmethod
    def get_patient_by_id(user_id):
        """Get patient details by ID."""
        user = query_db(
            'SELECT id, patient_id, full_name, email, phone, role FROM users WHERE id = ?',
            (user_id,), one=True
        )
        return dict(user) if user else None

    @staticmethod
    def get_doctor_by_id(doctor_id):
        """Get doctor details by ID."""
        doctor = query_db(
            '''SELECT id, doctor_id, full_name, email, phone, specialization,
               experience_years, hospital, bio, verified, rating
               FROM doctors WHERE id = ?''',
            (doctor_id,), one=True
        )
        return dict(doctor) if doctor else None

    @staticmethod
    def create_admin(username, password):
        """Create a new admin (internal usage only). Limits to 2 admins."""
        # Check admin count
        count = query_db('SELECT COUNT(*) as c FROM admins', one=True)
        if count and count['c'] >= 2:
            return None, 'Admin limit reached (max 2)'

        existing = query_db('SELECT id FROM admins WHERE username = ?', (username,), one=True)
        if existing:
            return None, 'Username taken'

        password_hash = generate_password_hash(password)
        try:
            admin_id = execute_db(
                'INSERT INTO admins (username, password_hash) VALUES (?, ?)',
                (username, password_hash)
            )
            return admin_id, None
        except Exception as e:
            logger.error(f"Admin creation error: {e}")
            return None, 'Creation failed'

    @staticmethod
    def login_admin(username, password):
        """Authenticate an admin."""
        # Use case-insensitive username match if desired, but sticking to exact match for security
        admin = query_db('SELECT * FROM admins WHERE username = ?', (username,), one=True)
        
        if not admin:
            logger.warning(f"Admin login failed: User '{username}' not found")
            return None, 'Invalid credentials'
        
        if not check_password_hash(admin['password_hash'], password):
            logger.warning(f"Admin login failed: Password mismatch for '{username}'")
            return None, 'Invalid credentials'

        logger.info(f"Admin '{username}' logged in successfully")
        return {
            'id': admin['id'],
            'username': admin['username'],
            'role': 'admin'
        }, None

    @staticmethod
    def get_admin_by_id(admin_id):
        """Get admin details."""
        admin = query_db('SELECT id, username, created_at FROM admins WHERE id = ?', (admin_id,), one=True)
        return dict(admin) if admin else None
