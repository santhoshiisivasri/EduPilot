"""EduPilot – Progress Tracking Routes"""
from flask import Blueprint, render_template, jsonify
from flask_login import login_required, current_user
from app.models import Roadmap, RoadmapMilestone, Assessment, ChatMessage
from datetime import datetime, timedelta, timezone

progress_bp = Blueprint('progress', __name__)


@progress_bp.route('/')
@login_required
def index():
    """Progress tracking dashboard."""
    roadmaps = Roadmap.query.filter_by(user_id=current_user.id)\
        .order_by(Roadmap.generated_at.desc()).all()

    active_roadmap = next((r for r in roadmaps if r.status == 'active'), None)

    # Activity heatmap data (last 12 weeks)
    heatmap_data = _get_activity_heatmap(current_user.id)

    # Weekly progress data
    weekly_data = _get_weekly_progress(current_user.id)

    return render_template('dashboard/progress.html',
                           roadmaps=roadmaps,
                           active_roadmap=active_roadmap,
                           heatmap_data=heatmap_data,
                           weekly_data=weekly_data)


@progress_bp.route('/data')
@login_required
def data():
    """Return progress data as JSON for charts."""
    weekly = _get_weekly_progress(current_user.id)
    heatmap = _get_activity_heatmap(current_user.id)

    active_roadmap = Roadmap.query.filter_by(
        user_id=current_user.id, status='active'
    ).first()

    roadmap_data = {}
    if active_roadmap:
        milestones = active_roadmap.milestones.order_by(RoadmapMilestone.order).all()
        roadmap_data = {
            'total': len(milestones),
            'completed': sum(1 for m in milestones if m.completed),
            'by_level': {
                'beginner': {
                    'total': sum(1 for m in milestones if m.level == 'beginner'),
                    'completed': sum(1 for m in milestones if m.level == 'beginner' and m.completed)
                },
                'intermediate': {
                    'total': sum(1 for m in milestones if m.level == 'intermediate'),
                    'completed': sum(1 for m in milestones if m.level == 'intermediate' and m.completed)
                },
                'advanced': {
                    'total': sum(1 for m in milestones if m.level == 'advanced'),
                    'completed': sum(1 for m in milestones if m.level == 'advanced' and m.completed)
                }
            }
        }

    return jsonify({
        'weekly_activity': weekly,
        'heatmap': heatmap,
        'roadmap': roadmap_data
    })


def _get_activity_heatmap(user_id):
    """Generate activity heatmap data for last 84 days."""
    end_date = datetime.now(timezone.utc).date()
    start_date = end_date - timedelta(days=83)

    # Count chat messages per day
    messages = ChatMessage.query.filter_by(user_id=user_id, role='user')\
        .filter(ChatMessage.timestamp >= datetime.combine(start_date, datetime.min.time())).all()

    activity = {}
    for msg in messages:
        date_str = msg.timestamp.date().isoformat() if hasattr(msg.timestamp, 'date') else str(msg.timestamp)[:10]
        activity[date_str] = activity.get(date_str, 0) + 1

    # Fill all dates
    result = []
    current = start_date
    while current <= end_date:
        date_str = current.isoformat()
        count = activity.get(date_str, 0)
        result.append({'date': date_str, 'count': count})
        current += timedelta(days=1)

    return result


def _get_weekly_progress(user_id):
    """Get weekly activity for the last 8 weeks."""
    weeks = []
    for i in range(7, -1, -1):
        week_end = datetime.now(timezone.utc).date() - timedelta(weeks=i)
        week_start = week_end - timedelta(days=6)
        msg_count = ChatMessage.query.filter_by(user_id=user_id, role='user')\
            .filter(
                ChatMessage.timestamp >= datetime.combine(week_start, datetime.min.time()),
                ChatMessage.timestamp <= datetime.combine(week_end, datetime.max.time())
            ).count()
        weeks.append({
            'week': f"Week {8 - i}",
            'label': week_start.strftime('%b %d'),
            'messages': msg_count,
            'hours': round(msg_count * 0.25, 1)  # Estimate
        })
    return weeks
