"""
session.py - UserSession model for tracking login sessions and JWT tokens

Stores:
- JWT token information for each login session
- IP address and user agent for security auditing
- Token expiration and revocation status
- Device information (browser, OS, device type)
"""

from datetime import datetime, timedelta
from . import db
import hashlib

class UserSession(db.Model):
    """User login session - tracks active JWT tokens"""
    
    __tablename__ = 'user_sessions'
    
    # Primary Key
    id = db.Column(db.Integer, primary_key=True)
    
    # Foreign Key to User
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Token Information
    token_jti = db.Column(db.String(100), unique=True, nullable=False, index=True)  # JWT ID (unique identifier)
    token_type = db.Column(db.String(20), default='access')  # 'access' or 'refresh'
    
    # Session Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)
    last_activity = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Device & Location Info (for security)
    ip_address = db.Column(db.String(45))  # IPv4 (15) or IPv6 (45) max length
    user_agent = db.Column(db.Text)        # Browser/OS info
    device_name = db.Column(db.String(100)) # 'Chrome on Windows', 'Safari on iPhone'
    
    # Session Status
    is_active = db.Column(db.Boolean, default=True)
    is_revoked = db.Column(db.Boolean, default=False)  # Manually revoked (logout)
    
    # Optional: Refresh token linking (for token refresh flow)
    refresh_token_jti = db.Column(db.String(100), nullable=True)  # Link to refresh session
    
    # ==================== Factory Methods ====================
    
    @classmethod
    def create_session(cls, user_id, token_jti, expires_at, ip_address=None, user_agent=None):
        """
        Create a new user session when user logs in
        """
        # Parse device info from user agent
        device_name = cls._parse_user_agent(user_agent)
        
        return cls(
            user_id=user_id,
            token_jti=token_jti,
            expires_at=expires_at,
            ip_address=ip_address,
            user_agent=user_agent,
            device_name=device_name,
            is_active=True,
            is_revoked=False
        )
    
    @classmethod
    def create_refresh_session(cls, user_id, access_token_jti, refresh_token_jti, expires_at, ip_address=None, user_agent=None):
        """
        Create a refresh session (for longer-lived authentication)
        """
        session = cls.create_session(user_id, refresh_token_jti, expires_at, ip_address, user_agent)
        session.token_type = 'refresh'
        session.refresh_token_jti = access_token_jti
        return session
    
    @staticmethod
    def _parse_user_agent(user_agent):
        """
        Parse user agent string to get readable device name
        Example: "Chrome 120 on Windows 11" or "Safari on iPhone"
        """
        if not user_agent:
            return "Unknown Device"
        
        user_agent_lower = user_agent.lower()
        
        # Detect browser
        browser = "Unknown Browser"
        if "chrome" in user_agent_lower and "edg" not in user_agent_lower:
            browser = "Chrome"
        elif "firefox" in user_agent_lower:
            browser = "Firefox"
        elif "safari" in user_agent_lower and "chrome" not in user_agent_lower:
            browser = "Safari"
        elif "edg" in user_agent_lower:
            browser = "Edge"
        elif "opera" in user_agent_lower:
            browser = "Opera"
        
        # Detect OS
        os_name = "Unknown OS"
        if "windows" in user_agent_lower:
            os_name = "Windows"
        elif "mac" in user_agent_lower:
            os_name = "macOS"
        elif "linux" in user_agent_lower:
            os_name = "Linux"
        elif "android" in user_agent_lower:
            os_name = "Android"
        elif "iphone" in user_agent_lower or "ipad" in user_agent_lower:
            os_name = "iOS"
        
        # Detect device type
        device = "Computer"
        if "mobile" in user_agent_lower or "android" in user_agent_lower:
            device = "Mobile"
        elif "tablet" in user_agent_lower or "ipad" in user_agent_lower:
            device = "Tablet"
        
        return f"{browser} on {os_name} ({device})"
    
    # ==================== Session Management Methods ====================
    
    def update_activity(self):
        """Update last activity timestamp"""
        self.last_activity = datetime.utcnow()
    
    def revoke(self):
        """
        Revoke this session (used on logout)
        This token can no longer be used for authentication
        """
        self.is_revoked = True
        self.is_active = False
    
    def expire(self):
        """Mark session as expired"""
        self.is_active = False
    
    def is_expired(self):
        """Check if session has expired"""
        return datetime.utcnow() > self.expires_at
    
    def extend_session(self, additional_days=7):
        """Extend session expiration (for "Remember Me" functionality)"""
        if self.is_active and not self.is_revoked:
            self.expires_at = datetime.utcnow() + timedelta(days=additional_days)
            self.update_activity()
            return True
        return False
    
    # ==================== Security Methods ====================
    
    def is_valid(self):
        """
        Check if session is still valid
        Returns True if:
        - Not revoked
        - Not expired
        - Active
        """
        return (not self.is_revoked and 
                not self.is_expired() and 
                self.is_active)
    
    def get_session_age_hours(self):
        """Get session age in hours"""
        age = datetime.utcnow() - self.created_at
        return round(age.total_seconds() / 3600, 1)
    
    def get_inactive_hours(self):
        """Get hours since last activity"""
        inactive = datetime.utcnow() - self.last_activity
        return round(inactive.total_seconds() / 3600, 1)
    
    # ==================== Serialization ====================
    
    def to_dict(self):
        """Convert session to dictionary for API responses"""
        return {
            'id': self.id,
            'device_name': self.device_name,
            'ip_address': self.ip_address,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'created_formatted': self.created_at.strftime('%b %d, %Y %I:%M %p') if self.created_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'last_activity': self.last_activity.isoformat() if self.last_activity else None,
            'is_active': self.is_active,
            'is_revoked': self.is_revoked,
            'session_age_hours': self.get_session_age_hours(),
            'inactive_hours': self.get_inactive_hours()
        }
    
    def __repr__(self):
        return f'<UserSession user={self.user_id} device={self.device_name} active={self.is_active}>'


# ==================== Session Manager Helper ====================

class SessionManager:
    """
    Utility class for managing user sessions across the application
    Handles cleanup, revocation, and validation
    """
    
    @staticmethod
    def revoke_all_user_sessions(user_id, db_session):
        """
        Revoke ALL active sessions for a user
        Used when user changes password or suspects compromise
        """
        sessions = UserSession.query.filter_by(
            user_id=user_id,
            is_active=True,
            is_revoked=False
        ).all()
        
        revoked_count = 0
        for session in sessions:
            session.revoke()
            revoked_count += 1
        
        db_session.commit()
        return revoked_count
    
    @staticmethod
    def revoke_other_sessions(user_id, current_session_id, db_session):
        """
        Revoke all sessions EXCEPT the current one
        Useful for "Log out from other devices" feature
        """
        sessions = UserSession.query.filter(
            UserSession.user_id == user_id,
            UserSession.id != current_session_id,
            UserSession.is_active == True,
            UserSession.is_revoked == False
        ).all()
        
        revoked_count = 0
        for session in sessions:
            session.revoke()
            revoked_count += 1
        
        db_session.commit()
        return revoked_count
    
    @staticmethod
    def cleanup_expired_sessions(db_session):
        """
        Delete or mark expired sessions
        Run this periodically (e.g., via cron job)
        """
        expired_sessions = UserSession.query.filter(
            UserSession.expires_at < datetime.utcnow(),
            UserSession.is_active == True
        ).all()
        
        cleaned_count = 0
        for session in expired_sessions:
            session.expire()
            cleaned_count += 1
        
        db_session.commit()
        return cleaned_count
    
    @staticmethod
    def get_active_sessions_count(user_id):
        """Get count of active sessions for a user"""
        return UserSession.query.filter(
            UserSession.user_id == user_id,
            UserSession.is_active == True,
            UserSession.is_revoked == False
        ).count()
    
    @staticmethod
    def get_session_by_token_jti(token_jti):
        """Find session by JWT ID"""
        return UserSession.query.filter_by(token_jti=token_jti).first()