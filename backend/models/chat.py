"""
chat.py - ChatMessage model for storing conversation history

Stores:
- Message content (user input or Sage response)
- Role (user/sage)
- Emotion detected from user message
- Explanation for Sage's response (XAI)
- Timestamps for conversation ordering
"""

from datetime import datetime
from . import db

class ChatMessage(db.Model):
    """Individual chat message between user and Sage"""
    
    __tablename__ = 'chat_messages'
    
    # Primary Key
    id = db.Column(db.Integer, primary_key=True)
    
    # Foreign Key to User (who sent/received this message)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Message content
    role = db.Column(db.String(20), nullable=False)  # 'user' or 'sage'
    message = db.Column(db.Text, nullable=False)     # The actual message text
    
    # Explainable AI (XAI) - Why Sage responded this way
    explanation = db.Column(db.Text)                 # Explanation for bot responses
    emotion = db.Column(db.String(50))               # Detected emotion ('sadness', 'anxiety', etc.)
    intent = db.Column(db.String(50))                # Detected intent ('journaling', 'mindfulness', etc.)
    confidence = db.Column(db.Float, default=0.0)    # ML confidence score (0-1)
    
    # Crisis detection flag
    is_crisis = db.Column(db.Boolean, default=False) # Was this a crisis message?
    
    # Metadata
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    # For future features (likes, feedback)
    user_rating = db.Column(db.Integer, nullable=True)  # User rated response 1-5 (optional)
    was_helpful = db.Column(db.Boolean, default=None)   # Did user find this helpful?
    
    # ==================== Factory Methods ====================
    
    @classmethod
    def create_user_message(cls, user_id, message):
        """
        Create a new user message
        Returns ChatMessage instance
        """
        return cls(
            user_id=user_id,
            role='user',
            message=message.strip(),
            timestamp=datetime.utcnow()
        )
    
    @classmethod
    def create_sage_response(cls, user_id, response_text, explanation=None, emotion=None, intent=None, confidence=0.0, is_crisis=False):
        """
        Create a new Sage bot response
        Returns ChatMessage instance
        """
        return cls(
            user_id=user_id,
            role='sage',
            message=response_text,
            explanation=explanation,
            emotion=emotion,
            intent=intent,
            confidence=confidence,
            is_crisis=is_crisis,
            timestamp=datetime.utcnow()
        )
    
    # ==================== Utility Methods ====================
    
    def is_user_message(self):
        """Check if message is from user"""
        return self.role == 'user'
    
    def is_bot_message(self):
        """Check if message is from Sage bot"""
        return self.role == 'sage'
    
    def mark_helpful(self):
        """Mark this response as helpful"""
        self.was_helpful = True
    
    def mark_not_helpful(self):
        """Mark this response as not helpful"""
        self.was_helpful = False
    
    def add_rating(self, rating):
        """Add user rating (1-5) for this response"""
        if 1 <= rating <= 5:
            self.user_rating = rating
    
    def to_dict(self):
        """
        Convert message to dictionary for API responses
        """
        return {
            'id': self.id,
            'role': self.role,
            'message': self.message,
            'explanation': self.explanation,
            'emotion': self.emotion,
            'intent': self.intent,
            'confidence': self.confidence,
            'is_crisis': self.is_crisis,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'was_helpful': self.was_helpful,
            'user_rating': self.user_rating
        }
    
    def to_preview_dict(self):
        """
        Minimal version for chat previews (shorter)
        """
        return {
            'id': self.id,
            'role': self.role,
            'message': self.message[:100] + ('...' if len(self.message) > 100 else ''),
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }
    
    def get_explainable_ai_text(self):
        """
        Generate human-readable explanation for why Sage responded this way
        Used for the "Why Sage said this" button
        """
        if not self.explanation:
            return "Sage responded based on general wellness guidelines."
        
        return self.explanation
    
    def __repr__(self):
        """String representation for debugging"""
        return f'<ChatMessage {self.role} user={self.user_id} at {self.timestamp}>'


# ==================== Conversation Manager ====================
# Helper class for managing chat conversations (not a database model)

class ConversationManager:
    """
    Utility class for managing chat conversations
    Not stored in database - used for session-based context
    """
    
    def __init__(self, max_context_length=10):
        self.messages = []
        self.max_context_length = max_context_length
    
    def add_message(self, role, content):
        """Add a message to conversation context"""
        self.messages.append({
            'role': role,
            'content': content
        })
        # Keep only recent messages for context
        if len(self.messages) > self.max_context_length:
            self.messages.pop(0)
    
    def get_context(self):
        """Get conversation context as list of recent messages"""
        return self.messages
    
    def clear(self):
        """Clear conversation context"""
        self.messages = []
    
    def get_last_user_message(self):
        """Get the most recent user message"""
        for msg in reversed(self.messages):
            if msg['role'] == 'user':
                return msg['content']
        return None
    
    def get_last_bot_message(self):
        """Get the most recent bot message"""
        for msg in reversed(self.messages):
            if msg['role'] == 'sage':
                return msg['content']
        return None