"""
models/__init__.py - Database initialization and model exports

This file:
1. Creates the SQLAlchemy database instance
2. Imports all model classes
3. Provides a clean import interface for other parts of the app
"""

from flask_sqlalchemy import SQLAlchemy

# Create the database instance (shared across all models)
# This db object will be used by all model files
db = SQLAlchemy()

# Import all models so they register with SQLAlchemy
# Order matters: User must be imported first because other models reference it
from .user import User
from .chat import ChatMessage
from .mood import MoodEntry
from .journal import JournalEntry
from .session import UserSession

# Define what gets exported when someone does: from models import *
__all__ = [
    'db',           # The database instance
    'User',         # User model (authentication, profile)
    'ChatMessage',  # Chat history model
    'MoodEntry',    # Mood tracking model
    'JournalEntry', # Journal entries model
    'UserSession'   # Session management model
]