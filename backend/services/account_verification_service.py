import uuid
import random
import string
from datetime import datetime, timedelta
from backend.utils.database import query_db, execute_db
from backend.services.email_service import EmailService

class AccountVerificationService:
    @staticmethod
    def create_verification(user_id, email):
        token = str(uuid.uuid4())
        
        # Invalidate any existing tokens for this user
        execute_db('DELETE FROM account_verifications WHERE user_id = ?', (user_id,))
        
        # Store token with no OTP yet
        execute_db(
            '''INSERT INTO account_verifications (user_id, token)
               VALUES (?, ?)''',
            (user_id, token)
        )
        
        # Build link
        # Ideally get base URL dynamically or from config, hardcoding for now as usually localhost:5000 in dev
        link = f"http://localhost:5000/api/auth/verify-email/{token}"
        EmailService.send_verification_email(email, link)
        return token

    @staticmethod
    def verify_token_and_send_otp(token):
        """
        Validates the email link token.
        If valid, generates OTP, sends it, and returns the email (to show on frontend).
        """
        record = query_db(
            '''SELECT av.id, u.email, av.user_id 
               FROM account_verifications av
               JOIN users u ON av.user_id = u.id
               WHERE av.token = ?''',
            (token,), one=True
        )
        
        if not record:
            return None, "Invalid verification link."

        # Generate OTP
        otp = ''.join(random.choices(string.digits, k=6))
        expires_at = (datetime.now() + timedelta(minutes=5)).strftime('%Y-%m-%d %H:%M:%S')

        # Update record with OTP
        execute_db(
            '''UPDATE account_verifications 
               SET otp_code = ?, expires_at = ?, attempts = 0
               WHERE id = ?''',
            (otp, expires_at, record['id'])
        )

        # Send OTP
        EmailService.send_otp_email(record['email'], otp)
        
        return record['email'], None

    @staticmethod
    def verify_otp(email, otp_code):
        user = query_db('SELECT id FROM users WHERE email = ?', (email,), one=True)
        if not user:
            return False, "User not found."

        record = query_db(
            '''SELECT * FROM account_verifications 
               WHERE user_id = ? AND otp_code = ?''',
            (user['id'], otp_code), one=True
        )
        
        if not record:
            return False, "Invalid OTP."
        
        # Check attempts
        if record['attempts'] >= 3:
            return False, "Too many failed attempts. Please request a new verification link."
            
        # Check expiry
        if datetime.now() > datetime.strptime(record['expires_at'], '%Y-%m-%d %H:%M:%S'):
             return False, "OTP expired."

        # Success - Mark user as verified
        execute_db('UPDATE users SET is_verified = 1 WHERE id = ?', (user['id'],))
        
        # Clean up verification record
        execute_db('DELETE FROM account_verifications WHERE id = ?', (record['id'],))
        
        return True, "Verification successful."

    @staticmethod
    def increment_attempts(email):
        user = query_db('SELECT id FROM users WHERE email = ?', (email,), one=True)
        if user:
            execute_db(
                '''UPDATE account_verifications 
                   SET attempts = attempts + 1 
                   WHERE user_id = ?''', 
                (user['id'],)
            )
