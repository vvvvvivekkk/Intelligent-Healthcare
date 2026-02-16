import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'fallback-secret-key')
    DATABASE_PATH = os.getenv('DATABASE_PATH', 'medsync.db')
    OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY', '')
    OPENROUTER_MODEL = 'meta-llama/llama-3.3-70b-instruct:free'
    OPENROUTER_URL = 'https://openrouter.ai/api/v1/chat/completions'
    SESSION_TYPE = 'filesystem'
    PERMANENT_SESSION_LIFETIME = 3600
    OTP_EXPIRY_MINUTES = 10
    MAX_API_RETRIES = 3
    API_RETRY_DELAY = 2


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
