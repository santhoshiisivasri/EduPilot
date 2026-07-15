"""EduPilot – AI Chat Routes (IBM Watsonx.ai Granite)"""
from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from app.extensions import db
from app.models import ChatMessage, Achievement
from app.watsonx_client import get_watsonx_client
from app.agent_instructions import build_system_prompt, AGENT_PERSONA

chat_bp = Blueprint('chat', __name__)


@chat_bp.route('/')
@login_required
def index():
    """AI Chat Coach page."""
    # Get chat history (last 30 messages)
    history = ChatMessage.query.filter_by(user_id=current_user.id)\
        .order_by(ChatMessage.timestamp.asc())\
        .limit(30).all()

    return render_template('dashboard/chat.html',
                           history=history,
                           agent_name=AGENT_PERSONA['name'])


@chat_bp.route('/send', methods=['POST'])
@login_required
def send():
    """Send a message to the AI coach and get a response."""
    data = request.get_json()
    if not data or 'message' not in data:
        return jsonify({'error': 'No message provided'}), 400

    user_message = data['message'].strip()
    if not user_message:
        return jsonify({'error': 'Empty message'}), 400

    if len(user_message) > 2000:
        return jsonify({'error': 'Message too long (max 2000 characters)'}), 400

    # Save user message
    user_msg = ChatMessage(
        user_id=current_user.id,
        role='user',
        content=user_message
    )
    db.session.add(user_msg)
    db.session.commit()

    # Build profile context for system prompt
    profile = current_user.profile
    profile_data = {}
    if profile:
        profile_data = {
            'name': profile.full_name or current_user.username,
            'education': profile.education or '',
            'career_goal': profile.career_goal or '',
            'skills': profile.skills_list,
            'interests': profile.interests_list,
            'experience_level': profile.experience_level or 'beginner',
            'learning_style': profile.learning_style or '',
            'study_hours': profile.study_hours_per_week or 10,
        }

    system_prompt = build_system_prompt(profile_data)

    # Build conversation history for context
    history = ChatMessage.query.filter_by(user_id=current_user.id)\
        .order_by(ChatMessage.timestamp.desc())\
        .limit(20).all()
    history.reverse()

    messages = [{'role': msg.role, 'content': msg.content} for msg in history]

    # Get AI response
    client = get_watsonx_client()
    ai_response = client.chat(messages, system_prompt)

    # Save AI response
    ai_msg = ChatMessage(
        user_id=current_user.id,
        role='assistant',
        content=ai_response
    )
    db.session.add(ai_msg)
    db.session.commit()

    # Award first chat badge
    _check_chat_badge(current_user.id)

    return jsonify({
        'response': ai_response,
        'timestamp': ai_msg.timestamp.isoformat()
    })


@chat_bp.route('/history')
@login_required
def history():
    """Get chat history as JSON."""
    msgs = ChatMessage.query.filter_by(user_id=current_user.id)\
        .order_by(ChatMessage.timestamp.asc()).all()
    return jsonify([m.to_dict() for m in msgs])


@chat_bp.route('/clear', methods=['POST'])
@login_required
def clear():
    """Clear chat history."""
    ChatMessage.query.filter_by(user_id=current_user.id).delete()
    db.session.commit()
    return jsonify({'status': 'cleared'})


def _check_chat_badge(user_id):
    """Award first message badge."""
    msg_count = ChatMessage.query.filter_by(user_id=user_id, role='user').count()
    existing = Achievement.query.filter_by(user_id=user_id, badge_name='First Chat').first()
    if msg_count >= 1 and not existing:
        badge = Achievement(
            user_id=user_id,
            badge_name='First Chat',
            badge_icon='bi-chat-heart',
            badge_color='#FF6B6B',
            description='Started your first conversation with Aria!'
        )
        db.session.add(badge)
        db.session.commit()
