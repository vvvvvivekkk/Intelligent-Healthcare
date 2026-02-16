import logging
from functools import wraps
from flask import jsonify, session

logger = logging.getLogger(__name__)


def error_response(message, status_code=400, errors=None):
    """Standardized error response."""
    response = {
        'success': False,
        'message': message
    }
    if errors:
        response['errors'] = errors
    return jsonify(response), status_code


def success_response(data=None, message='Success', status_code=200):
    """Standardized success response."""
    response = {
        'success': True,
        'message': message
    }
    if data is not None:
        response['data'] = data
    return jsonify(response), status_code


def login_required(f):
    """Decorator to require login for a route."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session and 'doctor_id' not in session:
            return error_response('Authentication required', 401)
        return f(*args, **kwargs)
    return decorated_function


def patient_required(f):
    """Decorator to require patient role."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session.get('role') != 'patient':
            return error_response('Patient access required', 403)
        return f(*args, **kwargs)
    return decorated_function


def doctor_required(f):
    """Decorator to require doctor role."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'doctor_id' not in session or session.get('role') != 'doctor':
            return error_response('Doctor access required', 403)
        return f(*args, **kwargs)
    return decorated_function


def validate_required_fields(data, fields):
    """Validate that required fields are present in data."""
    missing = [f for f in fields if not data.get(f)]
    if missing:
        return False, f"Missing required fields: {', '.join(missing)}"
    return True, None


class AppError(Exception):
    """Custom application error."""
    def __init__(self, message, status_code=400):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)
