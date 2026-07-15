"""EduPilot – Learning Analytics Routes"""
from flask import Blueprint, render_template, jsonify
from flask_login import login_required, current_user
from app.models import ChatMessage, Assessment, Roadmap, RoadmapMilestone, StudyPlan
from datetime import datetime, timedelta, timezone

analytics_bp = Blueprint('analytics', __name__)


@analytics_bp.route('/')
@login_required
def index():
    """Analytics dashboard page."""
    return render_template('dashboard/analytics.html')


@analytics_bp.route('/data')
@login_required
def data():
    """Return all analytics data as JSON for Chart.js."""
    user_id = current_user.id

    # Weekly study hours (last 8 weeks)
    weekly_hours = _weekly_hours(user_id)

    # Assessment scores over time
    assessments = Assessment.query.filter_by(user_id=user_id)\
        .order_by(Assessment.taken_at.asc()).all()
    assessment_data = [
        {
            'domain': a.domain,
            'score': a.score,
            'date': a.taken_at.strftime('%b %d') if a.taken_at else '',
            'grade': a.grade_label()
        }
        for a in assessments
    ]

    # Milestone completion by level
    roadmaps = Roadmap.query.filter_by(user_id=user_id).all()
    milestones_by_level = {'beginner': {'total': 0, 'done': 0},
                            'intermediate': {'total': 0, 'done': 0},
                            'advanced': {'total': 0, 'done': 0}}
    for r in roadmaps:
        for m in r.milestones.all():
            level = m.level if m.level in milestones_by_level else 'beginner'
            milestones_by_level[level]['total'] += 1
            if m.completed:
                milestones_by_level[level]['done'] += 1

    # Chat activity by day of week
    all_msgs = ChatMessage.query.filter_by(user_id=user_id, role='user').all()
    day_activity = [0] * 7  # Mon-Sun
    for msg in all_msgs:
        if msg.timestamp:
            day_activity[msg.timestamp.weekday()] += 1

    # Career readiness over time (simplified)
    readiness_score = current_user.get_career_readiness_score()

    # Total stats
    total_messages = ChatMessage.query.filter_by(user_id=user_id, role='user').count()
    total_milestones_done = sum(
        r.milestones.filter_by(completed=True).count() for r in roadmaps
    )
    total_assessments = len(assessments)
    avg_score = sum(a.score for a in assessments) / len(assessments) if assessments else 0

    return jsonify({
        'weekly_hours': weekly_hours,
        'assessments': assessment_data,
        'milestones_by_level': milestones_by_level,
        'day_activity': day_activity,
        'readiness_score': readiness_score,
        'total_messages': total_messages,
        'total_milestones_done': total_milestones_done,
        'total_assessments': total_assessments,
        'avg_assessment_score': round(avg_score, 1)
    })


def _weekly_hours(user_id):
    """Estimate weekly study hours from chat activity."""
    result = []
    for i in range(7, -1, -1):
        week_end = datetime.now(timezone.utc) - timedelta(weeks=i)
        week_start = week_end - timedelta(days=6)
        msgs = ChatMessage.query.filter_by(user_id=user_id, role='user')\
            .filter(ChatMessage.timestamp.between(week_start, week_end)).count()
        estimated_hours = round(msgs * 0.3, 1)
        result.append({
            'week': week_start.strftime('%b %d'),
            'hours': estimated_hours,
            'messages': msgs
        })
    return result
