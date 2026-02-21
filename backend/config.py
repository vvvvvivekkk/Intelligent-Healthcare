import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root so GMAIL_SENDER / GMAIL_PASSWORD are found
_project_root = Path(__file__).resolve().parent.parent
load_dotenv(_project_root / ".env")


class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'fallback-secret-key')
    DATABASE_PATH = os.getenv('DATABASE_PATH', 'medsync.db')
    OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY', '')
    OPENROUTER_MODEL = os.getenv('OPENROUTER_MODEL', 'mistralai/mistral-7b-instruct')
    OPENROUTER_FALLBACK_MODEL = os.getenv('OPENROUTER_FALLBACK_MODEL', 'meta-llama/llama-3-8b-instruct')
    OPENROUTER_URL = os.getenv('OPENROUTER_BASE_URL', 'https://openrouter.ai/api/v1/chat/completions')
    SESSION_TYPE = 'filesystem'
    PERMANENT_SESSION_LIFETIME = 3600
    OTP_EXPIRY_MINUTES = 10
    MAX_API_RETRIES = 3
    API_RETRY_DELAY = 2

    # Email Config
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.getenv('GMAIL_SENDER')
    MAIL_PASSWORD = os.getenv('GMAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.getenv('GMAIL_SENDER')
    MAIL_VERIFICATION_TIMEOUT = int(os.getenv('MAIL_VERIFICATION_TIMEOUT', 24))
    # If True, when email send fails in development, OTP is printed to server console so you can still test
    MAIL_DEBUG_OTP_TO_CONSOLE = os.getenv('MAIL_DEBUG_OTP_TO_CONSOLE', '').lower() in ('true', '1', 'yes')


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False


config_map = {
    'development': DevelopmentConfig,
    'production': ProductionConfig
}


def get_config():
    env = os.getenv('FLASK_ENV', 'development')
    return config_map.get(env, DevelopmentConfig)
