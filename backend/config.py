"""
config.py - Configuration management for Sage backend
Loads environment variables and provides configuration objects
"""

import os
from datetime import timedelta
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Base configuration class"""
    
    # Flask Settings
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-me')
    DEBUG = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    # Database
    DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///database/sage.db')
    
    # JWT Settings
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'jwt-secret-change-me')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(days=7)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    JWT_TOKEN_LOCATION = ['headers']
    JWT_HEADER_NAME = 'Authorization'
    JWT_HEADER_TYPE = 'Bearer'
    
    # CORS Settings
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', 'http://localhost:3000,http://127.0.0.1:5500,http://localhost:5000,https://grand-tartufo-dc4f90.netlify.app').split(',')
    
    # Rate Limiting - Fixed to handle string values properly
    RATE_LIMIT_CHAT = 20  # messages per minute
    RATE_LIMIT_LOGIN = 5   # attempts per minute
    
    # Application Settings
    MAX_MESSAGE_LENGTH = 2000
    CHAT_HISTORY_LIMIT = 50
    MOOD_HISTORY_DAYS = 90
    
    # Google OAuth (Optional)
    GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID', '')
    GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET', '')
    GOOGLE_REDIRECT_URI = os.environ.get('GOOGLE_REDIRECT_URI', 'https://sage-ai-based-mental-health-support-system-production.up.railway.app/api/auth/google/callback')
    
    # Email Settings (Optional)
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME', '')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', '')
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'True').lower() == 'true'
    
    # Crisis Settings
    ENABLE_CRISIS_REDIRECT = True
    CRISIS_ALERT_EMAIL = os.environ.get('CRISIS_ALERT_EMAIL', '')
    
    # Helplines (India)
    INDIAN_HELPLINES = [
        {'name': 'KIRAN', 'number': '1800-599-0019', 'timing': '24×7', 'coverage': 'All India', 'description': 'Govt of India National Mental Health Helpline'},
        {'name': 'iCall (TISS)', 'number': '+91-9152987821', 'timing': 'Mon–Sat, 8 AM – 10 PM', 'coverage': 'All India', 'description': 'Free telephone counselling by TISS'},
        {'name': 'Vandrevala Foundation', 'number': '1860-2662-345', 'timing': '24×7', 'coverage': 'All India', 'description': 'Free 24/7 mental health support'},
        {'name': 'AASRA', 'number': '+91-9820466726', 'timing': '24×7', 'coverage': 'All India', 'description': 'Suicide prevention helpline'},
        {'name': 'NIMHANS Helpline', 'number': '080-46110007', 'timing': '24×7', 'coverage': 'All India', 'description': 'NIMHANS psychosocial helpline'},
        {'name': 'Snehi', 'number': '+91-9582208181', 'timing': '10 AM – 10 PM', 'coverage': 'All India', 'description': 'Emotional support helpline'}
    ]
    
    # Crisis detection keywords
    CRISIS_KEYWORDS = [
        'suicide', 'kill myself', 'end my life', 'want to die', 'no reason to live',
        'self-harm', 'cut myself', 'hurt myself', 'please help me', 'i can\'t do this anymore',
        'give up', 'better off dead', 'ending it', 'take my life'
    ]
    
    # Off-topic keywords
    OFF_TOPIC_KEYWORDS = [
        'cricket', 'movie', 'politics', 'stock market', 'crypto', 'bitcoin',
        'football', 'ipl', 'match', 'cinema', 'celebrity', 'gossip'
    ]


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False


class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    DEBUG = True


# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}


def get_config(env=None):
    """Returns the appropriate config based on environment"""
    if env is None:
        env = os.environ.get('FLASK_ENV', 'development')
    return config.get(env, DevelopmentConfig)