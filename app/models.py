"""
EduPilot – Database Models
Defines all SQLAlchemy ORM models for the application.
"""
import json
from datetime import datetime, timezone
from flask_login import UserMixin
from app.extensions import db, login_manager


# ─── User Loader ───────────────────────────────────────────
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ─── User Model ────────────────────────────────────────────
class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), default='student')  # student / admin
    is_active_account = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    last_login = db.Column(db.DateTime)

    # Relationships
    profile = db.relationship('Profile', backref='user', uselist=False, cascade='all, delete-orphan')
    chat_messages = db.relationship('ChatMessage', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    roadmaps = db.relationship('Roadmap', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    assessments = db.relationship('Assessment', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    achievements = db.relationship('Achievement', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    study_plans = db.relationship('StudyPlan', backref='user', lazy='dynamic', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<User {self.username}>'

    @property
    def is_admin(self):
        return self.role == 'admin'

    def get_career_readiness_score(self):
        """Calculate a career readiness score based on profile completion and progress."""
        score = 0
        if self.profile:
            p = self.profile
            if p.full_name: score += 10
            if p.education: score += 10
            if p.career_goal: score += 15
            if p.skills_list: score += 15
            if p.interests_list: score += 10
            if p.learning_style: score += 10
            if p.study_hours_per_week: score += 5
        # Assessment bonus
        latest_assessment = Assessment.query.filter_by(user_id=self.id).order_by(Assessment.taken_at.desc()).first()
        if latest_assessment:
            score += min(25, int(latest_assessment.score * 0.25))
        return min(100, score)


# ─── Profile Model ─────────────────────────────────────────
class Profile(db.Model):
    __tablename__ = 'profiles'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    full_name = db.Column(db.String(150))
    avatar = db.Column(db.String(255), default='default_avatar.png')
    education = db.Column(db.String(200))  # e.g. "B.Tech Computer Science"
    institution = db.Column(db.String(200))
    graduation_year = db.Column(db.Integer)
    career_goal = db.Column(db.String(300))
    experience_level = db.Column(db.String(50), default='beginner')  # beginner/intermediate/advanced
    learning_style = db.Column(db.String(100))  # visual/auditory/kinesthetic/reading-writing
    study_hours_per_week = db.Column(db.Integer, default=10)
    bio = db.Column(db.Text)
    preferred_domain = db.Column(db.String(100))
    dark_mode = db.Column(db.Boolean, default=False)
    email_notifications = db.Column(db.Boolean, default=True)

    # JSON stored as strings
    _skills = db.Column('skills', db.Text, default='[]')
    _interests = db.Column('interests', db.Text, default='[]')

    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    @property
    def skills_list(self):
        try:
            return json.loads(self._skills) if self._skills else []
        except (json.JSONDecodeError, TypeError):
            return []

    @skills_list.setter
    def skills_list(self, value):
        self._skills = json.dumps(value if isinstance(value, list) else [])

    @property
    def interests_list(self):
        try:
            return json.loads(self._interests) if self._interests else []
        except (json.JSONDecodeError, TypeError):
            return []

    @interests_list.setter
    def interests_list(self, value):
        self._interests = json.dumps(value if isinstance(value, list) else [])

    def completion_percentage(self):
        fields = [self.full_name, self.education, self.career_goal,
                  self._skills, self._interests, self.learning_style,
                  self.study_hours_per_week, self.preferred_domain]
        filled = sum(1 for f in fields if f and f not in ['[]', '', None, 0])
        return int((filled / len(fields)) * 100)


# ─── Chat Message Model ────────────────────────────────────
class ChatMessage(db.Model):
    __tablename__ = 'chat_messages'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'user' or 'assistant'
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            'id': self.id,
            'role': self.role,
            'content': self.content,
            'timestamp': self.timestamp.isoformat()
        }


# ─── Roadmap Model ─────────────────────────────────────────
class Roadmap(db.Model):
    __tablename__ = 'roadmaps'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    domain = db.Column(db.String(100), nullable=False)
    title = db.Column(db.String(200))
    status = db.Column(db.String(20), default='active')  # active/completed/paused
    generated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    milestones = db.relationship('RoadmapMilestone', backref='roadmap', lazy='dynamic', cascade='all, delete-orphan')

    def completion_percentage(self):
        total = self.milestones.count()
        if total == 0:
            return 0
        completed = self.milestones.filter_by(completed=True).count()
        return int((completed / total) * 100)


# ─── Roadmap Milestone Model ───────────────────────────────
class RoadmapMilestone(db.Model):
    __tablename__ = 'roadmap_milestones'

    id = db.Column(db.Integer, primary_key=True)
    roadmap_id = db.Column(db.Integer, db.ForeignKey('roadmaps.id'), nullable=False)
    level = db.Column(db.String(20), nullable=False)  # beginner/intermediate/advanced
    order = db.Column(db.Integer, default=0)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    duration_weeks = db.Column(db.Integer, default=2)
    completed = db.Column(db.Boolean, default=False)
    completed_at = db.Column(db.DateTime)

    _resources = db.Column('resources', db.Text, default='[]')
    _projects = db.Column('projects', db.Text, default='[]')
    _certifications = db.Column('certifications', db.Text, default='[]')

    @property
    def resources_list(self):
        try:
            return json.loads(self._resources) if self._resources else []
        except (json.JSONDecodeError, TypeError):
            return []

    @resources_list.setter
    def resources_list(self, value):
        self._resources = json.dumps(value if isinstance(value, list) else [])

    @property
    def projects_list(self):
        try:
            return json.loads(self._projects) if self._projects else []
        except (json.JSONDecodeError, TypeError):
            return []

    @projects_list.setter
    def projects_list(self, value):
        self._projects = json.dumps(value if isinstance(value, list) else [])

    @property
    def certifications_list(self):
        try:
            return json.loads(self._certifications) if self._certifications else []
        except (json.JSONDecodeError, TypeError):
            return []

    @certifications_list.setter
    def certifications_list(self, value):
        self._certifications = json.dumps(value if isinstance(value, list) else [])


# ─── Assessment Model ──────────────────────────────────────
class Assessment(db.Model):
    __tablename__ = 'assessments'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    domain = db.Column(db.String(100), nullable=False)
    score = db.Column(db.Float, default=0.0)
    feedback = db.Column(db.Text)
    taken_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    _questions = db.Column('questions', db.Text, default='[]')
    _answers = db.Column('answers', db.Text, default='{}')

    @property
    def questions_list(self):
        try:
            return json.loads(self._questions) if self._questions else []
        except (json.JSONDecodeError, TypeError):
            return []

    @questions_list.setter
    def questions_list(self, value):
        self._questions = json.dumps(value if isinstance(value, list) else [])

    @property
    def answers_dict(self):
        try:
            return json.loads(self._answers) if self._answers else {}
        except (json.JSONDecodeError, TypeError):
            return {}

    @answers_dict.setter
    def answers_dict(self, value):
        self._answers = json.dumps(value if isinstance(value, dict) else {})

    def grade_label(self):
        if self.score >= 80:
            return 'Excellent'
        elif self.score >= 60:
            return 'Good'
        elif self.score >= 40:
            return 'Average'
        return 'Needs Improvement'


# ─── Achievement / Badge Model ─────────────────────────────
class Achievement(db.Model):
    __tablename__ = 'achievements'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    badge_name = db.Column(db.String(100), nullable=False)
    badge_icon = db.Column(db.String(50), default='bi-award')
    badge_color = db.Column(db.String(20), default='gold')
    description = db.Column(db.String(300))
    earned_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))


# ─── Study Plan Model ──────────────────────────────────────
class StudyPlan(db.Model):
    __tablename__ = 'study_plans'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    week_start = db.Column(db.Date, nullable=False)
    total_hours = db.Column(db.Float, default=0.0)
    ai_generated = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    _daily_goals = db.Column('daily_goals', db.Text, default='{}')

    @property
    def daily_goals_dict(self):
        try:
            return json.loads(self._daily_goals) if self._daily_goals else {}
        except (json.JSONDecodeError, TypeError):
            return {}

    @daily_goals_dict.setter
    def daily_goals_dict(self, value):
        self._daily_goals = json.dumps(value if isinstance(value, dict) else {})


# ─── Course Recommendation Model ───────────────────────────
class CourseRecommendation(db.Model):
    __tablename__ = 'course_recommendations'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    course_title = db.Column(db.String(200), nullable=False)
    provider = db.Column(db.String(100))  # Coursera, Udemy, edX, etc.
    url = db.Column(db.String(500))
    difficulty = db.Column(db.String(50))  # Beginner/Intermediate/Advanced
    domain = db.Column(db.String(100))
    duration = db.Column(db.String(50))
    is_free = db.Column(db.Boolean, default=False)
    rating = db.Column(db.Float, default=0.0)
    added_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    is_completed = db.Column(db.Boolean, default=False)
    completed_at = db.Column(db.DateTime)
