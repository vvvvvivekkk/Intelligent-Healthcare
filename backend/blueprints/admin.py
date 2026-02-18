from flask import Blueprint, request, session
from backend.services.admin_service import AdminService
from backend.services.auth_service import AuthService
from backend.utils.helpers import success_response, error_response, admin_required, validate_required_fields

admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')


@admin_bp.route('/login', methods=['POST'])
def login_admin():
    """Admin login (separate from patient/doctor login)."""
    data = request.get_json()
    valid, msg = validate_required_fields(data, ['username', 'password'])
    if not valid:
        return error_response(msg)

    admin, err = AuthService.login_admin(data['username'], data['password'])
    if err:
        return error_response(err, 401)

    session.clear()
    session['admin_id'] = admin['id']
    session['username'] = admin['username']
    session['role'] = 'admin'
    session.permanent = True

    return success_response(admin, 'Admin login successful')


@admin_bp.route('/stats', methods=['GET'])
@admin_required
def get_stats():
    """Get dashboard statistics."""
    stats, err = AdminService.get_dashboard_stats()
    if err:
        return error_response(err)
    return success_response(stats)


@admin_bp.route('/doctors', methods=['GET'])
@admin_required
def get_doctors():
    """Get all registered doctors."""
    doctors = AdminService.get_all_doctors()
    return success_response(doctors)


@admin_bp.route('/doctors', methods=['POST'])
@admin_required
def add_doctor():
    """Add a new doctor from admin panel."""
    data = request.get_json()
    valid, msg = validate_required_fields(data, ['full_name', 'email', 'specialization'])
    if not valid:
        return error_response(msg)
    result, err = AdminService.add_doctor(data)
    if err:
        return error_response(err)
    return success_response(result, 'Doctor added successfully', 201)


@admin_bp.route('/doctors/<int:doctor_id>/verify', methods=['POST'])
@admin_required
def verify_doctor(doctor_id):
    """Verify a doctor account."""
    success, msg = AdminService.verify_doctor(doctor_id)
    if not success:
        return error_response(msg)
    return success_response(message=msg)


@admin_bp.route('/doctors/<int:doctor_id>', methods=['DELETE'])
@admin_required
def delete_doctor(doctor_id):
    """Delete a doctor account."""
    success, msg = AdminService.delete_doctor(doctor_id)
    if not success:
        return error_response(msg)
    return success_response(message=msg)


@admin_bp.route('/patients', methods=['GET'])
@admin_required
def get_patients():
    """Get all registered patients."""
    patients = AdminService.get_all_patients()
    return success_response(patients)


@admin_bp.route('/patients/<int:patient_id>', methods=['DELETE'])
@admin_required
def delete_patient(patient_id):
    """Ban/Delete a patient account."""
    success, msg = AdminService.delete_patient(patient_id)
    if not success:
        return error_response(msg)
    return success_response(message=msg)


@admin_bp.route('/appointments', methods=['GET'])
@admin_required
def get_appointments():
    """Get recent appointments."""
    appointments = AdminService.get_all_appointments()
    return success_response(appointments)


@admin_bp.route('/chat-logs', methods=['GET'])
@admin_required
def get_chat_logs():
    """Get system-wide chat logs."""
    logs = AdminService.get_recent_chat_logs()
    return success_response(logs)


@admin_bp.route('/me', methods=['GET'])
@admin_required
def get_current_admin():
    """Get current admin profile."""
    admin = AuthService.get_admin_by_id(session['admin_id'])
    if not admin:
        return error_response('Admin not found', 404)
    return success_response(admin)
