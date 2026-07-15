"""
EduPilot – Flask Application Factory
"""
import os
from flask import Flask
from app.config import config
from app.extensions import db, login_manager, bcrypt, migrate


def create_app(config_name=None):
    """Application factory function."""
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')

    app = Flask(__name__,
                template_folder='templates',
                static_folder='static')

    # Load config
    app.config.from_object(config.get(config_name, config['default']))

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    bcrypt.init_app(app)
    migrate.init_app(app, db)

    # Ensure upload directory exists
    os.makedirs(app.config.get('UPLOAD_FOLDER', 'static/uploads'), exist_ok=True)

    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.profile import profile_bp
    from app.routes.chat import chat_bp
    from app.routes.roadmap import roadmap_bp
    from app.routes.assessment import assessment_bp
    from app.routes.progress import progress_bp
    from app.routes.career import career_bp
    from app.routes.planner import planner_bp
    from app.routes.analytics import analytics_bp
    from app.routes.admin import admin_bp
    from app.routes.settings import settings_bp
    from app.routes.main import main_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
    app.register_blueprint(profile_bp, url_prefix='/profile')
    app.register_blueprint(chat_bp, url_prefix='/chat')
    app.register_blueprint(roadmap_bp, url_prefix='/roadmap')
    app.register_blueprint(assessment_bp, url_prefix='/assessment')
    app.register_blueprint(progress_bp, url_prefix='/progress')
    app.register_blueprint(career_bp, url_prefix='/career')
    app.register_blueprint(planner_bp, url_prefix='/planner')
    app.register_blueprint(analytics_bp, url_prefix='/analytics')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(settings_bp, url_prefix='/settings')

    # Create DB tables
    with app.app_context():
        db.create_all()
        _seed_admin(app)

    # Context processors
    @app.context_processor
    def inject_globals():
        from app.agent_instructions import AGENT_PERSONA, CAREER_DOMAINS
        return {
            'app_name': 'EduPilot',
            'agent_name': AGENT_PERSONA['name'],
            'career_domains': CAREER_DOMAINS
        }

    return app


def _seed_admin(app):
    """Create default admin user if not exists."""
    from app.models import User, Profile
    from app.extensions import bcrypt

    admin_email = app.config.get('ADMIN_EMAIL', 'admin@edupilot.ai')
    if not User.query.filter_by(email=admin_email).first():
        hashed_pw = bcrypt.generate_password_hash(
            app.config.get('ADMIN_PASSWORD', 'Admin@123!')
        ).decode('utf-8')
        admin = User(
            username='admin',
            email=admin_email,
            password_hash=hashed_pw,
            role='admin'
        )
        db.session.add(admin)
        db.session.flush()

        profile = Profile(
            user_id=admin.id,
            full_name='EduPilot Admin',
            career_goal='Platform Administration'
        )
        db.session.add(profile)
        db.session.commit()
        import logging; logging.getLogger(__name__).info(f"[EduPilot] Admin user created: {admin_email}")
