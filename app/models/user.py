from datetime import datetime
from app import db
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from time import time
import json
from sqlalchemy.dialects.postgresql import JSONB

class User(db.Model):
    """User model with SDA-focused profile"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, index=True)
    email = db.Column(db.String(120), unique=True, index=True)
    password_hash = db.Column(db.String(128))
    email_verified = db.Column(db.Boolean, default=False)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Profile
    profile = db.Column(JSONB, default={
        'sabbath_preferences': {
            'preparation_start_hour': 14,  # Default to Friday 2 PM
            'notification_hours_before': 24,
            'auto_mode': True
        },
        'spiritual_goals': {
            'bible_study': {
                'daily_chapters': 1,
                'study_time_minutes': 30,
                'memorization_verses_per_week': 1
            },
            'prayer': {
                'morning_prayer': True,
                'evening_prayer': True,
                'prayer_time_minutes': 15
            },
            'health': {
                'rest_hours': 8,
                'water_glasses': 8,
                'exercise_minutes': 30
            }
        },
        'doctrinal_interests': [
            'sabbath',
            'health_message',
            'prophecy',
            'sanctuary'
        ],
        'ministry_involvement': []
    })
    
    # Relationships
    spiritual_records = db.relationship('SpiritualRecord', backref='user', lazy='dynamic')
    prayer_requests = db.relationship('PrayerRequest', backref='user', lazy='dynamic')
    bible_studies = db.relationship('BibleStudy', backref='user', lazy='dynamic')
    
    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        if self.profile is None:
            self.profile = {}
    
    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')
    
    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def generate_auth_token(self, expiration=3600):
        """Generate JWT token"""
        return jwt.encode(
            {'user_id': self.id, 'exp': time() + expiration},
            current_app.config['SECRET_KEY'],
            algorithm='HS256'
        )
    
    def update_last_seen(self):
        """Update last seen timestamp"""
        self.last_seen = datetime.utcnow()
        db.session.add(self)
    
    def update_profile(self, updates):
        """Update user profile"""
        if isinstance(self.profile, str):
            self.profile = json.loads(self.profile)
        self.profile.update(updates)
        db.session.add(self)
    
    def get_reset_password_token(self, expires_in=600):
        """Generate password reset token"""
        return jwt.encode(
            {'reset_password': self.id, 'exp': time() + expires_in},
            current_app.config['SECRET_KEY'],
            algorithm='HS256'
        )
    
    @staticmethod
    def verify_reset_password_token(token):
        """Verify password reset token"""
        try:
            id = jwt.decode(
                token,
                current_app.config['SECRET_KEY'],
                algorithms=['HS256']
            )['reset_password']
        except:
            return None
        return User.query.get(id)
    
    def to_dict(self):
        """Convert user to dictionary"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'email_verified': self.email_verified,
            'active': self.active,
            'created_at': self.created_at.isoformat(),
            'last_seen': self.last_seen.isoformat(),
            'profile': self.profile
        }
    
    def __repr__(self):
        return f'<User {self.username}>'

class SpiritualRecord(db.Model):
    """Model for tracking spiritual growth records"""
    __tablename__ = 'spiritual_records'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    date = db.Column(db.Date, default=datetime.utcnow().date)
    category = db.Column(db.String(64))  # bible_study, prayer, service, health
    metrics = db.Column(JSONB)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class PrayerRequest(db.Model):
    """Model for prayer requests"""
    __tablename__ = 'prayer_requests'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    title = db.Column(db.String(128))
    request = db.Column(db.Text)
    is_answered = db.Column(db.Boolean, default=False)
    answer_notes = db.Column(db.Text)
    is_private = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    answered_at = db.Column(db.DateTime)

class BibleStudy(db.Model):
    """Model for Bible study tracking"""
    __tablename__ = 'bible_studies'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    date = db.Column(db.Date, default=datetime.utcnow().date)
    book = db.Column(db.String(64))
    chapter = db.Column(db.Integer)
    verses = db.Column(db.String(64))  # e.g., "1-5,7,9-12"
    notes = db.Column(db.Text)
    duration_minutes = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
