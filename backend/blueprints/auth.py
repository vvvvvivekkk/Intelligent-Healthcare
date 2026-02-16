from flask import Blueprint, request, session
from backend.services.auth_service import AuthService
from backend.utils.helpers import (
    success_response, error_response, login_required,
    validate_required_fields
)

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')


@auth_bp.route('/register/patient', methods=['POST'])
def register_patient():
    """Register a new patient."""
    data = request.get_json()
    if not data:
        return error_response('Request body required')

    valid, msg = validate_required_fields(data, ['full_name', 'email', 'password'])
    if not valid:
        return error_response(msg)

    if len(data['password']) < 6:
        return error_response('Password must be at least 6 characters')

    user, err = AuthService.register_patient(
        full_name=data['full_name'],
        email=data['email'].lower().strip(),
        password=data['password'],
        phone=data.get('phone')
    )

    if err:
        return error_response(err)

    return success_response(user, 'Registration successful', 201)


@auth_bp.route('/register/doctor', methods=['POST'])
def register_doctor():
    """Register a new doctor."""
    data = request.get_json()
    if not data:
        return error_response('Request body required')

    valid, msg = validate_required_fields(
        data, ['full_name', 'email', 'password', 'specialization']
    )
    if not valid:
        return error_response(msg)

    doctor, err = AuthService.register_doctor(
        full_name=data['full_name'],
        email=data['email'].lower().strip(),
        password=data['password'],
        specialization=data['specialization'],
        experience_years=data.get('experience_years', 0),
        hospital=data.get('hospital'),
        phone=data.get('phone'),
        bio=data.get('bio')
    )

    if err:
        return error_response(err)

    return success_response(doctor, 'Doctor registration successful', 201)


@auth_bp.route('/login/patient', methods=['POST'])
def login_patient():
    """Patient login."""
    data = request.get_json()
    if not data:
        return error_response('Request body required')

    valid, msg = validate_required_fields(data, ['email', 'password'])
    if not valid:
        return error_response(msg)

    user, err = AuthService.login_patient(
        data['email'].lower().strip(),
        data['password']
    )

    if err:
        return error_response(err, 401)

    session.clear()
    session['user_id'] = user['id']
    session['patient_id'] = user['patient_id']
    session['role'] = 'patient'
    session['full_name'] = user['full_name']
    session.permanent = True

    return success_response(user, 'Login successful')


@auth_bp.route('/login/doctor', methods=['POST'])
def login_doctor():
    """Doctor login."""
    data = request.get_json()
    if not data:
        return error_response('Request body required')

    valid, msg = validate_required_fields(data, ['email', 'password'])
    if not valid:
        return error_response(msg)

    doctor, err = AuthService.login_doctor(
        data['email'].lower().strip(),
        data['password']
    )

    if err:
        return error_response(err, 401)

    session.clear()
    session['doctor_id'] = doctor['id']
    session['doctor_code'] = doctor['doctor_id']
    session['role'] = 'doctor'
    session['full_name'] = doctor['full_name']
    session.permanent = True

    return success_response(doctor, 'Login successful')


@auth_bp.route('/logout', methods=['POST'])
def logout():
    """Logout current user."""
    session.clear()
    return success_response(message='Logged out successfully')


@auth_bp.route('/me', methods=['GET'])
@login_required
def get_current_user():
    """Get current user profile."""
    if session.get('role') == 'patient':
        user = AuthService.get_patient_by_id(session['user_id'])
        if user:
            return success_response(user)
    elif session.get('role') == 'doctor':
        doctor = AuthService.get_doctor_by_id(session['doctor_id'])
        if doctor:
            return success_response(doctor)

    return error_response('User not found', 404)


@auth_bp.route('/session', methods=['GET'])
def check_session():
    """Check if user has active session."""
    if 'user_id' in session:
        return success_response({
            'authenticated': True,
            'role': session.get('role'),
            'full_name': session.get('full_name'),
            'user_id': session.get('user_id'),
            'patient_id': session.get('patient_id')
        })
    elif 'doctor_id' in session:
        from backend.services.doctor_service import DoctorService
        doc_info = DoctorService.get_doctor_profile(session.get('doctor_id'))
        data = {
            'authenticated': True,
            'role': session.get('role'),
            'full_name': session.get('full_name'),
            'doctor_id': session.get('doctor_id'),
            'doctor_code': session.get('doctor_code')
        }
        if doc_info:
            data['specialization'] = doc_info.get('specialization')
            data['hospital'] = doc_info.get('hospital')
            data['experience_years'] = doc_info.get('experience_years')
            data['bio'] = doc_info.get('bio')
        return success_response(data)
    
    return success_response({'authenticated': False})
