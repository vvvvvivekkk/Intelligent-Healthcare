import uuid
import logging
from backend.utils.database import query_db, execute_db, get_db

logger = logging.getLogger(__name__)


class AppointmentService:
    """Service layer for appointment and slot management."""

    @staticmethod
    def generate_appointment_id():
        return f"APT-{uuid.uuid4().hex[:8].upper()}"

    # ─── Slot Management ─────────────────────────────────────

    @staticmethod
    def add_slot(doctor_id, slot_date, start_time, end_time):
        """Add a new availability slot for a doctor."""
        # Check for overlapping slots
        overlap = query_db(
            '''SELECT id FROM slots 
               WHERE doctor_id = ? AND slot_date = ?
               AND ((start_time < ? AND end_time > ?) OR
                    (start_time < ? AND end_time > ?) OR
                    (start_time >= ? AND end_time <= ?))''',
            (doctor_id, slot_date, end_time, start_time,
             end_time, start_time, start_time, end_time),
            one=True
        )
        if overlap:
            return None, 'Slot overlaps with existing slot'

        try:
            slot_id = execute_db(
                '''INSERT INTO slots (doctor_id, slot_date, start_time, end_time, is_booked)
                   VALUES (?, ?, ?, ?, 0)''',
                (doctor_id, slot_date, start_time, end_time)
            )
            slot = query_db('SELECT * FROM slots WHERE id = ?', (slot_id,), one=True)
            return dict(slot), None
        except Exception as e:
            logger.error(f"Add slot error: {e}")
            return None, 'Failed to add slot'

    @staticmethod
    def update_slot(slot_id, doctor_id, slot_date=None, start_time=None, end_time=None):
        """Update an existing slot."""
        slot = query_db('SELECT * FROM slots WHERE id = ? AND doctor_id = ?',
                       (slot_id, doctor_id), one=True)
        if not slot:
            return None, 'Slot not found'
        if slot['is_booked']:
            return None, 'Cannot edit a booked slot'

        new_date = slot_date or slot['slot_date']
        new_start = start_time or slot['start_time']
        new_end = end_time or slot['end_time']

        # Check overlaps excluding current slot
        overlap = query_db(
            '''SELECT id FROM slots 
               WHERE doctor_id = ? AND slot_date = ? AND id != ?
               AND ((start_time < ? AND end_time > ?) OR
                    (start_time < ? AND end_time > ?) OR
                    (start_time >= ? AND end_time <= ?))''',
            (doctor_id, new_date, slot_id, new_end, new_start,
             new_end, new_start, new_start, new_end),
            one=True
        )
        if overlap:
            return None, 'Updated slot would overlap with existing slot'

        execute_db(
            'UPDATE slots SET slot_date = ?, start_time = ?, end_time = ? WHERE id = ?',
            (new_date, new_start, new_end, slot_id)
        )
        updated = query_db('SELECT * FROM slots WHERE id = ?', (slot_id,), one=True)
        return dict(updated), None

    @staticmethod
    def delete_slot(slot_id, doctor_id):
        """Delete a slot."""
        slot = query_db('SELECT * FROM slots WHERE id = ? AND doctor_id = ?',
                       (slot_id, doctor_id), one=True)
        if not slot:
            return False, 'Slot not found'
        if slot['is_booked']:
            return False, 'Cannot delete a booked slot'

        execute_db('DELETE FROM slots WHERE id = ?', (slot_id,))
        return True, None

    @staticmethod
    def get_doctor_slots(doctor_id, date=None, available_only=False):
        """Get slots for a doctor."""
        query = 'SELECT * FROM slots WHERE doctor_id = ?'
        params = [doctor_id]

        if date:
            query += ' AND slot_date = ?'
            params.append(date)
        
        if available_only:
            query += ' AND is_booked = 0'
        
        query += ' ORDER BY slot_date, start_time'
        
        slots = query_db(query, tuple(params))
        return [dict(s) for s in slots]

    @staticmethod
    def get_available_slots(doctor_id, date=None):
        """Get available (unbooked) slots for a doctor."""
        return AppointmentService.get_doctor_slots(doctor_id, date, available_only=True)

    # ─── Appointment Management ───────────────────────────────

    @staticmethod
    def book_appointment(patient_id, doctor_id, slot_id, reason=None):
        """Book an appointment."""
        conn = get_db()
        try:
            # Check slot availability with row lock
            slot = conn.execute('SELECT * FROM slots WHERE id = ? AND is_booked = 0',
                              (slot_id,)).fetchone()
            if not slot:
                return None, 'Slot is no longer available'

            # Resolve doctor_id from slot if not provided
            if doctor_id is None:
                doctor_id = slot['doctor_id']
            elif slot['doctor_id'] != doctor_id:
                return None, 'Slot does not belong to this doctor'

            appointment_id = AppointmentService.generate_appointment_id()

            # Book the slot
            conn.execute('UPDATE slots SET is_booked = 1 WHERE id = ?', (slot_id,))

            # Create appointment
            conn.execute(
                '''INSERT INTO appointments (appointment_id, patient_id, doctor_id, slot_id, status, reason)
                   VALUES (?, ?, ?, ?, 'scheduled', ?)''',
                (appointment_id, patient_id, doctor_id, slot_id, reason)
            )

            conn.commit()

            appointment = conn.execute(
                '''SELECT a.*, s.slot_date, s.start_time, s.end_time,
                   d.full_name as doctor_name, d.specialization,
                   u.full_name as patient_name, u.patient_id as patient_code
                   FROM appointments a
                   JOIN slots s ON a.slot_id = s.id
                   JOIN doctors d ON a.doctor_id = d.id
                   JOIN users u ON a.patient_id = u.id
                   WHERE a.appointment_id = ?''',
                (appointment_id,)
            ).fetchone()

            return dict(appointment), None
        except Exception as e:
            conn.rollback()
            logger.error(f"Booking error: {e}")
            return None, 'Booking failed'
        finally:
            conn.close()

    @staticmethod
    def cancel_appointment(appointment_id, cancelled_by='patient'):
        """Cancel an appointment."""
        conn = get_db()
        try:
            apt = conn.execute(
                'SELECT * FROM appointments WHERE id = ? AND status = "scheduled"',
                (appointment_id,)
            ).fetchone()
            if not apt:
                return False, 'Appointment not found or cannot be cancelled'

            status = 'cancelled'
            conn.execute(
                'UPDATE appointments SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?',
                (status, appointment_id)
            )
            # Free up the slot
            conn.execute('UPDATE slots SET is_booked = 0 WHERE id = ?', (apt['slot_id'],))
            conn.commit()
            return True, None
        except Exception as e:
            conn.rollback()
            logger.error(f"Cancel error: {e}")
            return False, 'Cancellation failed'
        finally:
            conn.close()

    @staticmethod
    def emergency_cancel(appointment_id, doctor_id):
        """Emergency cancellation by doctor."""
        conn = get_db()
        try:
            apt = conn.execute(
                '''SELECT * FROM appointments 
                   WHERE id = ? AND doctor_id = ? AND status = "scheduled"''',
                (appointment_id, doctor_id)
            ).fetchone()
            if not apt:
                return False, None, 'Appointment not found'

            conn.execute(
                '''UPDATE appointments SET status = "emergency_cancelled", 
                   updated_at = CURRENT_TIMESTAMP WHERE id = ?''',
                (appointment_id,)
            )
            conn.execute('UPDATE slots SET is_booked = 0 WHERE id = ?', (apt['slot_id'],))
            conn.commit()
            return True, apt['patient_id'], None
        except Exception as e:
            conn.rollback()
            logger.error(f"Emergency cancel error: {e}")
            return False, None, 'Emergency cancellation failed'
        finally:
            conn.close()

    @staticmethod
    def reschedule_appointment(appointment_id, new_slot_id, patient_id):
        """Reschedule an appointment to a new slot."""
        conn = get_db()
        try:
            apt = conn.execute(
                '''SELECT * FROM appointments WHERE id = ? AND patient_id = ?
                   AND status IN ("scheduled", "emergency_cancelled")''',
                (appointment_id, patient_id)
            ).fetchone()
            if not apt:
                return None, 'Appointment not found or cannot be rescheduled'

            new_slot = conn.execute(
                'SELECT * FROM slots WHERE id = ? AND is_booked = 0',
                (new_slot_id,)
            ).fetchone()
            if not new_slot:
                return None, 'New slot is not available'

            # Free old slot
            conn.execute('UPDATE slots SET is_booked = 0 WHERE id = ?', (apt['slot_id'],))
            # Book new slot
            conn.execute('UPDATE slots SET is_booked = 1 WHERE id = ?', (new_slot_id,))
            # Update appointment
            conn.execute(
                '''UPDATE appointments SET slot_id = ?, status = "rescheduled",
                   updated_at = CURRENT_TIMESTAMP WHERE id = ?''',
                (new_slot_id, appointment_id)
            )
            conn.commit()

            updated = conn.execute(
                '''SELECT a.*, s.slot_date, s.start_time, s.end_time,
                   d.full_name as doctor_name, d.specialization
                   FROM appointments a
                   JOIN slots s ON a.slot_id = s.id
                   JOIN doctors d ON a.doctor_id = d.id
                   WHERE a.id = ?''',
                (appointment_id,)
            ).fetchone()
            return dict(updated), None
        except Exception as e:
            conn.rollback()
            logger.error(f"Reschedule error: {e}")
            return None, 'Rescheduling failed'
        finally:
            conn.close()

    @staticmethod
    def get_patient_appointments(patient_id, status=None):
        """Get appointments for a patient."""
        query = '''SELECT a.*, s.slot_date, s.start_time, s.end_time,
                   d.full_name as doctor_name, d.specialization, d.hospital,
                   d.doctor_id as doctor_code
                   FROM appointments a
                   JOIN slots s ON a.slot_id = s.id
                   JOIN doctors d ON a.doctor_id = d.id
                   WHERE a.patient_id = ?'''
        params = [patient_id]

        if status:
            query += ' AND a.status = ?'
            params.append(status)
        
        query += ' ORDER BY s.slot_date DESC, s.start_time DESC'
        
        appointments = query_db(query, tuple(params))
        return [dict(a) for a in appointments]

    @staticmethod
    def get_doctor_appointments(doctor_id, status=None):
        """Get appointments for a doctor."""
        query = '''SELECT a.*, s.slot_date, s.start_time, s.end_time,
                   u.full_name as patient_name, u.patient_id as patient_code,
                   u.email as patient_email, u.phone as patient_phone
                   FROM appointments a
                   JOIN slots s ON a.slot_id = s.id
                   JOIN users u ON a.patient_id = u.id
                   WHERE a.doctor_id = ?'''
        params = [doctor_id]

        if status:
            query += ' AND a.status = ?'
            params.append(status)
        
        query += ' ORDER BY s.slot_date DESC, s.start_time DESC'
        
        appointments = query_db(query, tuple(params))
        return [dict(a) for a in appointments]

    @staticmethod
    def update_appointment_status(appointment_id, status):
        """Update appointment status."""
        valid = ['scheduled', 'completed', 'cancelled', 'emergency_cancelled', 
                 'rescheduled', 'otp_pending']
        if status not in valid:
            return False, 'Invalid status'
        
        execute_db(
            'UPDATE appointments SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?',
            (status, appointment_id)
        )
        return True, None

    @staticmethod
    def get_appointment_by_id(appointment_id):
        """Get appointment details."""
        apt = query_db(
            '''SELECT a.*, s.slot_date, s.start_time, s.end_time,
               d.full_name as doctor_name, d.specialization, d.hospital,
               u.full_name as patient_name, u.patient_id as patient_code
               FROM appointments a
               JOIN slots s ON a.slot_id = s.id
               JOIN doctors d ON a.doctor_id = d.id
               JOIN users u ON a.patient_id = u.id
               WHERE a.id = ?''',
            (appointment_id,), one=True
        )
        return dict(apt) if apt else None
