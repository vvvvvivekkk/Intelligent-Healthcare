from flask_mail import Message
from flask import current_app
from backend import mail
import logging

logger = logging.getLogger(__name__)


class EmailService:
    """
    Sends email synchronously so callers get accurate success/failure.
    Returns (True, None) on success, (False, error_message) on failure.
    """

    @staticmethod
    def _is_configured():
        """Check if mail credentials are set."""
        c = current_app.config
        return bool(c.get('MAIL_USERNAME') and c.get('MAIL_PASSWORD'))

    @staticmethod
    def send_email(subject, recipients, body=None, html=None):
        """
        Send email. Returns (True, None) on success, (False, error_message) on failure.
        """
        if not EmailService._is_configured():
            logger.warning("Email not configured: set GMAIL_SENDER and GMAIL_PASSWORD in .env")
            return False, "Email service is not configured. Set GMAIL_SENDER and GMAIL_PASSWORD in .env"

        if not recipients:
            return False, "No recipients"

        try:
            msg = Message(subject, recipients=recipients)
            if body:
                msg.body = body
            if html:
                msg.html = html
            if not msg.body and not msg.html:
                msg.body = "(No content)"
            mail.send(msg)
            logger.info(f"Email sent to {recipients}")
            return True, None
        except Exception as e:
            logger.exception("Failed to send email: %s", e)
            err = str(e).strip()
            if "Authentication failed" in err or "Username and Password not accepted" in err:
                return False, "Invalid email credentials. Use a Gmail App Password if 2FA is on."
            if "Connection" in err or "refused" in err.lower():
                return False, "Could not connect to mail server. Check network and MAIL_SERVER/MAIL_PORT."
            return False, f"Failed to send email: {err[:100]}"

    @staticmethod
    def send_verification_email(email, link):
        subject = "Verify your MedSync AI Account"
        body = f"Verify your account: {link}"
        html = f"""
        <h3>Welcome to MedSync AI</h3>
        <p>Please click the link below to verify your email address:</p>
        <p><a href="{link}">Verify Account</a></p>
        <p>This link will expire in 24 hours.</p>
        """
        return EmailService.send_email(subject, [email], body=body, html=html)

    @staticmethod
    def send_otp_email(email, otp):
        subject = "Your MedSync AI Verification Code"
        body = f"Your verification code is: {otp}. It expires in 5 minutes."
        html = f"""
        <h3>MedSync AI Verification</h3>
        <p>Your verification code is:</p>
        <h2 style="letter-spacing:4px">{otp}</h2>
        <p>This code expires in 5 minutes.</p>
        """
        return EmailService.send_email(subject, [email], body=body, html=html)
