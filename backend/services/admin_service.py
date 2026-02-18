import uuid
import logging
from werkzeug.security import generate_password_hash
from backend.utils.database import query_db, execute_db

logger = logging.getLogger(__name__)

class AdminService:
    """Service layer for administrative operations."""

    @staticmethod
    def add_doctor(data):
        """Add a new doctor from admin panel."""
        try:
            # Check for duplicate email
            existing = query_db('SELECT id FROM doctors WHERE email = ?', (data['email'],), one=True)
            if existing:
                return None, 'A doctor with this email already exists'

            doctor_id = f"DOC-{uuid.uuid4().hex[:8].upper()}"
            password_hash = generate_password_hash(data.get('password', 'doctor123'))

            execute_db(
                '''INSERT INTO doctors (doctor_id, full_name, email, phone, password_hash,
                   specialization, experience_years, hospital, bio, verified)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1)''',
                (doctor_id, data['full_name'], data['email'], data.get('phone', ''),
                 password_hash, data['specialization'], data.get('experience_years', 0),
                 data.get('hospital', ''), data.get('bio', ''))
            )
            logger.info(f"Admin added doctor: {data['full_name']} ({doctor_id})")
            return {'doctor_id': doctor_id, 'full_name': data['full_name']}, None
        except Exception as e:
            logger.error(f"Add doctor error: {e}")
            return None, f"Failed to add doctor: {e}"

    @staticmethod
    def get_dashboard_stats():
        """Get system-wide statistics."""
        try:
            patients = query_db('SELECT COUNT(*) as c FROM users WHERE role="patient"', one=True)['c']
            doctors = query_db('SELECT COUNT(*) as c FROM doctors', one=True)['c']
            pending_doctors = query_db('SELECT COUNT(*) as c FROM doctors WHERE verified=0', one=True)['c']
            appointments = query_db('SELECT COUNT(*) as c FROM appointments', one=True)['c']
            
            return {
                'total_patients': patients,
                'total_doctors': doctors,
                'pending_verifications': pending_doctors,
                'total_appointments': appointments
            }, None
        except Exception as e:
            return None, str(e)

    @staticmethod
    def get_all_doctors():
        """Get all doctors with verification status."""
        return query_db(
            '''SELECT id, doctor_id, full_name, email, phone, specialization, 
               experience_years, hospital, bio, verified, rating, created_at 
               FROM doctors ORDER BY created_at DESC'''
        )

    @staticmethod
    def get_all_patients():
        """Get all patients."""
        return query_db(
            '''SELECT id, patient_id, full_name, email, phone, created_at 
               FROM users WHERE role="patient" ORDER BY created_at DESC'''
        )

    @staticmethod
    def verify_doctor(doctor_id):
        """Approve a newly registered doctor."""
        try:
            execute_db('UPDATE doctors SET verified = 1 WHERE id = ?', (doctor_id,))
            return True, 'Doctor verified successfully'
        except Exception as e:
            return False, f"Verification failed: {e}"

    @staticmethod
    def delete_doctor(doctor_id):
        """Delete a doctor account."""
        try:
            execute_db('DELETE FROM doctors WHERE id = ?', (doctor_id,))
            return True, 'Doctor deleted successfully'
        except Exception as e:
            return False, f"Deletion failed: {e}"

    @staticmethod
    def delete_patient(patient_id):
        """Delete a patient account."""
        try:
            execute_db('DELETE FROM users WHERE id = ?', (patient_id,))
            return True, 'Patient deleted successfully'
        except Exception as e:
            return False, f"Deletion failed: {e}"

    @staticmethod
    def get_all_appointments():
        """Get all appointments with details."""
        return query_db(
            '''SELECT a.id, a.appointment_id, a.status, a.slot_id, 
               u.full_name as patient_name, d.full_name as doctor_name, 
               s.slot_date, s.start_time
               FROM appointments a
               JOIN users u ON a.patient_id = u.id
               JOIN doctors d ON a.doctor_id = d.id
               JOIN slots s ON a.slot_id = s.id
               ORDER BY a.created_at DESC LIMIT 100'''
        )

    @staticmethod
    def get_recent_chat_logs():
        """Get system-wide chat logs."""
        return query_db(
            '''SELECT c.id, c.session_id, c.role, c.message, c.created_at, 
               u.full_name as user_name
               FROM chat_history c
               JOIN users u ON c.user_id = u.id
               ORDER BY c.created_at DESC LIMIT 50'''
        )
