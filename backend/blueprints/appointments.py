from flask import Blueprint, request, session
from backend.services.appointment_service import AppointmentService
from backend.services.notification_service import NotificationService
from backend.services.otp_service import OTPService
from backend.utils.helpers import (
    success_response, error_response, login_required,
    patient_required, doctor_required, validate_required_fields
)

appointments_bp = Blueprint('appointments', __name__, url_prefix='/api/appointments')


# ─── Slot Management (Doctor) ────────────────────────────────

@appointments_bp.route('/slots', methods=['POST'])
@doctor_required
def add_slot():
    """Add a new availability slot."""
    data = request.get_json()
    valid, msg = validate_required_fields(data, ['slot_date', 'start_time', 'end_time'])
    if not valid:
        return error_response(msg)

    slot, err = AppointmentService.add_slot(
        doctor_id=session['doctor_id'],
        slot_date=data['slot_date'],
        start_time=data['start_time'],
        end_time=data['end_time']
    )

    if err:
        return error_response(err)
    return success_response(slot, 'Slot added successfully', 201)


@appointments_bp.route('/slots/<int:slot_id>', methods=['PUT'])
@doctor_required
def update_slot(slot_id):
    """Update a slot."""
    data = request.get_json()
    slot, err = AppointmentService.update_slot(
        slot_id=slot_id,
        doctor_id=session['doctor_id'],
        slot_date=data.get('slot_date'),
        start_time=data.get('start_time'),
        end_time=data.get('end_time')
    )

    if err:
        return error_response(err)
    return success_response(slot, 'Slot updated')


@appointments_bp.route('/slots/<int:slot_id>', methods=['DELETE'])
@doctor_required
def delete_slot(slot_id):
    """Delete a slot."""
    success, err = AppointmentService.delete_slot(slot_id, session['doctor_id'])
    if err:
        return error_response(err)
    return success_response(message='Slot deleted')


@appointments_bp.route('/slots/doctor', methods=['GET'])
@doctor_required
def get_my_slots():
    """Get current doctor's slots."""
    date = request.args.get('date')
    slots = AppointmentService.get_doctor_slots(session['doctor_id'], date)
    return success_response(slots)


@appointments_bp.route('/slots/doctor/<int:doctor_id>', methods=['GET'])
@login_required
def get_doctor_slots(doctor_id):
    """Get available slots for a specific doctor."""
    date = request.args.get('date')
    slots = AppointmentService.get_available_slots(doctor_id, date)
    return success_response(slots)


# ─── Appointment Booking ─────────────────────────────────────

@appointments_bp.route('/book', methods=['POST'])
@patient_required
def book_appointment():
    """Book an appointment."""
    data = request.get_json()
    valid, msg = validate_required_fields(data, ['slot_id'])
    if not valid:
        return error_response(msg)

    # doctor_id is optional — will be resolved from slot if not provided
    doctor_id = data.get('doctor_id')

    appointment, err = AppointmentService.book_appointment(
        patient_id=session['user_id'],
        doctor_id=doctor_id,
        slot_id=data['slot_id'],
        reason=data.get('reason')
    )

    if err:
        return error_response(err)

    # Send notifications
    NotificationService.send_booking_notification(
        appointment, session['user_id'], appointment['doctor_id']
    )

    return success_response(appointment, 'Appointment booked successfully', 201)


@appointments_bp.route('/<int:appointment_id>/cancel', methods=['POST'])
@login_required
def cancel_appointment(appointment_id):
    """Cancel an appointment."""
    role = session.get('role')
    cancelled_by = role if role in ('patient', 'doctor') else 'patient'

    apt = AppointmentService.get_appointment_by_id(appointment_id)
    if not apt:
        return error_response('Appointment not found', 404)

    success, err = AppointmentService.cancel_appointment(appointment_id, cancelled_by)
    if err:
        return error_response(err)

    NotificationService.send_cancellation_notification(
        apt,
        apt['patient_id'] if isinstance(apt['patient_id'], int) else session.get('user_id'),
        apt['doctor_id'] if isinstance(apt['doctor_id'], int) else session.get('doctor_id'),
        cancelled_by
    )

    return success_response(message='Appointment cancelled')


@appointments_bp.route('/<int:appointment_id>/emergency-cancel', methods=['POST'])
@doctor_required
def emergency_cancel(appointment_id):
    """Emergency cancel by doctor."""
    success, patient_id, err = AppointmentService.emergency_cancel(
        appointment_id, session['doctor_id']
    )
    if err:
        return error_response(err)

    NotificationService.send_emergency_notification(patient_id, appointment_id)

    return success_response(message='Emergency cancellation processed')


@appointments_bp.route('/<int:appointment_id>/reschedule', methods=['POST'])
@patient_required
def reschedule_appointment(appointment_id):
    """Reschedule an appointment."""
    data = request.get_json()
    valid, msg = validate_required_fields(data, ['new_slot_id'])
    if not valid:
        return error_response(msg)

    appointment, err = AppointmentService.reschedule_appointment(
        appointment_id, data['new_slot_id'], session['user_id']
    )

    if err:
        return error_response(err)
    return success_response(appointment, 'Appointment rescheduled')


# ─── Appointment Viewing ─────────────────────────────────────

@appointments_bp.route('/patient', methods=['GET'])
@patient_required
def get_patient_appointments():
    """Get current patient's appointments."""
    status = request.args.get('status')
    appointments = AppointmentService.get_patient_appointments(session['user_id'], status)
    return success_response(appointments)


@appointments_bp.route('/doctor', methods=['GET'])
@doctor_required
def get_doctor_appointments():
    """Get current doctor's appointments."""
    status = request.args.get('status')
    appointments = AppointmentService.get_doctor_appointments(session['doctor_id'], status)
    return success_response(appointments)


@appointments_bp.route('/<int:appointment_id>', methods=['GET'])
@login_required
def get_appointment(appointment_id):
    """Get appointment details."""
    apt = AppointmentService.get_appointment_by_id(appointment_id)
    if not apt:
        return error_response('Appointment not found', 404)
    return success_response(apt)


@appointments_bp.route('/<int:appointment_id>/status', methods=['PUT'])
@doctor_required
def update_status(appointment_id):
    """Update appointment status (doctor only)."""
    data = request.get_json()
    status = data.get('status')
    if not status:
        return error_response('Status required')

    success, err = AppointmentService.update_appointment_status(appointment_id, status)
    if err:
        return error_response(err)
    return success_response(message='Status updated')


# ─── OTP Management ──────────────────────────────────────────

@appointments_bp.route('/<int:appointment_id>/otp/generate', methods=['POST'])
@login_required
def generate_otp(appointment_id):
    """Generate OTP for consultation."""
    apt = AppointmentService.get_appointment_by_id(appointment_id)
    if not apt:
        return error_response('Appointment not found', 404)

    otp = OTPService.create_otp(appointment_id)

    # Send OTP notification
    NotificationService.create_notification(
        recipient_type='patient',
        title='Consultation OTP',
        message=f'Your OTP for consultation is: {otp}. Valid for 10 minutes.',
        notification_type='otp',
        user_id=apt['patient_id'],
        appointment_id=appointment_id
    )

    return success_response({'otp': otp}, 'OTP generated and sent')


@appointments_bp.route('/<int:appointment_id>/otp/verify', methods=['POST'])
@login_required
def verify_otp(appointment_id):
    """Verify OTP for consultation."""
    data = request.get_json()
    otp_code = data.get('otp')
    if not otp_code:
        return error_response('OTP required')

    success, msg = OTPService.verify_otp(appointment_id, otp_code)
    if not success:
        return error_response(msg)

    return success_response(message=msg)


# ─── Notifications ────────────────────────────────────────────

@appointments_bp.route('/notifications', methods=['GET'])
@login_required
def get_notifications():
    """Get notifications for current user."""
    unread = request.args.get('unread', 'false').lower() == 'true'

    if session.get('role') == 'patient':
        notifs = NotificationService.get_patient_notifications(session['user_id'], unread)
        count = NotificationService.get_unread_count(user_id=session['user_id'])
    else:
        notifs = NotificationService.get_doctor_notifications(session['doctor_id'], unread)
        count = NotificationService.get_unread_count(doctor_id=session['doctor_id'])

    return success_response({'notifications': notifs, 'unread_count': count})


@appointments_bp.route('/notifications/<int:notif_id>/read', methods=['POST'])
@login_required
def mark_notification_read(notif_id):
    """Mark notification as read."""
    NotificationService.mark_as_read(notif_id)
    return success_response(message='Notification marked as read')


@appointments_bp.route('/notifications/read-all', methods=['POST'])
@login_required
def mark_all_notifications_read():
    """Mark all notifications as read."""
    if session.get('role') == 'patient':
        NotificationService.mark_all_read(user_id=session['user_id'])
    else:
        NotificationService.mark_all_read(doctor_id=session['doctor_id'])
    return success_response(message='All notifications marked as read')
