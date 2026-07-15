"""EduPilot – Settings Routes"""
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from app.extensions import db

settings_bp = Blueprint('settings', __name__)


@settings_bp.route('/')
@login_required
def index():
    return render_template('dashboard/settings.html')


@settings_bp.route('/update', methods=['POST'])
@login_required
def update():
    """Update user settings."""
    data = request.get_json() or request.form

    profile = current_user.profile
    if profile:
        if 'dark_mode' in data:
            profile.dark_mode = str(data['dark_mode']).lower() in ('true', '1', 'on')
        if 'email_notifications' in data:
            profile.email_notifications = str(data['email_notifications']).lower() in ('true', '1', 'on')
        db.session.commit()

    if request.is_json:
        return jsonify({'status': 'updated', 'dark_mode': profile.dark_mode if profile else False})

    flash('Settings saved!', 'success')
    return redirect(url_for('settings.index'))
