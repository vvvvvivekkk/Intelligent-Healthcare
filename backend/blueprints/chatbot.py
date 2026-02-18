from flask import Blueprint, request, session
from backend.services.chatbot_service import ChatbotService
from backend.services.doctor_service import DoctorService
from backend.services.appointment_service import AppointmentService
from backend.services.notification_service import NotificationService
from backend.services.otp_service import OTPService
from backend.utils.helpers import (
    success_response, error_response, patient_required
)

chatbot_bp = Blueprint('chatbot', __name__, url_prefix='/api/chatbot')


@chatbot_bp.route('/message', methods=['POST'])
@patient_required
def send_message():
    """Send a message to the AI chatbot."""
    data = request.get_json()
    if not data or not data.get('message', '').strip():
        return error_response('Message required')

    user_id = session['user_id']
    session_id = data.get('session_id') or ChatbotService.get_or_create_session(user_id)

    response, parsed_data, ai_error = ChatbotService.process_message(
        user_id, session_id, data['message'].strip()
    )

    result = {
        'response': response,
        'session_id': session_id
    }

    if parsed_data:
        # Only include full analysis card if structured data (diseases/advice) is present
        if 'possible_diseases' in parsed_data:
            result['analysis'] = parsed_data

        # Auto-recommend doctors based on specialization (works for both JSON and tag)
        spec = parsed_data.get('recommended_specialization', '')
        if spec:
            doctors = DoctorService.get_doctors_by_specialization(spec)
            if not doctors:
                doctors = DoctorService.search_doctors(spec, 'specialization')
            result['recommended_doctors'] = doctors

    if ai_error:
        result['ai_error'] = ai_error

    return success_response(result)


@chatbot_bp.route('/history', methods=['GET'])
@patient_required
def get_history():
    """Get chat history."""
    user_id = session['user_id']
    session_id = request.args.get('session_id')
    limit = request.args.get('limit', 50, type=int)

    history = ChatbotService.get_chat_history(user_id, session_id, limit)
    return success_response(history)


@chatbot_bp.route('/sessions', methods=['GET'])
@patient_required
def get_sessions():
    """Get all chat sessions."""
    user_id = session['user_id']
    sessions = ChatbotService.get_all_sessions(user_id)
    return success_response(sessions)


@chatbot_bp.route('/new-session', methods=['POST'])
@patient_required
def new_session():
    """Start a new chat session."""
    session_id = ChatbotService.create_new_session()
    return success_response({'session_id': session_id}, 'New session created')


@chatbot_bp.route('/book-from-chat', methods=['POST'])
@patient_required
def book_from_chat():
    """Book an appointment directly from chatbot recommendation."""
    data = request.get_json()
    if not data:
        return error_response('Request body required')

    doctor_id = data.get('doctor_id')
    slot_id = data.get('slot_id')
    reason = data.get('reason', 'AI-recommended consultation')

    if not doctor_id or not slot_id:
        return error_response('Doctor ID and slot ID required')

    appointment, err = AppointmentService.book_appointment(
        patient_id=session['user_id'],
        doctor_id=doctor_id,
        slot_id=slot_id,
        reason=reason
    )

    if err:
        return error_response(err)

    NotificationService.send_booking_notification(
        appointment, session['user_id'], doctor_id
    )

    # Auto-generate OTP at booking time (valid for 24 hours)
    otp_code = OTPService.create_otp(
        appointment['id'], expiry_minutes=1440, update_status=False
    )
    NotificationService.create_notification(
        recipient_type='patient',
        title='🔐 Consultation OTP',
        message=f"Your verification OTP for appointment on "
                f"{appointment.get('slot_date', '')} at {appointment.get('start_time', '')} "
                f"is: {otp_code}. Share this with your doctor during consultation.",
        notification_type='otp',
        user_id=session['user_id'],
        appointment_id=appointment['id']
    )
    appointment['otp_code'] = otp_code

    return success_response(appointment, 'Appointment booked from chatbot', 201)


@chatbot_bp.route('/doctor-slots/<int:doctor_id>', methods=['GET'])
@patient_required
def get_doctor_slots_for_chat(doctor_id):
    """Get ALL slots for a doctor (both available and booked) so UI can show booked ones as unavailable."""
    date = request.args.get('date')
    # Return ALL slots — frontend will show booked slots as red/disabled
    slots = AppointmentService.get_doctor_slots(doctor_id, date, available_only=False)
    return success_response(slots)


@chatbot_bp.route('/specializations', methods=['GET'])
@patient_required
def get_specializations_for_chat():
    """Get all available specializations for booking flow."""
    specs = DoctorService.get_specializations()
    return success_response(specs)


@chatbot_bp.route('/doctors-by-spec', methods=['GET'])
@patient_required
def get_doctors_by_spec_for_chat():
    """Get doctors by specialization for booking flow."""
    spec = request.args.get('specialization', '')
    if not spec:
        return error_response('Specialization required')
    doctors = DoctorService.get_doctors_by_specialization(spec)
    if not doctors:
        doctors = DoctorService.search_doctors(spec, 'specialization')
    return success_response(doctors)
