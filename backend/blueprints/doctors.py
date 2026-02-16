from flask import Blueprint, request, session
from backend.services.doctor_service import DoctorService
from backend.utils.helpers import (
    success_response, error_response, login_required, doctor_required
)

doctors_bp = Blueprint('doctors', __name__, url_prefix='/api/doctors')


@doctors_bp.route('/', methods=['GET'])
def get_doctors():
    """Get all verified doctors."""
    doctors = DoctorService.get_all_doctors(verified_only=True)
    return success_response(doctors)


@doctors_bp.route('/all', methods=['GET'])
def get_all_doctors():
    """Get all doctors (including unverified)."""
    doctors = DoctorService.get_all_doctors(verified_only=False)
    return success_response(doctors)


@doctors_bp.route('/search', methods=['GET'])
def search_doctors():
    """Search doctors by name, specialization, or disease."""
    query = request.args.get('q', '').strip()
    search_type = request.args.get('type', 'all')

    if not query:
        return error_response('Search query required')

    if search_type not in ('name', 'specialization', 'disease', 'all'):
        return error_response('Invalid search type')

    doctors = DoctorService.search_doctors(query, search_type)
    return success_response(doctors)


@doctors_bp.route('/specializations', methods=['GET'])
def get_specializations():
    """Get all available specializations."""
    specs = DoctorService.get_specializations()
    return success_response(specs)


@doctors_bp.route('/by-specialization/<specialization>', methods=['GET'])
def get_by_specialization(specialization):
    """Get doctors by specialization."""
    doctors = DoctorService.get_doctors_by_specialization(specialization)
    return success_response(doctors)


@doctors_bp.route('/<int:doctor_id>', methods=['GET'])
def get_doctor(doctor_id):
    """Get doctor profile."""
    doctor = DoctorService.get_doctor_profile(doctor_id)
    if not doctor:
        return error_response('Doctor not found', 404)
    return success_response(doctor)


@doctors_bp.route('/profile', methods=['PUT'])
@doctor_required
def update_profile():
    """Update doctor profile."""
    data = request.get_json()
    if not data:
        return error_response('Request body required')

    doctor_id = session['doctor_id']
    success = DoctorService.update_doctor_profile(doctor_id, **data)
    
    if success:
        doctor = DoctorService.get_doctor_profile(doctor_id)
        return success_response(doctor, 'Profile updated')
    return error_response('No fields to update')


@doctors_bp.route('/disease-mapping', methods=['GET'])
def get_disease_mapping():
    """Get disease-to-specialization mappings."""
    disease = request.args.get('disease')
    mappings = DoctorService.get_disease_mapping(disease)
    return success_response(mappings)


@doctors_bp.route('/recommend', methods=['POST'])
@login_required
def recommend_doctors():
    """Recommend doctors based on specialization from AI analysis."""
    data = request.get_json()
    if not data:
        return error_response('Request body required')

    specialization = data.get('specialization', '').strip()
    if not specialization:
        return error_response('Specialization required')

    doctors = DoctorService.get_doctors_by_specialization(specialization)

    if not doctors:
        # Try fuzzy match
        doctors = DoctorService.search_doctors(specialization, 'specialization')

    return success_response({
        'specialization': specialization,
        'doctors': doctors,
        'count': len(doctors)
    })
