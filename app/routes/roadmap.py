"""EduPilot – Course Roadmap Routes"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime, timezone
from app.extensions import db
from app.models import Roadmap, RoadmapMilestone, Achievement
from app.watsonx_client import get_watsonx_client
from app.agent_instructions import build_system_prompt, CAREER_DOMAINS

roadmap_bp = Blueprint('roadmap', __name__)


@roadmap_bp.route('/')
@login_required
def index():
    """Show user's active roadmap or let them choose a domain."""
    active_roadmap = Roadmap.query.filter_by(
        user_id=current_user.id, status='active'
    ).order_by(Roadmap.generated_at.desc()).first()

    all_roadmaps = Roadmap.query.filter_by(
        user_id=current_user.id
    ).order_by(Roadmap.generated_at.desc()).all()

    return render_template('dashboard/roadmap.html',
                           roadmap=active_roadmap,
                           all_roadmaps=all_roadmaps,
                           career_domains=CAREER_DOMAINS)


@roadmap_bp.route('/generate', methods=['POST'])
@login_required
def generate():
    """Generate a new AI-powered roadmap."""
    domain = request.form.get('domain', '').strip()
    if not domain:
        flash('Please select a career domain.', 'warning')
        return redirect(url_for('roadmap.index'))

    profile = current_user.profile
    profile_data = {}
    if profile:
        profile_data = {
            'education': profile.education or '',
            'career_goal': profile.career_goal or domain,
            'skills': profile.skills_list,
            'experience_level': profile.experience_level or 'beginner',
            'learning_style': profile.learning_style or 'mixed',
            'study_hours': profile.study_hours_per_week or 10,
        }

    system_prompt = build_system_prompt(profile_data)
    client = get_watsonx_client()

    # Deactivate previous roadmaps
    Roadmap.query.filter_by(user_id=current_user.id, status='active').update({'status': 'paused'})

    # Generate roadmap
    roadmap_data = client.generate_roadmap(profile_data, domain, system_prompt)

    # Save to database
    roadmap = Roadmap(
        user_id=current_user.id,
        domain=domain,
        title=roadmap_data.get('title', f'{domain} Roadmap'),
        status='active'
    )
    db.session.add(roadmap)
    db.session.flush()

    # Save milestones
    levels_data = roadmap_data.get('levels', {})
    level_order = {'beginner': 0, 'intermediate': 10, 'advanced': 20}

    for level_name, milestones in levels_data.items():
        if not isinstance(milestones, list):
            continue
        base_order = level_order.get(level_name, 0)
        for i, m in enumerate(milestones):
            milestone = RoadmapMilestone(
                roadmap_id=roadmap.id,
                level=level_name,
                order=base_order + i,
                title=m.get('title', f'{level_name.title()} Milestone {i+1}'),
                description=m.get('description', ''),
                duration_weeks=m.get('duration_weeks', 2),
            )
            milestone.resources_list = m.get('resources', [])
            milestone.projects_list = m.get('projects', [])
            milestone.certifications_list = m.get('certifications', [])
            db.session.add(milestone)

    db.session.commit()

    # Award roadmap badge
    _check_roadmap_badge(current_user.id)

    flash(f'🗺️ Your personalized {domain} roadmap has been generated!', 'success')
    return redirect(url_for('roadmap.view', roadmap_id=roadmap.id))


@roadmap_bp.route('/view/<int:roadmap_id>')
@login_required
def view(roadmap_id):
    """View a specific roadmap."""
    roadmap = Roadmap.query.filter_by(
        id=roadmap_id, user_id=current_user.id
    ).first_or_404()

    milestones = roadmap.milestones.order_by(RoadmapMilestone.order).all()

    # Group by level
    grouped = {'beginner': [], 'intermediate': [], 'advanced': []}
    for m in milestones:
        level = m.level if m.level in grouped else 'beginner'
        grouped[level].append(m)

    return render_template('dashboard/roadmap.html',
                           roadmap=roadmap,
                           milestones=milestones,
                           grouped_milestones=grouped,
                           all_roadmaps=Roadmap.query.filter_by(user_id=current_user.id).all(),
                           career_domains=CAREER_DOMAINS)


@roadmap_bp.route('/milestone/<int:milestone_id>/toggle', methods=['POST'])
@login_required
def toggle_milestone(milestone_id):
    """Toggle milestone completion status."""
    milestone = RoadmapMilestone.query.join(Roadmap).filter(
        RoadmapMilestone.id == milestone_id,
        Roadmap.user_id == current_user.id
    ).first_or_404()

    milestone.completed = not milestone.completed
    milestone.completed_at = datetime.now(timezone.utc) if milestone.completed else None
    db.session.commit()

    # Check for completion badges
    roadmap = milestone.roadmap
    if milestone.completed:
        _check_completion_badges(current_user.id, roadmap)

    return jsonify({
        'completed': milestone.completed,
        'progress': roadmap.completion_percentage()
    })


def _check_roadmap_badge(user_id):
    existing = Achievement.query.filter_by(user_id=user_id, badge_name='Roadmap Explorer').first()
    if not existing:
        badge = Achievement(
            user_id=user_id,
            badge_name='Roadmap Explorer',
            badge_icon='bi-map',
            badge_color='#45B7D1',
            description='Generated your first personalized learning roadmap!'
        )
        db.session.add(badge)
        db.session.commit()


def _check_completion_badges(user_id, roadmap):
    progress = roadmap.completion_percentage()
    badges_to_check = [
        (25, 'First Steps', 'bi-footprints', '#F7DC6F', 'Completed 25% of your roadmap'),
        (50, 'Halfway Hero', 'bi-star-half', '#FF6B6B', 'Completed 50% of your roadmap'),
        (100, 'Roadmap Champion', 'bi-trophy-fill', '#FFD700', 'Completed 100% of your roadmap!'),
    ]
    for threshold, name, icon, color, desc in badges_to_check:
        if progress >= threshold:
            existing = Achievement.query.filter_by(user_id=user_id, badge_name=name).first()
            if not existing:
                badge = Achievement(
                    user_id=user_id, badge_name=name, badge_icon=icon,
                    badge_color=color, description=desc
                )
                db.session.add(badge)
    db.session.commit()
