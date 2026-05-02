"""
routes/__init__.py - Routes package initialization and blueprint exports

This file:
1. Makes the routes folder a proper Python package
2. Creates Blueprint instances for each route module
3. Exports all blueprints for easy registration in app.py

Blueprints are Flask's way of organizing routes into modules.
Each blueprint handles a specific feature area:
- auth: Login, register, Google OAuth
- chat: Conversation endpoints
- mood: Mood tracking endpoints
- journal: Journal CRUD operations
- user: User profile and settings
"""

from flask import Blueprint

# Create blueprint instances
# Each blueprint will have its routes defined in separate files
# The url_prefix adds a prefix to all routes in that blueprint

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')
chat_bp = Blueprint('chat', __name__, url_prefix='/api/chat')
mood_bp = Blueprint('mood', __name__, url_prefix='/api/mood')
journal_bp = Blueprint('journal', __name__, url_prefix='/api/journal')
user_bp = Blueprint('user', __name__, url_prefix='/api/user')
helplines_bp = Blueprint('helplines', __name__, url_prefix='/api/helplines')

# Import route modules to register their endpoints with the blueprints
# These imports must come after blueprint creation to avoid circular imports
from . import auth
from . import chat
from . import mood
from . import journal
from . import user
from . import helplines

# Define what gets exported when someone does: from routes import *
__all__ = [
    'auth_bp',
    'chat_bp', 
    'mood_bp',
    'journal_bp',
    'user_bp',
    'helplines_bp'
]