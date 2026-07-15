"""EduPilot – Dashboard Routes"""
from flask import Blueprint, render_template, jsonify
from flask_login import login_required, current_user
from app.models import Roadmap, Assessment, Achievement, ChatMessage, StudyPlan
from app.agent_instructions import CAREER_DOMAINS, CAREER_READINESS_LABELS
from datetime import datetime, timedelta, timezone

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/')
@dashboard_bp.route('/index')
@login_required
def index():
    user = current_user

    # Get career readiness score
    readiness_score = user.get_career_readiness_score()

    # Get readiness label
    readiness_label = "Just Starting"
    readiness_icon = "bi-emoji-neutral"
    readiness_color = "#6c757d"
    for (low, high), (label, icon, color) in CAREER_READINESS_LABELS.items():
        if low <= readiness_score <= high:
            readiness_label = label
            readiness_icon = icon
            readiness_color = color
            break

    # Get active roadmap
    active_roadmap = Roadmap.query.filter_by(
        user_id=user.id, status='active'
    ).order_by(Roadmap.generated_at.desc()).first()

    # Get latest assessment
    latest_assessment = Assessment.query.filter_by(
        user_id=user.id
    ).order_by(Assessment.taken_at.desc()).first()

    # Get recent achievements
    recent_achievements = Achievement.query.filter_by(
        user_id=user.id
    ).order_by(Achievement.earned_at.desc()).limit(5).all()

    # Get today's plan
    today = datetime.now(timezone.utc).date()
    study_plan = StudyPlan.query.filter_by(
        user_id=user.id
    ).order_by(StudyPlan.week_start.desc()).first()

    # Calculate study streak (simplified)
    streak_days = _calculate_streak(user.id)

    # Total courses completed
    completed_milestones = 0
    total_milestones = 0
    if active_roadmap:
        completed_milestones = active_roadmap.milestones.filter_by(completed=True).count()
        total_milestones = active_roadmap.milestones.count()

    return render_template('dashboard/index.html',
                           user=user,
                           readiness_score=readiness_score,
                           readiness_label=readiness_label,
                           readiness_icon=readiness_icon,
                           readiness_color=readiness_color,
                           active_roadmap=active_roadmap,
                           latest_assessment=latest_assessment,
                           recent_achievements=recent_achievements,
                           study_plan=study_plan,
                           streak_days=streak_days,
                           completed_milestones=completed_milestones,
                           total_milestones=total_milestones,
                           career_domains=CAREER_DOMAINS)


@dashboard_bp.route('/achievements')
@login_required
def achievements():
    """Achievements and badges page."""
    earned_badges = current_user.achievements.order_by(Achievement.earned_at.desc()).all()
    return render_template('dashboard/achievements.html',
                           earned_badges=earned_badges)


def _calculate_streak(user_id):
    """Calculate user's current study streak in days."""
    messages = ChatMessage.query.filter_by(user_id=user_id, role='user')\
        .order_by(ChatMessage.timestamp.desc()).all()

    if not messages:
        return 0

    streak = 0
    check_date = datetime.now(timezone.utc).date()

    for msg in messages:
        msg_date = msg.timestamp.date() if msg.timestamp.tzinfo else msg.timestamp.date()
        if msg_date == check_date:
            if streak == 0:
                streak = 1
            check_date -= timedelta(days=1)
        elif msg_date < check_date:
            break

    return streak
