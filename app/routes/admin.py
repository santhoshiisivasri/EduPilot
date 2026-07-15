"""EduPilot – Admin Dashboard Routes"""
from flask import Blueprint, render_template, jsonify, abort
from flask_login import login_required, current_user
from app.models import User, ChatMessage, Assessment, Roadmap, Achievement
from app.extensions import db
from datetime import datetime, timedelta, timezone

admin_bp = Blueprint('admin', __name__)


def admin_required(f):
    """Decorator to restrict access to admin users."""
    from functools import wraps
    from flask import redirect, url_for, flash
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('Admin access required.', 'danger')
            return redirect(url_for('dashboard.index'))
        return f(*args, **kwargs)
    return decorated


@admin_bp.route('/')
@login_required
@admin_required
def index():
    """Admin dashboard overview."""
    total_users = User.query.filter_by(role='student').count()
    total_messages = ChatMessage.query.count()
    total_assessments = Assessment.query.count()
    total_roadmaps = Roadmap.query.count()

    recent_users = User.query.filter_by(role='student')\
        .order_by(User.created_at.desc()).limit(10).all()

    # AI interaction stats
    today_msgs = ChatMessage.query.filter(
        ChatMessage.timestamp >= datetime.now(timezone.utc).replace(hour=0, minute=0, second=0)
    ).count()

    # Weekly signups
    week_ago = datetime.now(timezone.utc) - timedelta(days=7)
    weekly_signups = User.query.filter(User.created_at >= week_ago).count()

    return render_template('admin/index.html',
                           total_users=total_users,
                           total_messages=total_messages,
                           total_assessments=total_assessments,
                           total_roadmaps=total_roadmaps,
                           recent_users=recent_users,
                           today_msgs=today_msgs,
                           weekly_signups=weekly_signups)


@admin_bp.route('/users')
@login_required
@admin_required
def users():
    """All users list."""
    all_users = User.query.order_by(User.created_at.desc()).all()
    return jsonify([{
        'id': u.id,
        'username': u.username,
        'email': u.email,
        'role': u.role,
        'created_at': u.created_at.isoformat() if u.created_at else '',
        'last_login': u.last_login.isoformat() if u.last_login else '',
        'profile_complete': u.profile.completion_percentage() if u.profile else 0
    } for u in all_users])


@admin_bp.route('/analytics')
@login_required
@admin_required
def platform_analytics():
    """Platform-wide analytics."""
    users = User.query.filter_by(role='student').all()
    total_chat_msgs = ChatMessage.query.filter_by(role='user').count()

    # Domain popularity
    domain_counts = db.session.query(Roadmap.domain, db.func.count(Roadmap.id))\
        .group_by(Roadmap.domain).all()

    return jsonify({
        'total_users': len(users),
        'total_ai_messages': total_chat_msgs,
        'domain_popularity': [{'domain': d, 'count': c} for d, c in domain_counts],
        'avg_messages_per_user': round(total_chat_msgs / max(len(users), 1), 1)
    })
