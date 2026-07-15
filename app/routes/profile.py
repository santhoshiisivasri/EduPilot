"""EduPilot – Profile Routes"""
import os
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.extensions import db
from app.models import Profile, Achievement
from app.agent_instructions import CAREER_DOMAINS

profile_bp = Blueprint('profile', __name__)

LEARNING_STYLES = [
    ('visual', '🎥 Visual – Videos & diagrams'),
    ('reading', '📖 Reading/Writing – Docs & articles'),
    ('kinesthetic', '💻 Hands-on – Projects & coding'),
    ('structured', '🎓 Structured – Courses & quizzes'),
]

EXPERIENCE_LEVELS = [
    ('beginner', 'Beginner – Just starting out'),
    ('intermediate', 'Intermediate – Some experience'),
    ('advanced', 'Advanced – Experienced developer'),
]


@profile_bp.route('/setup', methods=['GET', 'POST'])
@login_required
def setup():
    """Profile setup wizard for new users."""
    return render_template('dashboard/profile.html',
                           is_setup=True,
                           career_domains=CAREER_DOMAINS,
                           learning_styles=LEARNING_STYLES,
                           experience_levels=EXPERIENCE_LEVELS)


@profile_bp.route('/view')
@login_required
def view():
    profile = current_user.profile
    return render_template('dashboard/profile.html',
                           profile=profile,
                           career_domains=CAREER_DOMAINS,
                           learning_styles=LEARNING_STYLES,
                           experience_levels=EXPERIENCE_LEVELS)


@profile_bp.route('/update', methods=['POST'])
@login_required
def update():
    profile = current_user.profile
    if not profile:
        profile = Profile(user_id=current_user.id)
        db.session.add(profile)

    # Text fields
    profile.full_name = request.form.get('full_name', '').strip()
    profile.education = request.form.get('education', '').strip()
    profile.institution = request.form.get('institution', '').strip()
    profile.career_goal = request.form.get('career_goal', '').strip()
    profile.experience_level = request.form.get('experience_level', 'beginner')
    profile.learning_style = request.form.get('learning_style', '')
    profile.preferred_domain = request.form.get('preferred_domain', '')
    profile.bio = request.form.get('bio', '').strip()

    try:
        profile.study_hours_per_week = int(request.form.get('study_hours_per_week', 10))
        profile.graduation_year = int(request.form.get('graduation_year', 0)) or None
    except ValueError:
        profile.study_hours_per_week = 10

    # JSON fields (comma-separated from form)
    skills_raw = request.form.get('skills', '')
    interests_raw = request.form.get('interests', '')
    profile.skills_list = [s.strip() for s in skills_raw.split(',') if s.strip()]
    profile.interests_list = [i.strip() for i in interests_raw.split(',') if i.strip()]

    # Handle avatar upload
    if 'avatar' in request.files:
        file = request.files['avatar']
        if file and file.filename and allowed_file(file.filename):
            upload_folder = os.path.join('app', 'static', 'uploads', 'avatars')
            os.makedirs(upload_folder, exist_ok=True)
            filename = f"avatar_{current_user.id}.{file.filename.rsplit('.', 1)[1].lower()}"
            file.save(os.path.join(upload_folder, filename))
            profile.avatar = filename

    db.session.commit()

    # Award profile completion badge
    _check_profile_badge(current_user, profile)

    flash('✅ Profile updated successfully!', 'success')
    is_setup = request.form.get('is_setup') == '1'
    if is_setup:
        return redirect(url_for('chat.index'))
    return redirect(url_for('profile.view'))


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif', 'webp'}


def _check_profile_badge(user, profile):
    """Award badge for completing profile."""
    from app.models import Achievement
    if profile.completion_percentage() >= 80:
        existing = Achievement.query.filter_by(
            user_id=user.id, badge_name='Profile Master'
        ).first()
        if not existing:
            badge = Achievement(
                user_id=user.id,
                badge_name='Profile Master',
                badge_icon='bi-person-check',
                badge_color='#4ECDC4',
                description='Completed 80%+ of your profile'
            )
            db.session.add(badge)
            db.session.commit()
