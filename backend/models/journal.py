"""
journal.py - JournalEntry model for private journaling

Stores:
- Journal title and content (user's private thoughts)
- Prompt used (optional - which prompt inspired the entry)
- Associated mood and emotion tags
- Timestamps for creation and last update
"""

from datetime import datetime
from . import db

class JournalEntry(db.Model):
    """Private journal entry written by user"""
    
    __tablename__ = 'journal_entries'
    
    # Primary Key
    id = db.Column(db.Integer, primary_key=True)
    
    # Foreign Key to User
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Journal Content
    title = db.Column(db.String(200))
    content = db.Column(db.Text, nullable=False)
    
    # Metadata
    prompt_used = db.Column(db.String(200))  # Which prompt inspired this entry
    mood_score = db.Column(db.Integer)       # Optional: mood at time of writing (1-10)
    emotion_tags = db.Column(db.String(200)) # Comma-separated tags: "sadness,anxiety"
    
    # Privacy & Status
    is_private = db.Column(db.Boolean, default=True)  # Always true for now, but extensible
    is_favorite = db.Column(db.Boolean, default=False)  # User can star important entries
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # ==================== Factory Methods ====================
    
    @classmethod
    def create_entry(cls, user_id, content, title=None, prompt_used=None, mood_score=None, emotion_tags=None):
        """
        Create a new journal entry
        """
        return cls(
            user_id=user_id,
            title=title or f"Journal Entry - {datetime.now().strftime('%b %d, %Y')}",
            content=content,
            prompt_used=prompt_used,
            mood_score=mood_score,
            emotion_tags=emotion_tags
        )
    
    @classmethod
    def create_from_prompt(cls, user_id, prompt, content):
        """
        Create a journal entry using a specific prompt
        """
        return cls(
            user_id=user_id,
            title=f"Prompt: {prompt[:50]}...",
            content=content,
            prompt_used=prompt
        )
    
    # ==================== Update Methods ====================
    
    def update_content(self, new_content, new_title=None):
        """
        Update journal entry content
        """
        self.content = new_content
        if new_title:
            self.title = new_title
        self.updated_at = datetime.utcnow()
    
    def toggle_favorite(self):
        """Mark or unmark entry as favorite"""
        self.is_favorite = not self.is_favorite
    
    def add_emotion_tag(self, tag):
        """
        Add an emotion tag to the entry
        Tags are comma-separated strings
        """
        if self.emotion_tags:
            tags = self.emotion_tags.split(',')
            if tag not in tags:
                tags.append(tag)
                self.emotion_tags = ','.join(tags)
        else:
            self.emotion_tags = tag
    
    def get_emotion_tags_list(self):
        """Get emotion tags as Python list"""
        if not self.emotion_tags:
            return []
        return self.emotion_tags.split(',')
    
    # ==================== Analytics & Statistics ====================
    
    def get_word_count(self):
        """Count number of words in journal entry"""
        if not self.content:
            return 0
        return len(self.content.split())
    
    def get_character_count(self):
        """Count number of characters"""
        return len(self.content) if self.content else 0
    
    def get_estimated_read_time(self):
        """
        Estimate reading time in minutes
        Average reading speed: 200 words per minute
        """
        word_count = self.get_word_count()
        if word_count == 0:
            return 0
        return max(1, round(word_count / 200))
    
    # ==================== Serialization ====================
    
    def to_dict(self):
        """Convert journal entry to dictionary for API responses"""
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'preview': self.content[:150] + ('...' if len(self.content) > 150 else ''),
            'prompt_used': self.prompt_used,
            'mood_score': self.mood_score,
            'emotion_tags': self.get_emotion_tags_list(),
            'is_favorite': self.is_favorite,
            'word_count': self.get_word_count(),
            'read_time': self.get_estimated_read_time(),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'created_date_formatted': self.created_at.strftime('%b %d, %Y') if self.created_at else None,
            'created_time_formatted': self.created_at.strftime('%I:%M %p') if self.created_at else None
        }
    
    def to_export_dict(self):
        """
        Full export format (for user data export)
        Includes all fields without truncation
        """
        return {
            'title': self.title,
            'content': self.content,
            'prompt_used': self.prompt_used,
            'mood_score': self.mood_score,
            'emotion_tags': self.emotion_tags,
            'is_favorite': self.is_favorite,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<JournalEntry id={self.id} user={self.user_id} created={self.created_at}>'


# ==================== Journal Prompt Library ====================

class JournalPromptLibrary:
    """
    Collection of journaling prompts for users
    These prompts help users start writing when they feel stuck
    """
    
    # General wellness prompts
    GENERAL_PROMPTS = [
        "What are three things you're grateful for today?",
        "How are you feeling right now, without judgment?",
        "What's one small win you had today?",
        "What's something you'd like to let go of?",
        "Describe a moment today that made you smile.",
        "What's one kind thing you can do for yourself tomorrow?",
        "What emotion showed up most today, and where did you feel it in your body?",
        "If you could say 'no' to one thing tomorrow, what would it be?",
        "What's a thought that kept coming back today?",
        "Write a short letter of compassion to yourself."
    ]
    
    # Anxiety/stress focused prompts
    ANXIETY_PROMPTS = [
        "What's making you feel anxious right now? Write it down, then ask: 'Is this within my control?'",
        "Describe what 'calm' feels like in your body. When was the last time you felt that way?",
        "List 5 things you can see, 4 you can touch, 3 you can hear, 2 you can smell, and 1 you can taste.",
        "Write down the worry that's on your mind. Then write down a more balanced thought.",
        "What's one small step you can take today to reduce your anxiety?"
    ]
    
    # Sadness/depression focused prompts
    SADNESS_PROMPTS = [
        "What's one small thing that brought you even a tiny bit of comfort today?",
        "Write a letter to your sadness. What would you say to it?",
        "What's something you used to enjoy that you haven't done in a while?",
        "Describe a time when you felt truly at peace. What made that moment special?",
        "What would you say to a friend who was feeling the way you feel right now?"
    ]
    
    # Gratitude & positivity prompts
    GRATITUDE_PROMPTS = [
        "List 3 things that went well today, no matter how small.",
        "Who is someone you're grateful to have in your life? Why?",
        "What's something about yourself that you appreciate?",
        "What's a challenge you overcame recently?",
        "What's something beautiful you noticed today?"
    ]
    
    # Self-reflection prompts
    REFLECTION_PROMPTS = [
        "What did you learn about yourself this week?",
        "If you could give your past self one piece of advice, what would it be?",
        "What's a belief you hold that might be holding you back?",
        "What does 'taking care of yourself' look like right now?",
        "What's something you want to forgive yourself for?"
    ]
    
    @classmethod
    def get_all_prompts(cls):
        """Get all prompts as a single list"""
        return (cls.GENERAL_PROMPTS + cls.ANXIETY_PROMPTS + 
                cls.SADNESS_PROMPTS + cls.GRATITUDE_PROMPTS + 
                cls.REFLECTION_PROMPTS)
    
    @classmethod
    def get_random_prompt(cls, category=None):
        """Get a random prompt (optionally from specific category)"""
        import random
        
        if category == 'general':
            prompts = cls.GENERAL_PROMPTS
        elif category == 'anxiety':
            prompts = cls.ANXIETY_PROMPTS
        elif category == 'sadness':
            prompts = cls.SADNESS_PROMPTS
        elif category == 'gratitude':
            prompts = cls.GRATITUDE_PROMPTS
        elif category == 'reflection':
            prompts = cls.REFLECTION_PROMPTS
        else:
            prompts = cls.get_all_prompts()
        
        return random.choice(prompts)
    
    @classmethod
    def get_prompts_by_emotion(cls, emotion):
        """
        Get prompts tailored to specific emotion
        """
        emotion_prompt_map = {
            'sadness': cls.SADNESS_PROMPTS,
            'anxiety': cls.ANXIETY_PROMPTS,
            'stress': cls.ANXIETY_PROMPTS,
            'fear': cls.ANXIETY_PROMPTS,
            'joy': cls.GRATITUDE_PROMPTS,
            'gratitude': cls.GRATITUDE_PROMPTS,
            'neutral': cls.GENERAL_PROMPTS
        }
        return emotion_prompt_map.get(emotion, cls.GENERAL_PROMPTS)