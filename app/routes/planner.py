"""EduPilot – Weekly Study Planner Routes"""
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from datetime import datetime, date, timedelta, timezone
from app.extensions import db
from app.models import StudyPlan, Roadmap, RoadmapMilestone
from app.watsonx_client import get_watsonx_client
from app.agent_instructions import build_system_prompt

planner_bp = Blueprint('planner', __name__)

DAYS_OF_WEEK = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']


@planner_bp.route('/')
@login_required
def index():
    """Weekly study planner page."""
    today = datetime.now(timezone.utc).date()
    # Get start of current week (Monday)
    week_start = today - timedelta(days=today.weekday())

    current_plan = StudyPlan.query.filter_by(
        user_id=current_user.id, week_start=week_start
    ).first()

    past_plans = StudyPlan.query.filter_by(user_id=current_user.id)\
        .order_by(StudyPlan.week_start.desc()).limit(4).all()

    # Get current milestone for context
    current_milestone = None
    active_roadmap = Roadmap.query.filter_by(
        user_id=current_user.id, status='active'
    ).first()
    if active_roadmap:
        current_milestone = active_roadmap.milestones.filter_by(completed=False)\
            .order_by(RoadmapMilestone.order).first()

    return render_template('dashboard/planner.html',
                           current_plan=current_plan,
                           past_plans=past_plans,
                           days_of_week=DAYS_OF_WEEK,
                           week_start=week_start,
                           today=today,
                           current_milestone=current_milestone)


@planner_bp.route('/generate', methods=['POST'])
@login_required
def generate():
    """Generate an AI-powered weekly study plan."""
    profile = current_user.profile
    profile_data = {}
    if profile:
        profile_data = {
            'name': profile.full_name or current_user.username,
            'learning_style': profile.learning_style or 'mixed',
            'experience_level': profile.experience_level or 'beginner',
        }

    study_hours = profile.study_hours_per_week if profile else 10

    # Get current milestone
    active_roadmap = Roadmap.query.filter_by(
        user_id=current_user.id, status='active'
    ).first()
    current_milestone_title = "General Learning"
    if active_roadmap:
        milestone = active_roadmap.milestones.filter_by(completed=False)\
            .order_by(RoadmapMilestone.order).first()
        if milestone:
            current_milestone_title = milestone.title

    system_prompt = build_system_prompt(profile_data)
    client = get_watsonx_client()

    plan_data = client.generate_weekly_plan(
        profile_data, current_milestone_title, study_hours, system_prompt
    )

    # Save plan
    today = datetime.now(timezone.utc).date()
    week_start = today - timedelta(days=today.weekday())

    existing = StudyPlan.query.filter_by(
        user_id=current_user.id, week_start=week_start
    ).first()

    if existing:
        existing.daily_goals_dict = plan_data.get('days', {})
        existing.total_hours = plan_data.get('total_hours', study_hours)
        db.session.commit()
        plan = existing
    else:
        plan = StudyPlan(
            user_id=current_user.id,
            week_start=week_start,
            total_hours=plan_data.get('total_hours', study_hours),
        )
        plan.daily_goals_dict = plan_data.get('days', {})
        db.session.add(plan)
        db.session.commit()

    return jsonify({
        'success': True,
        'plan_id': plan.id,
        'plan': plan_data
    })
