"""
mood.py - MoodEntry model for daily mood check-ins and tracking

Stores:
- Mood score (1-10, where 1=very low, 10=amazing)
- Date of check-in (one entry per user per day)
- Optional note/journal entry about the mood
- Timestamp for when it was recorded
"""

from datetime import datetime
from . import db

class MoodEntry(db.Model):
    """Daily mood check-in entry"""
    
    __tablename__ = 'mood_entries'
    
    # Primary Key
    id = db.Column(db.Integer, primary_key=True)
    
    # Foreign Key to User
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Mood Data
    mood_score = db.Column(db.Integer, nullable=False)  # 1-10 scale
    date = db.Column(db.String(20), nullable=False, index=True)  # YYYY-MM-DD format
    note = db.Column(db.Text)  # Optional: user can add a note about their mood
    
    # Additional context (optional)
    time_of_day = db.Column(db.String(20))  # 'morning', 'afternoon', 'evening', 'night'
    activity_before = db.Column(db.String(100))  # What they were doing before check-in
    sleep_hours = db.Column(db.Float)  # Optional: sleep tracking
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # ==================== Constraints ====================
    # Ensure one mood entry per user per day
    __table_args__ = (
        db.UniqueConstraint('user_id', 'date', name='unique_user_mood_per_day'),
    )
    
    # ==================== Factory Methods ====================
    
    @classmethod
    def create_entry(cls, user_id, mood_score, date=None, note=None, time_of_day=None, activity_before=None, sleep_hours=None):
        """
        Create a new mood entry
        If date not provided, uses today's date
        """
        if date is None:
            from ..utils.helpers import get_today_date
            date = get_today_date()
        
        return cls(
            user_id=user_id,
            mood_score=mood_score,
            date=date,
            note=note,
            time_of_day=time_of_day,
            activity_before=activity_before,
            sleep_hours=sleep_hours
        )
    
    # ==================== Mood Score Helpers ====================
    
    def get_mood_label(self):
        """Convert mood score to descriptive label"""
        if self.mood_score >= 9:
            return "Amazing"
        elif self.mood_score >= 7:
            return "Good"
        elif self.mood_score >= 5:
            return "Okay"
        elif self.mood_score >= 3:
            return "Low"
        else:
            return "Very Low"
    
    def get_mood_emoji(self):
        """Get emoji representation of mood score"""
        if self.mood_score >= 9:
            return "😍"
        elif self.mood_score >= 7:
            return "😊"
        elif self.mood_score >= 5:
            return "🙂"
        elif self.mood_score >= 3:
            return "😐"
        else:
            return "😔"
    
    def get_mood_color(self):
        """Get CSS color for mood score (for graphs)"""
        if self.mood_score >= 9:
            return "#4CAF50"  # Green - Excellent
        elif self.mood_score >= 7:
            return "#8BC34A"  # Light Green - Good
        elif self.mood_score >= 5:
            return "#FFC107"  # Yellow - Okay
        elif self.mood_score >= 3:
            return "#FF9800"  # Orange - Low
        else:
            return "#F44336"  # Red - Very Low
    
    # ==================== Date Helpers ====================
    
    def is_today(self):
        """Check if this entry is from today"""
        from ..utils.helpers import get_today_date
        return self.date == get_today_date()
    
    def is_yesterday(self):
        """Check if this entry is from yesterday"""
        from ..utils.helpers import get_yesterday_date
        return self.date == get_yesterday_date()
    
    def days_ago(self):
        """Calculate how many days ago this entry was made"""
        from datetime import datetime
        entry_date = datetime.strptime(self.date, '%Y-%m-%d')
        today = datetime.now()
        diff = today - entry_date
        return diff.days
    
    # ==================== Serialization ====================
    
    def to_dict(self):
        """Convert mood entry to dictionary for API responses"""
        return {
            'id': self.id,
            'mood_score': self.mood_score,
            'mood_label': self.get_mood_label(),
            'mood_emoji': self.get_mood_emoji(),
            'date': self.date,
            'note': self.note,
            'time_of_day': self.time_of_day,
            'activity_before': self.activity_before,
            'sleep_hours': self.sleep_hours,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def to_chart_data(self):
        """Format for chart.js graph"""
        return {
            'date': self.date,
            'score': self.mood_score,
            'label': self.get_mood_label(),
            'emoji': self.get_mood_emoji()
        }
    
    def __repr__(self):
        return f'<MoodEntry user={self.user_id} date={self.date} score={self.mood_score}>'


# ==================== Mood Statistics Helper ====================

class MoodStatistics:
    """Helper class for calculating mood statistics"""
    
    @staticmethod
    def get_average_mood(entries):
        """Calculate average mood score from list of entries"""
        if not entries:
            return 0
        total = sum(e.mood_score for e in entries)
        return round(total / len(entries), 1)
    
    @staticmethod
    def get_weekly_average(entries):
        """Calculate weekly average (last 7 days)"""
        from ..utils.helpers import get_week_ago_date
        
        week_ago = get_week_ago_date()
        week_entries = [e for e in entries if e.date >= week_ago]
        return MoodStatistics.get_average_mood(week_entries)
    
    @staticmethod
    def get_monthly_average(entries):
        """Calculate monthly average (last 30 days)"""
        from datetime import datetime, timedelta
        
        month_ago = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        month_entries = [e for e in entries if e.date >= month_ago]
        return MoodStatistics.get_average_mood(month_entries)
    
    @staticmethod
    def get_trend(entries):
        """
        Determine mood trend (improving, stable, declining)
        Returns 'improving', 'stable', or 'declining'
        """
        if len(entries) < 3:
            return 'stable'
        
        # Compare first third to last third
        third = len(entries) // 3
        first_avg = MoodStatistics.get_average_mood(entries[:third])
        last_avg = MoodStatistics.get_average_mood(entries[-third:])
        
        difference = last_avg - first_avg
        if difference > 0.5:
            return 'improving'
        elif difference < -0.5:
            return 'declining'
        else:
            return 'stable'
    
    @staticmethod
    def get_best_day(entries):
        """Find the day with highest mood score"""
        if not entries:
            return None
        best = max(entries, key=lambda e: e.mood_score)
        return {'date': best.date, 'score': best.mood_score, 'note': best.note}
    
    @staticmethod
    def get_worst_day(entries):
        """Find the day with lowest mood score"""
        if not entries:
            return None
        worst = min(entries, key=lambda e: e.mood_score)
        return {'date': worst.date, 'score': worst.mood_score, 'note': worst.note}