"""
EduPilot – Flask Extensions
Initialized here, registered in app factory to avoid circular imports.
"""
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from flask_migrate import Migrate

db = SQLAlchemy()
login_manager = LoginManager()
bcrypt = Bcrypt()
migrate = Migrate()

# Configure Login Manager
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access EduPilot.'
login_manager.login_message_category = 'info'
