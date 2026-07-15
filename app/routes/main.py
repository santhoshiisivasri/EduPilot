"""EduPilot – Main routes (landing page, home)"""
from flask import Blueprint, render_template, redirect, url_for
from flask_login import current_user
from app.agent_instructions import CAREER_DOMAINS

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    return render_template('landing.html', career_domains=CAREER_DOMAINS)


@main_bp.route('/about')
def about():
    return render_template('landing.html', career_domains=CAREER_DOMAINS, scroll_to='about')
