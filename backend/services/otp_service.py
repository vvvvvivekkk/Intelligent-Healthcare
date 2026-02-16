import random
import string
import logging
from datetime import datetime, timedelta
from backend.utils.database import query_db, execute_db

logger = logging.getLogger(__name__)


class OTPService:
    """Service layer for OTP-based consultation security."""

    @staticmethod
    def generate_otp(length=6):
        """Generate a random numeric OTP."""
        return ''.join(random.choices(string.digits, k=length))

    @staticmethod
    def create_otp(appointment_id, expiry_minutes=10):
        """Create and store OTP for an appointment."""
        otp_code = OTPService.generate_otp()
        expires_at = (datetime.now() + timedelta(minutes=expiry_minutes)).strftime('%Y-%m-%d %H:%M:%S')

        # Invalidate any existing OTPs
        execute_db(
            'DELETE FROM otp_verification WHERE appointment_id = ? AND is_verified = 0',
            (appointment_id,)
        )

        execute_db(
            '''INSERT INTO otp_verification (appointment_id, otp_code, is_verified, expires_at)
               VALUES (?, ?, 0, ?)''',
            (appointment_id, otp_code, expires_at)
        )

        # Update appointment status
        execute_db(
            'UPDATE appointments SET status = "otp_pending" WHERE id = ?',
            (appointment_id,)
        )

        logger.info(f"OTP generated for appointment {appointment_id}")
        return otp_code

    @staticmethod
    def verify_otp(appointment_id, otp_code):
        """Verify OTP for an appointment."""
        record = query_db(
            '''SELECT * FROM otp_verification 
               WHERE appointment_id = ? AND otp_code = ? AND is_verified = 0
               ORDER BY created_at DESC LIMIT 1''',
            (appointment_id, otp_code), one=True
        )

        if not record:
            return False, 'Invalid OTP'

        # Check expiry
        expires_at = datetime.strptime(record['expires_at'], '%Y-%m-%d %H:%M:%S')
        if datetime.now() > expires_at:
            return False, 'OTP has expired. Please request a new one.'

        # Mark as verified
        execute_db(
            'UPDATE otp_verification SET is_verified = 1 WHERE id = ?',
            (record['id'],)
        )

        # Update appointment status
        execute_db(
            'UPDATE appointments SET status = "scheduled" WHERE id = ?',
            (appointment_id,)
        )

        return True, 'OTP verified successfully'

    @staticmethod
    def get_otp_status(appointment_id):
        """Get OTP verification status for an appointment."""
        record = query_db(
            '''SELECT * FROM otp_verification WHERE appointment_id = ?
               ORDER BY created_at DESC LIMIT 1''',
            (appointment_id,), one=True
        )
        if not record:
            return None
        return {
            'is_verified': bool(record['is_verified']),
            'expires_at': record['expires_at'],
            'created_at': record['created_at']
        }
