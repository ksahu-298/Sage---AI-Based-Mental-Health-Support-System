"""
user.py - User model for authentication, profile, and gamification

Stores:
- Basic user info (username, email, password)
- Gamification data (streak, badges)
- Account status (active, created_at)
- Relationships to other data (chat, mood, journal)
"""

from datetime import datetime
from . import db
import json

class User(db.Model):
    """User account model"""
    
    __tablename__ = 'users'
    
    # Primary Key
    id = db.Column(db.Integer, primary_key=True)
    
    # Authentication fields
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, index=True)
    password_hash = db.Column(db.String(200))  # Store hashed password, never plain text
    
    # Google OAuth (optional)
    google_id = db.Column(db.String(100), unique=True, nullable=True)
    avatar = db.Column(db.String(500))  # Profile picture URL from Google
    
    # Gamification & Streaks
    streak = db.Column(db.Integer, default=0)  # Current consecutive check-in days
    longest_streak = db.Column(db.Integer, default=0)  # Personal best streak
    last_checkin = db.Column(db.String(20))  # Date of last check-in (YYYY-MM-DD)
    total_checkins = db.Column(db.Integer, default=0)  # Total mood check-ins ever
    
    # Badges (stored as JSON array)
    _badges = db.Column('badges', db.Text, default='[]')
    
    # Account metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    is_admin = db.Column(db.Boolean, default=False)
    
    # User preferences (stored as JSON)
    _preferences = db.Column('preferences', db.Text, default='{}')
    
    # Relationships (links to other tables)
    # These create virtual connections - not actual database columns
    chat_messages = db.relationship('ChatMessage', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    mood_entries = db.relationship('MoodEntry', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    journal_entries = db.relationship('JournalEntry', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    sessions = db.relationship('UserSession', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    
    # ==================== Property Getters/Setters for JSON Fields ====================
    
    @property
    def badges(self):
        """Get badges as Python list (converts from JSON)"""
        if self._badges:
            return json.loads(self._badges)
        return []
    
    @badges.setter
    def badges(self, value):
        """Set badges from Python list (converts to JSON for storage)"""
        if value is None:
            self._badges = '[]'
        else:
            self._badges = json.dumps(value)
    
    @property
    def preferences(self):
        """Get user preferences as Python dict"""
        if self._preferences:
            return json.loads(self._preferences)
        return {}
    
    @preferences.setter
    def preferences(self, value):
        """Set user preferences from Python dict"""
        if value is None:
            self._preferences = '{}'
        else:
            self._preferences = json.dumps(value)
    
    # ==================== Badge Management ====================
    
    def add_badge(self, badge_name):
        """Add a badge to user's collection if not already earned"""
        current_badges = self.badges
        if badge_name not in current_badges:
            current_badges.append(badge_name)
            self.badges = current_badges
            return True
        return False
    
    def has_badge(self, badge_name):
        """Check if user has earned a specific badge"""
        return badge_name in self.badges
    
    def get_unlocked_badges(self):
        """Return list of all badges user has earned"""
        return self.badges
    
    def get_locked_badges(self):
        """Return list of badges user hasn't earned yet"""
        all_badges = [
            {'name': 'First Step', 'requirement': 'Complete first mood check-in', 'icon': '👣'},
            {'name': 'Resilience Star', 'requirement': '7 day streak', 'icon': '⭐'},
            {'name': 'Mindful Warrior', 'requirement': '14 day streak', 'icon': '🧘'},
            {'name': 'Wellness Champion', 'requirement': '30 day streak', 'icon': '🏆'},
            {'name': 'Journal Keeper', 'requirement': 'Write 10 journal entries', 'icon': '📔'},
            {'name': 'Emotion Explorer', 'requirement': 'Log 5 different moods', 'icon': '🎭'},
            {'name': 'Chat Companion', 'requirement': 'Send 50 messages to Sage', 'icon': '💬'}
        ]
        
        earned = self.badges
        locked = [b for b in all_badges if b['name'] not in earned]
        return locked
    
    # ==================== Streak Management ====================
    
    def update_streak(self, today_date):
        """
        Update user's streak based on today's check-in
        Returns: (new_streak, is_new_record)
        """
        from ..utils.helpers import get_yesterday_date
        
        yesterday = get_yesterday_date()
        
        if self.last_checkin == today_date:
            # Already checked in today
            return self.streak, False
        
        if self.last_checkin == yesterday:
            # Consecutive day - increase streak
            self.streak += 1
        else:
            # Streak broken - start over
            self.streak = 1
        
        # Update longest streak if this is a new record
        is_new_record = False
        if self.streak > self.longest_streak:
            self.longest_streak = self.streak
            is_new_record = True
        
        # Update last check-in date
        self.last_checkin = today_date
        self.total_checkins += 1
        
        return self.streak, is_new_record
    
    def check_and_award_badges(self):
        """
        Check streak and award badges if conditions met
        Returns list of newly awarded badges
        """
        new_badges = []
        
        # Streak-based badges
        if self.streak >= 7 and not self.has_badge('Resilience Star'):
            self.add_badge('Resilience Star')
            new_badges.append('Resilience Star')
        
        if self.streak >= 14 and not self.has_badge('Mindful Warrior'):
            self.add_badge('Mindful Warrior')
            new_badges.append('Mindful Warrior')
        
        if self.streak >= 30 and not self.has_badge('Wellness Champion'):
            self.add_badge('Wellness Champion')
            new_badges.append('Wellness Champion')
        
        # First check-in badge
        if self.total_checkins >= 1 and not self.has_badge('First Step'):
            self.add_badge('First Step')
            new_badges.append('First Step')
        
        return new_badges
    
    # ==================== Utility Methods ====================
    
    def to_dict(self):
        """
        Convert user object to dictionary (for API responses)
        Never includes sensitive data like password_hash
        """
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'avatar': self.avatar,
            'streak': self.streak,
            'longest_streak': self.longest_streak,
            'total_checkins': self.total_checkins,
            'badges': self.badges,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'is_active': self.is_active,
            'preferences': self.preferences
        }
    
    def to_public_dict(self):
        """
        Public profile (even less data - for displaying to others)
        Currently just username, but can be expanded
        """
        return {
            'username': self.username,
            'avatar': self.avatar,
            'streak': self.streak,
            'badges': self.badges[:3]  # Show only top 3 badges
        }
    
    def __repr__(self):
        """String representation for debugging"""
        return f'<User {self.username}>'