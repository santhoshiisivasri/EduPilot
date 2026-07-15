"""EduPilot – Skill Assessment Routes"""
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from app.extensions import db
from app.models import Assessment, Achievement
from app.watsonx_client import get_watsonx_client
from app.agent_instructions import build_system_prompt, CAREER_DOMAINS

assessment_bp = Blueprint('assessment', __name__)

# Built-in assessment questions per domain
ASSESSMENT_QUESTIONS = {
    "frontend": [
        {"id": 0, "question": "What does CSS stand for?", "type": "short"},
        {"id": 1, "question": "Explain the difference between `display: block` and `display: flex`.", "type": "short"},
        {"id": 2, "question": "What is the purpose of JavaScript's `async/await`?", "type": "short"},
        {"id": 3, "question": "What is a React Hook? Name two common hooks.", "type": "short"},
        {"id": 4, "question": "Describe the CSS Box Model.", "type": "short"},
        {"id": 5, "question": "What is responsive design and how do you implement it?", "type": "short"},
        {"id": 6, "question": "What is the difference between `==` and `===` in JavaScript?", "type": "short"},
        {"id": 7, "question": "What is the DOM and how does JavaScript interact with it?", "type": "short"},
        {"id": 8, "question": "What is a REST API and how would you fetch data from one in JavaScript?", "type": "short"},
        {"id": 9, "question": "Describe your experience with version control (Git). What is a merge conflict?", "type": "short"},
    ],
    "backend": [
        {"id": 0, "question": "What is the difference between SQL and NoSQL databases?", "type": "short"},
        {"id": 1, "question": "Explain what an API endpoint is and how HTTP methods work.", "type": "short"},
        {"id": 2, "question": "What is middleware in the context of web frameworks?", "type": "short"},
        {"id": 3, "question": "What is authentication vs. authorization?", "type": "short"},
        {"id": 4, "question": "Describe the MVC (Model-View-Controller) architecture pattern.", "type": "short"},
        {"id": 5, "question": "What is database indexing and why is it important?", "type": "short"},
        {"id": 6, "question": "How does session management work in web applications?", "type": "short"},
        {"id": 7, "question": "What is caching and how would you implement it?", "type": "short"},
        {"id": 8, "question": "Explain the concept of microservices vs. monolithic architecture.", "type": "short"},
        {"id": 9, "question": "What is Docker and how does containerization help development?", "type": "short"},
    ],
    "datascience": [
        {"id": 0, "question": "What is the difference between supervised and unsupervised learning?", "type": "short"},
        {"id": 1, "question": "Explain the concept of overfitting and how to prevent it.", "type": "short"},
        {"id": 2, "question": "What Python libraries have you used for data analysis?", "type": "short"},
        {"id": 3, "question": "What is a confusion matrix and what does it tell you?", "type": "short"},
        {"id": 4, "question": "Explain the difference between mean, median, and mode.", "type": "short"},
        {"id": 5, "question": "What is feature engineering and why is it important?", "type": "short"},
        {"id": 6, "question": "What is cross-validation and why do we use it?", "type": "short"},
        {"id": 7, "question": "Describe the steps in a typical data science project.", "type": "short"},
        {"id": 8, "question": "What is the difference between correlation and causation?", "type": "short"},
        {"id": 9, "question": "What is a p-value and how is it used in hypothesis testing?", "type": "short"},
    ],
    "default": [
        {"id": 0, "question": "Describe your current experience with programming.", "type": "short"},
        {"id": 1, "question": "What programming languages are you familiar with?", "type": "short"},
        {"id": 2, "question": "Describe a technical project you've worked on.", "type": "short"},
        {"id": 3, "question": "What is version control and have you used Git?", "type": "short"},
        {"id": 4, "question": "How comfortable are you with command line/terminal?", "type": "short"},
        {"id": 5, "question": "What are your strongest technical skills?", "type": "short"},
        {"id": 6, "question": "What areas do you feel you need to improve the most?", "type": "short"},
        {"id": 7, "question": "Describe how you approach solving a complex technical problem.", "type": "short"},
        {"id": 8, "question": "Have you contributed to any open source projects?", "type": "short"},
        {"id": 9, "question": "What's your learning goal for the next 3 months?", "type": "short"},
    ]
}


@assessment_bp.route('/')
@login_required
def index():
    """Assessment selection page."""
    past_assessments = Assessment.query.filter_by(user_id=current_user.id)\
        .order_by(Assessment.taken_at.desc()).limit(5).all()
    return render_template('dashboard/assessment.html',
                           career_domains=CAREER_DOMAINS,
                           past_assessments=past_assessments)


@assessment_bp.route('/start/<domain>')
@login_required
def start(domain):
    """Start an assessment for a domain."""
    questions = ASSESSMENT_QUESTIONS.get(domain.lower(),
                                         ASSESSMENT_QUESTIONS['default'])
    return render_template('dashboard/assessment.html',
                           domain=domain,
                           questions=questions,
                           career_domains=CAREER_DOMAINS,
                           taking_assessment=True,
                           past_assessments=[])


@assessment_bp.route('/submit', methods=['POST'])
@login_required
def submit():
    """Submit and AI-evaluate an assessment."""
    data = request.get_json()
    domain = data.get('domain', 'general')
    answers = data.get('answers', {})

    questions = ASSESSMENT_QUESTIONS.get(domain.lower(), ASSESSMENT_QUESTIONS['default'])

    # Build profile for system prompt
    profile = current_user.profile
    profile_data = {}
    if profile:
        profile_data = {
            'name': profile.full_name or current_user.username,
            'education': profile.education or '',
            'career_goal': profile.career_goal or '',
            'skills': profile.skills_list,
            'experience_level': profile.experience_level or 'beginner',
        }

    system_prompt = build_system_prompt(profile_data)
    client = get_watsonx_client()

    # AI evaluation
    result = client.evaluate_assessment(domain, questions, answers, system_prompt)

    # Save assessment
    assessment = Assessment(
        user_id=current_user.id,
        domain=domain,
        score=result.get('score', 60),
        feedback=result.get('feedback', 'Good effort!')
    )
    assessment.questions_list = questions
    assessment.answers_dict = answers
    db.session.add(assessment)
    db.session.commit()

    # Award assessment badge
    _check_assessment_badge(current_user.id, result.get('score', 0))

    return jsonify({
        'assessment_id': assessment.id,
        'score': assessment.score,
        'grade': result.get('grade', 'Good'),
        'feedback': result.get('feedback', ''),
        'strengths': result.get('strengths', []),
        'gaps': result.get('gaps', []),
        'recommendations': result.get('recommendations', []),
        'next_steps': result.get('next_steps', '')
    })


def _check_assessment_badge(user_id, score):
    existing = Achievement.query.filter_by(user_id=user_id, badge_name='Assessment Taker').first()
    if not existing:
        badge = Achievement(
            user_id=user_id,
            badge_name='Assessment Taker',
            badge_icon='bi-pencil-square',
            badge_color='#BB8FCE',
            description='Completed your first skill assessment!'
        )
        db.session.add(badge)

    if score >= 80:
        existing_ace = Achievement.query.filter_by(user_id=user_id, badge_name='Assessment Ace').first()
        if not existing_ace:
            ace_badge = Achievement(
                user_id=user_id,
                badge_name='Assessment Ace',
                badge_icon='bi-patch-exclamation-fill',
                badge_color='#FFD700',
                description='Scored 80%+ on a skill assessment!'
            )
            db.session.add(ace_badge)

    db.session.commit()
