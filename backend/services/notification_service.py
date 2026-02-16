import logging
from datetime import datetime, timedelta
from backend.utils.database import query_db, execute_db

logger = logging.getLogger(__name__)


class NotificationService:
    """Service layer for notification management."""

    @staticmethod
    def create_notification(recipient_type, title, message, notification_type='info',
                           user_id=None, doctor_id=None, appointment_id=None):
        """Create a new notification."""
        try:
            notif_id = execute_db(
                '''INSERT INTO notifications 
                   (user_id, doctor_id, recipient_type, title, message, 
                    notification_type, is_read, related_appointment_id)
                   VALUES (?, ?, ?, ?, ?, ?, 0, ?)''',
                (user_id, doctor_id, recipient_type, title, message,
                 notification_type, appointment_id)
            )
            return notif_id
        except Exception as e:
            logger.error(f"Create notification error: {e}")
            return None

    @staticmethod
    def get_patient_notifications(user_id, unread_only=False):
        """Get notifications for a patient."""
        query = '''SELECT * FROM notifications WHERE user_id = ? AND recipient_type = "patient"'''
        params = [user_id]
        if unread_only:
            query += ' AND is_read = 0'
        query += ' ORDER BY created_at DESC LIMIT 50'
        
        notifs = query_db(query, tuple(params))
        return [dict(n) for n in notifs]

    @staticmethod
    def get_doctor_notifications(doctor_id, unread_only=False):
        """Get notifications for a doctor."""
        query = '''SELECT * FROM notifications WHERE doctor_id = ? AND recipient_type = "doctor"'''
        params = [doctor_id]
        if unread_only:
            query += ' AND is_read = 0'
        query += ' ORDER BY created_at DESC LIMIT 50'
        
        notifs = query_db(query, tuple(params))
        return [dict(n) for n in notifs]

    @staticmethod
    def mark_as_read(notification_id):
        """Mark a notification as read."""
        execute_db('UPDATE notifications SET is_read = 1 WHERE id = ?', (notification_id,))

    @staticmethod
    def mark_all_read(user_id=None, doctor_id=None):
        """Mark all notifications as read for a user."""
        if user_id:
            execute_db(
                'UPDATE notifications SET is_read = 1 WHERE user_id = ? AND recipient_type = "patient"',
                (user_id,)
            )
        elif doctor_id:
            execute_db(
                'UPDATE notifications SET is_read = 1 WHERE doctor_id = ? AND recipient_type = "doctor"',
                (doctor_id,)
            )

    @staticmethod
    def get_unread_count(user_id=None, doctor_id=None):
        """Count unread notifications."""
        if user_id:
            result = query_db(
                'SELECT COUNT(*) as count FROM notifications WHERE user_id = ? AND is_read = 0 AND recipient_type = "patient"',
                (user_id,), one=True
            )
        elif doctor_id:
            result = query_db(
                'SELECT COUNT(*) as count FROM notifications WHERE doctor_id = ? AND is_read = 0 AND recipient_type = "doctor"',
                (doctor_id,), one=True
            )
        else:
            return 0
        return result['count'] if result else 0

    @staticmethod
    def send_appointment_reminder(appointment):
        """Send appointment reminder notification (simulated)."""
        NotificationService.create_notification(
            recipient_type='patient',
            title='Appointment Reminder',
            message=f"Reminder: Your appointment with Dr. {appointment.get('doctor_name', 'Unknown')} "
                    f"is in 30 minutes at {appointment.get('start_time', '')}.",
            notification_type='reminder',
            user_id=appointment.get('patient_id'),
            appointment_id=appointment.get('id')
        )

    @staticmethod
    def send_booking_notification(appointment, patient_id, doctor_id):
        """Send booking confirmation notifications."""
        # Notify patient
        NotificationService.create_notification(
            recipient_type='patient',
            title='Appointment Booked',
            message=f"Your appointment has been confirmed for "
                    f"{appointment.get('slot_date', '')} at {appointment.get('start_time', '')}.",
            notification_type='booking',
            user_id=patient_id,
            appointment_id=appointment.get('id')
        )
        # Notify doctor
        NotificationService.create_notification(
            recipient_type='doctor',
            title='New Appointment',
            message=f"A new appointment has been booked for "
                    f"{appointment.get('slot_date', '')} at {appointment.get('start_time', '')}.",
            notification_type='booking',
            doctor_id=doctor_id,
            appointment_id=appointment.get('id')
        )

    @staticmethod
    def send_cancellation_notification(appointment, patient_id, doctor_id, cancelled_by='patient'):
        """Send cancellation notifications."""
        if cancelled_by == 'patient':
            NotificationService.create_notification(
                recipient_type='doctor',
                title='Appointment Cancelled',
                message=f"An appointment on {appointment.get('slot_date', '')} has been cancelled by the patient.",
                notification_type='cancellation',
                doctor_id=doctor_id,
                appointment_id=appointment.get('id')
            )
        else:
            NotificationService.create_notification(
                recipient_type='patient',
                title='Appointment Cancelled',
                message=f"Your appointment on {appointment.get('slot_date', '')} has been cancelled by the doctor.",
                notification_type='cancellation',
                user_id=patient_id,
                appointment_id=appointment.get('id')
            )

    @staticmethod
    def send_emergency_notification(patient_id, appointment_id):
        """Send emergency cancellation notification to patient."""
        NotificationService.create_notification(
            recipient_type='patient',
            title='Emergency: Appointment Cancelled',
            message='Your appointment has been cancelled due to an emergency. '
                    'Please reschedule at your earliest convenience.',
            notification_type='emergency',
            user_id=patient_id,
            appointment_id=appointment_id
        )

    @staticmethod
    def check_upcoming_reminders():
        """Check and send reminders for upcoming appointments (background task placeholder)."""
        reminder_time = (datetime.now() + timedelta(minutes=30)).strftime('%H:%M')
        today = datetime.now().strftime('%Y-%m-%d')
        
        upcoming = query_db(
            '''SELECT a.*, s.slot_date, s.start_time, s.end_time,
               d.full_name as doctor_name
               FROM appointments a
               JOIN slots s ON a.slot_id = s.id
               JOIN doctors d ON a.doctor_id = d.id
               WHERE a.status = "scheduled" AND s.slot_date = ? AND s.start_time <= ?''',
            (today, reminder_time)
        )
        
        for apt in upcoming:
            NotificationService.send_appointment_reminder(dict(apt))
        
        return len(upcoming)
