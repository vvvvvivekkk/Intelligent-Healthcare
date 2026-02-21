"""
Pre-registration email OTP verification.
OTP is sent and verified before the patient account is created.
OTP stored hashed; 5 min expiry; max 3 attempts.
"""
import random
import string
import logging
from datetime import datetime, timedelta

from werkzeug.security import generate_password_hash, check_password_hash

from flask import current_app
from backend.utils.database import query_db, execute_db
from backend.services.email_service import EmailService

logger = logging.getLogger(__name__)

REGISTRATION_OTP_EXPIRY_MINUTES = 5
MAX_OTP_ATTEMPTS = 3
VERIFICATION_VALID_MINUTES = 10  # How long verified_at is accepted for completing registration


class RegistrationOtpService:
    """OTP verification for patient registration (before account creation)."""

    @staticmethod
    def _generate_otp(length=6):
        return ''.join(random.choices(string.digits, k=length))

    @staticmethod
    def send_otp(email):
        """
        Generate OTP, store hashed, send email.
        Replaces any existing registration_otp for this email.
        Returns (True, None) on success, (False, error_message) on failure.
        """
        email = email.lower().strip()
        if not email:
            return False, "Email is required."

        # Do not send OTP if email is already registered
        existing_user = query_db('SELECT id FROM users WHERE email = ?', (email,), one=True)
        if existing_user:
            return False, "This email is already registered. Please sign in."

        otp = RegistrationOtpService._generate_otp()
        otp_hash = generate_password_hash(otp, method='pbkdf2:sha256')
        expires_at = (datetime.utcnow() + timedelta(minutes=REGISTRATION_OTP_EXPIRY_MINUTES)).strftime('%Y-%m-%d %H:%M:%S')

        execute_db('DELETE FROM registration_otp WHERE email = ?', (email,))
        execute_db(
            '''INSERT INTO registration_otp (email, otp_hash, expires_at, attempts, verified_at)
               VALUES (?, ?, ?, 0, NULL)''',
            (email, otp_hash, expires_at)
        )

        ok, send_err = EmailService.send_otp_email(email, otp)
        if not ok:
            # Dev fallback: print OTP to server console so you can test without fixing Gmail
            if current_app.debug and current_app.config.get('MAIL_DEBUG_OTP_TO_CONSOLE'):
                logger.warning("MAIL_DEBUG_OTP_TO_CONSOLE: OTP for %s is %s (email failed: %s)", email, otp, send_err)
                print(f"\n--- MedSync OTP for {email}: {otp} (valid 5 min) ---\n")
            else:
                execute_db('DELETE FROM registration_otp WHERE email = ?', (email,))
                return False, send_err or "Failed to send verification email. Please try again."

        logger.info(f"Registration OTP sent to {email}")
        return True, None

    @staticmethod
    def verify_otp(email, otp_code):
        """
        Verify OTP for the given email.
        Returns (True, None) on success, (False, error_message) on failure.
        On success, sets verified_at so registration can proceed.
        """
        email = email.lower().strip()
        otp_code = (otp_code or '').strip()
        if not email or not otp_code or len(otp_code) != 6 or not otp_code.isdigit():
            return False, "Please enter a valid 6-digit code."

        record = query_db(
            'SELECT id, otp_hash, expires_at, attempts FROM registration_otp WHERE email = ?',
            (email,), one=True
        )
        if not record:
            return False, "No verification code found for this email. Please request a new code."

        if record['attempts'] >= MAX_OTP_ATTEMPTS:
            return False, "Too many failed attempts. Please request a new verification code."

        try:
            expires_dt = datetime.strptime(record['expires_at'], '%Y-%m-%d %H:%M:%S')
        except (ValueError, TypeError):
            return False, "Verification code has expired. Please request a new code."

        if datetime.utcnow() > expires_dt:
            return False, "Verification code has expired. Please request a new code."

        if not check_password_hash(record['otp_hash'], otp_code):
            execute_db(
                'UPDATE registration_otp SET attempts = attempts + 1 WHERE id = ?',
                (record['id'],)
            )
            remaining = MAX_OTP_ATTEMPTS - record['attempts'] - 1
            if remaining <= 0:
                return False, "Too many failed attempts. Please request a new verification code."
            return False, f"Invalid code. {remaining} attempt(s) remaining."

        verified_at = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        execute_db(
            'UPDATE registration_otp SET verified_at = ? WHERE id = ?',
            (verified_at, record['id'])
        )
        logger.info(f"Registration OTP verified for {email}")
        return True, None

    @staticmethod
    def is_email_verified_for_registration(email):
        """
        Check if this email has successfully verified OTP and verified_at is still within validity window.
        """
        email = email.lower().strip()
        record = query_db(
            'SELECT verified_at FROM registration_otp WHERE email = ? AND verified_at IS NOT NULL',
            (email,), one=True
        )
        if not record or not record['verified_at']:
            return False
        try:
            verified_dt = datetime.strptime(record['verified_at'], '%Y-%m-%d %H:%M:%S')
        except (ValueError, TypeError):
            return False
        return datetime.utcnow() <= verified_dt + timedelta(minutes=VERIFICATION_VALID_MINUTES)

    @staticmethod
    def clear_after_registration(email):
        """Remove registration OTP record after successful account creation."""
        email = email.lower().strip()
        execute_db('DELETE FROM registration_otp WHERE email = ?', (email,))
