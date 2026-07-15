"""
EduPilot – Configuration Module
Supports Development and Production environments.
"""
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Base configuration shared by all environments."""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'edupilot-fallback-secret-key')
    APP_NAME = os.environ.get('APP_NAME', 'EduPilot')

    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///edupilot.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # IBM Watsonx.ai
    IBM_API_KEY = os.environ.get('IBM_API_KEY', '')
    IBM_PROJECT_ID = os.environ.get('IBM_PROJECT_ID', '')
    IBM_REGION = os.environ.get('IBM_REGION', 'us-south')
    WATSONX_MODEL_ID = os.environ.get('WATSONX_MODEL_ID', 'ibm/granite-4-h-small')

    # AI Generation Settings
    MAX_TOKENS = int(os.environ.get('MAX_TOKENS', 2048))
    TEMPERATURE = float(os.environ.get('TEMPERATURE', 0.7))
    MAX_CHAT_HISTORY = int(os.environ.get('MAX_CHAT_HISTORY', 50))

    # Admin
    ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL', 'admin@edupilot.ai')
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'Admin@123!')

    # File uploads
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5MB
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'static', 'uploads')


class DevelopmentConfig(Config):
    DEBUG = True
    FLASK_ENV = 'development'


class ProductionConfig(Config):
    DEBUG = False
    FLASK_ENV = 'production'


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
