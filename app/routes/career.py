"""EduPilot – Career Recommendation Routes"""
from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required, current_user
from app.agent_instructions import CAREER_DOMAINS, build_system_prompt
from app.watsonx_client import get_watsonx_client
from app.models import Assessment

career_bp = Blueprint('career', __name__)


@career_bp.route('/')
@login_required
def index():
    """Career recommendations dashboard."""
    profile = current_user.profile
    preferred_domain = profile.preferred_domain if profile else None

    # Find matching domains based on profile
    matched_domains = _get_matched_domains(profile)

    # Latest assessment for domain context
    latest_assessment = Assessment.query.filter_by(
        user_id=current_user.id
    ).order_by(Assessment.taken_at.desc()).first()

    return render_template('dashboard/career.html',
                           career_domains=CAREER_DOMAINS,
                           matched_domains=matched_domains,
                           preferred_domain=preferred_domain,
                           latest_assessment=latest_assessment)


@career_bp.route('/analyze', methods=['POST'])
@login_required
def analyze():
    """Get AI-powered career analysis."""
    profile = current_user.profile
    if not profile:
        return jsonify({'error': 'Please complete your profile first.'}), 400

    profile_data = {
        'name': profile.full_name or current_user.username,
        'education': profile.education or '',
        'career_goal': profile.career_goal or '',
        'skills': profile.skills_list,
        'interests': profile.interests_list,
        'experience_level': profile.experience_level or 'beginner',
    }

    system_prompt = build_system_prompt(profile_data)
    client = get_watsonx_client()

    message = f"""Based on my profile:
- Education: {profile_data['education']}
- Career Goal: {profile_data['career_goal']}
- Current Skills: {', '.join(profile_data['skills']) or 'None yet'}
- Experience: {profile_data['experience_level']}

Please provide:
1. My top 3 career path recommendations with salary ranges
2. Key skills I need to develop for each path
3. Estimated time to job-readiness for each path
4. Specific action steps I should take this month
5. Which path best matches my current profile and why

Format your response in a clear, encouraging way."""

    response = client.chat([{'role': 'user', 'content': message}], system_prompt)
    return jsonify({'analysis': response})


def _get_matched_domains(profile):
    """Return top matching career domains based on profile."""
    if not profile:
        return CAREER_DOMAINS[:4]

    matched = []
    skills_lower = [s.lower() for s in profile.skills_list]
    interests_lower = [i.lower() for i in profile.interests_list]
    goal_lower = (profile.career_goal or '').lower()

    for domain in CAREER_DOMAINS:
        score = 0
        domain_name_lower = domain['name'].lower()
        domain_id_lower = domain['id'].lower()

        # Check goal match
        if domain_id_lower in goal_lower or any(r.lower() in goal_lower for r in domain.get('job_roles', [])):
            score += 10

        # Check skills match
        for skill in domain.get('key_skills', []):
            if skill.lower() in skills_lower:
                score += 3

        # Check interests match
        for interest in interests_lower:
            if interest in domain_name_lower:
                score += 2

        # Preferred domain boost
        if profile.preferred_domain and profile.preferred_domain.lower() == domain_id_lower:
            score += 15

        matched.append({**domain, 'match_score': score})

    matched.sort(key=lambda x: x['match_score'], reverse=True)
    return matched
