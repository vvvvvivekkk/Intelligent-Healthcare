import os
import sys
import logging
from flask import Flask, send_from_directory, jsonify
from datetime import timedelta

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.config import get_config
from backend.utils.database import init_db
from backend.blueprints.auth import auth_bp
from backend.blueprints.doctors import doctors_bp
from backend.blueprints.appointments import appointments_bp
from backend.blueprints.chatbot import chatbot_bp
from backend.blueprints.admin import admin_bp

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_app():
    """Application factory."""
    app = Flask(__name__,
                static_folder='frontend',
                static_url_path='')

    # Load config
    config = get_config()
    app.config.from_object(config)
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=2)

    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(doctors_bp)
    app.register_blueprint(appointments_bp)
    app.register_blueprint(chatbot_bp)
    app.register_blueprint(admin_bp)

    # Initialize database
    with app.app_context():
        init_db()
        logger.info("Database initialized")

        # Auto-seed admin accounts if none exist, or fix password hashes
        try:
            from backend.utils.database import query_db, execute_db
            from werkzeug.security import generate_password_hash, check_password_hash
            admin = query_db('SELECT * FROM admins WHERE username = ?', ('admin',), one=True)
            if not admin:
                pwd = generate_password_hash('admin123')
                execute_db('INSERT INTO admins (username, password_hash) VALUES (?, ?)', ('admin', pwd))
                logger.info("Default admin account created (admin/admin123)")
            else:
                # Verify hash is valid - fix if corrupted or incompatible
                if not check_password_hash(admin['password_hash'], 'admin123'):
                    pwd = generate_password_hash('admin123')
                    execute_db('UPDATE admins SET password_hash = ? WHERE id = ?', (pwd, admin['id']))
                    logger.info("Admin password hash was invalid - reset to admin123")
                else:
                    logger.info("Admin account verified OK")
        except Exception as e:
            logger.error(f"Admin seed error: {e}")

    # ─── Error Handlers ──────────────────────────────────────

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({'success': False, 'message': 'Resource not found'}), 404

    @app.errorhandler(500)
    def server_error(e):
        logger.error(f"Server error: {e}")
        return jsonify({'success': False, 'message': 'Internal server error'}), 500

    @app.errorhandler(405)
    def method_not_allowed(e):
        return jsonify({'success': False, 'message': 'Method not allowed'}), 405

    # ─── Frontend Routes ─────────────────────────────────────

    @app.route('/')
    def index():
        return send_from_directory('frontend/pages', 'index.html')

    @app.route('/login')
    def login_page():
        return send_from_directory('frontend/pages', 'login.html')

    @app.route('/register')
    def register_page():
        return send_from_directory('frontend/pages', 'register.html')

    @app.route('/patient/dashboard')
    def patient_dashboard():
        return send_from_directory('frontend/pages', 'patient_dashboard.html')

    @app.route('/patient/chatbot')
    def patient_chatbot():
        return send_from_directory('frontend/pages', 'chatbot.html')

    @app.route('/patient/appointments')
    def patient_appointments():
        return send_from_directory('frontend/pages', 'patient_appointments.html')

    @app.route('/doctor/dashboard')
    def doctor_dashboard():
        return send_from_directory('frontend/pages', 'doctor_dashboard.html')

    @app.route('/doctor/register')
    def doctor_register():
        return send_from_directory('frontend/pages', 'doctor_register.html')

    @app.route('/doctor/login')
    def doctor_login():
        return send_from_directory('frontend/pages', 'doctor_login.html')

    @app.route('/doctors/browse')
    def browse_doctors():
        return send_from_directory('frontend/pages', 'browse_doctors.html')

    @app.route('/admin/login')
    def admin_login():
        return send_from_directory('frontend/pages', 'admin_login.html')

    @app.route('/admin/dashboard')
    def admin_dashboard():
        return send_from_directory('frontend/pages', 'admin_dashboard.html')

    # Health check
    @app.route('/api/health')
    def health():
        return jsonify({'status': 'healthy', 'app': 'MedSync AI'})

    return app


app = create_app()

if __name__ == '__main__':
    app.run(debug=True, port=5000)
