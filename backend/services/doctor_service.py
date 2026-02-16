import logging
from backend.utils.database import query_db, execute_db

logger = logging.getLogger(__name__)


class DoctorService:
    """Service layer for doctor operations."""

    @staticmethod
    def get_all_doctors(verified_only=True):
        """Get all doctors, optionally filtered by verification status."""
        if verified_only:
            doctors = query_db(
                '''SELECT id, doctor_id, full_name, email, phone, specialization,
                   experience_years, hospital, bio, verified, rating
                   FROM doctors WHERE verified = 1 ORDER BY rating DESC'''
            )
        else:
            doctors = query_db(
                '''SELECT id, doctor_id, full_name, email, phone, specialization,
                   experience_years, hospital, bio, verified, rating
                   FROM doctors ORDER BY rating DESC'''
            )
        return [dict(d) for d in doctors]

    @staticmethod
    def search_doctors(query_str, search_type='all'):
        """Search doctors by name, specialization, or disease."""
        query_str_like = f"%{query_str}%"
        
        if search_type == 'specialization':
            doctors = query_db(
                '''SELECT id, doctor_id, full_name, email, phone, specialization,
                   experience_years, hospital, bio, verified, rating
                   FROM doctors WHERE specialization LIKE ? AND verified = 1
                   ORDER BY rating DESC''',
                (query_str_like,)
            )
        elif search_type == 'disease':
            doctors = query_db(
                '''SELECT DISTINCT d.id, d.doctor_id, d.full_name, d.email, d.phone,
                   d.specialization, d.experience_years, d.hospital, d.bio, d.verified, d.rating
                   FROM doctors d
                   JOIN disease_specialization_mapping dsm ON d.specialization = dsm.specialization
                   WHERE dsm.disease LIKE ? AND d.verified = 1
                   ORDER BY d.rating DESC''',
                (query_str_like,)
            )
        elif search_type == 'name':
            doctors = query_db(
                '''SELECT id, doctor_id, full_name, email, phone, specialization,
                   experience_years, hospital, bio, verified, rating
                   FROM doctors WHERE full_name LIKE ? AND verified = 1
                   ORDER BY rating DESC''',
                (query_str_like,)
            )
        else:
            # search_type == 'all': search across name, specialization, and diseases
            doctors = query_db(
                '''SELECT DISTINCT d.id, d.doctor_id, d.full_name, d.email, d.phone,
                   d.specialization, d.experience_years, d.hospital, d.bio, d.verified, d.rating
                   FROM doctors d
                   LEFT JOIN disease_specialization_mapping dsm ON d.specialization = dsm.specialization
                   WHERE (d.full_name LIKE ? OR d.specialization LIKE ? OR dsm.disease LIKE ?)
                   AND d.verified = 1
                   ORDER BY d.rating DESC''',
                (query_str_like, query_str_like, query_str_like)
            )
        
        return [dict(d) for d in doctors]

    @staticmethod
    def get_doctors_by_specialization(specialization):
        """Get verified doctors by specialization."""
        doctors = query_db(
            '''SELECT id, doctor_id, full_name, email, phone, specialization,
               experience_years, hospital, bio, verified, rating
               FROM doctors WHERE specialization = ? AND verified = 1
               ORDER BY rating DESC''',
            (specialization,)
        )
        return [dict(d) for d in doctors]

    @staticmethod
    def get_doctor_profile(doctor_id):
        """Get detailed doctor profile."""
        doctor = query_db(
            '''SELECT id, doctor_id, full_name, email, phone, specialization,
               experience_years, hospital, bio, verified, rating
               FROM doctors WHERE id = ?''',
            (doctor_id,), one=True
        )
        return dict(doctor) if doctor else None

    @staticmethod
    def update_doctor_profile(doctor_id, **kwargs):
        """Update doctor profile fields."""
        allowed_fields = ['full_name', 'phone', 'specialization', 'experience_years',
                         'hospital', 'bio']
        updates = []
        values = []
        
        for field in allowed_fields:
            if field in kwargs and kwargs[field] is not None:
                updates.append(f"{field} = ?")
                values.append(kwargs[field])
        
        if not updates:
            return False
        
        values.append(doctor_id)
        query = f"UPDATE doctors SET {', '.join(updates)}, updated_at = CURRENT_TIMESTAMP WHERE id = ?"
        execute_db(query, tuple(values))
        return True

    @staticmethod
    def get_specializations():
        """Get all unique specializations."""
        specs = query_db('SELECT DISTINCT specialization FROM doctors WHERE verified = 1 ORDER BY specialization')
        return [s['specialization'] for s in specs]

    @staticmethod
    def get_disease_mapping(disease=None):
        """Get disease-to-specialization mappings."""
        if disease:
            mappings = query_db(
                'SELECT * FROM disease_specialization_mapping WHERE disease LIKE ?',
                (f"%{disease}%",)
            )
        else:
            mappings = query_db('SELECT * FROM disease_specialization_mapping ORDER BY disease')
        return [dict(m) for m in mappings]
