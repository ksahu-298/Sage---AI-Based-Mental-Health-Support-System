"""
helpers.py - Utility helper functions for Sage backend
Includes: validation, formatting, sanitization, timestamps
"""

import re
import json
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify
import bleach

# ==================== SANITIZATION & VALIDATION ====================

def sanitize_input(text):
    """
    Remove harmful HTML/script tags from user input
    Prevents XSS (Cross-Site Scripting) attacks
    """
    if not text:
        return ""
    # Bleach removes HTML tags while keeping safe formatting
    allowed_tags = ['b', 'i', 'em', 'strong', 'p', 'br']
    allowed_attributes = {}
    cleaned = bleach.clean(text, tags=allowed_tags, attributes=allowed_attributes, strip=True)
    return cleaned.strip()

def validate_email(email):
    """
    Validate email format using regex
    Returns True if valid, False otherwise
    """
    if not email:
        return False
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_username(username):
    """
    Validate username: 3-20 chars, alphanumeric + underscore
    Returns True if valid, False otherwise
    """
    if not username:
        return False
    pattern = r'^[a-zA-Z0-9_]{3,20}$'
    return re.match(pattern, username) is not None

def validate_mood_score(score):
    """
    Validate mood score is between 1 and 10
    """
    try:
        score = int(score)
        return 1 <= score <= 10
    except (ValueError, TypeError):
        return False

def truncate_text(text, max_length=2000):
    """
    Truncate text to maximum length
    Prevents excessively long messages
    """
    if not text:
        return ""
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."

def is_valid_message(text):
    """
    Check if message is valid (non-empty, not just whitespace)
    """
    if not text:
        return False
    return len(text.strip()) > 0

def contains_phone_number(text):
    """
    Check if text contains an Indian phone number
    Used to detect if user is sharing contact info
    """
    # Indian phone number patterns
    patterns = [
        r'\b[6-9]\d{9}\b',  # 10 digits starting with 6-9
        r'\b0[6-9]\d{9}\b',  # 11 digits with leading 0
        r'\b\+91[6-9]\d{9}\b'  # +91 followed by 10 digits
    ]
    for pattern in patterns:
        if re.search(pattern, text):
            return True
    return False

# ==================== FORMATTING FUNCTIONS ====================

def format_timestamp(timestamp):
    """
    Convert datetime to readable format
    Example: "2 minutes ago", "Yesterday", "Jan 15, 2024"
    """
    if not timestamp:
        return ""
    
    # If timestamp is string, convert to datetime
    if isinstance(timestamp, str):
        timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
    
    now = datetime.now()
    diff = now - timestamp
    
    if diff.days == 0:
        if diff.seconds < 60:
            return "just now"
        elif diff.seconds < 3600:
            mins = diff.seconds // 60
            return f"{mins} minute{'s' if mins > 1 else ''} ago"
        else:
            hours = diff.seconds // 3600
            return f"{hours} hour{'s' if hours > 1 else ''} ago"
    elif diff.days == 1:
        return "yesterday"
    elif diff.days < 7:
        return f"{diff.days} days ago"
    else:
        return timestamp.strftime("%b %d, %Y")

def format_mood_label(score):
    """
    Convert mood score to emoji and label
    """
    if score >= 9:
        return "😍 Amazing"
    elif score >= 7:
        return "😊 Good"
    elif score >= 5:
        return "🙂 Okay"
    elif score >= 3:
        return "😐 Meh"
    else:
        return "😔 Low"

def get_mood_emoji(score):
    """
    Get just the emoji for a mood score
    """
    if score >= 9:
        return "😍"
    elif score >= 7:
        return "😊"
    elif score >= 5:
        return "🙂"
    elif score >= 3:
        return "😐"
    else:
        return "😔"

# ==================== DATE & TIME HELPERS ====================

def get_today_date():
    """
    Get today's date as string in YYYY-MM-DD format
    """
    return datetime.now().strftime('%Y-%m-%d')

def get_yesterday_date():
    """
    Get yesterday's date as string in YYYY-MM-DD format
    """
    return (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')

def get_week_ago_date():
    """
    Get date from 7 days ago
    """
    return (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')

def is_same_day(date1, date2):
    """
    Check if two dates are the same day
    """
    return date1 == date2

def calculate_streak(last_checkin_date, current_streak):
    """
    Calculate updated streak based on last checkin
    """
    today = get_today_date()
    yesterday = get_yesterday_date()
    
    if not last_checkin_date:
        return 1  # First check-in
    
    if last_checkin_date == today:
        return current_streak  # Already checked in today
    
    if last_checkin_date == yesterday:
        return current_streak + 1  # Consecutive day
    
    return 1  # Streak broken, start over

# ==================== RESPONSE FORMATTING ====================

def create_success_response(data=None, message="Success"):
    """
    Create a standardized success response
    """
    return jsonify({
        'success': True,
        'message': message,
        'data': data,
        'timestamp': datetime.now().isoformat()
    })

def create_error_response(error_message, status_code=400):
    """
    Create a standardized error response
    """
    return jsonify({
        'success': False,
        'error': error_message,
        'timestamp': datetime.now().isoformat()
    }), status_code

# ==================== CRYPTO & HASHING ====================

import hashlib
import secrets

def generate_token(length=32):
    """
    Generate a secure random token
    Used for password reset, email verification
    """
    return secrets.token_urlsafe(length)

def hash_string(text):
    """
    Create a SHA-256 hash of a string
    Used for creating unique IDs from content
    """
    return hashlib.sha256(text.encode()).hexdigest()

# ==================== TEXT ANALYSIS HELPERS ====================

def count_words(text):
    """
    Count number of words in text
    """
    if not text:
        return 0
    return len(text.split())

def extract_hashtags(text):
    """
    Extract hashtags from text (#mentalhealth, #selfcare)
    """
    if not text:
        return []
    return re.findall(r'#(\w+)', text)

def remove_extra_whitespace(text):
    """
    Remove extra spaces, newlines, and trim
    """
    if not text:
        return ""
    # Replace multiple spaces with single space
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

# ==================== RATE LIMITING HELPERS ====================

# Simple in-memory rate limiter (for development)
# For production, use Redis or database

_rate_limit_cache = {}

def check_rate_limit(key, limit_per_minute=20):
    """
    Simple rate limiter - returns True if under limit
    """
    from time import time
    
    current_minute = int(time() / 60)
    cache_key = f"{key}:{current_minute}"
    
    if cache_key not in _rate_limit_cache:
        _rate_limit_cache[cache_key] = 0
    
    _rate_limit_cache[cache_key] += 1
    
    # Clean up old cache entries
    for k in list(_rate_limit_cache.keys()):
        if int(k.split(':')[-1]) < current_minute - 1:
            del _rate_limit_cache[k]
    
    return _rate_limit_cache[cache_key] <= limit_per_minute

# ==================== LOGGING HELPERS ====================

import logging

def setup_logger(name, log_file='sage.log', level=logging.INFO):
    """
    Set up a logger with file and console output
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # File handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(level)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    
    # Formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

# ==================== JSON HELPERS ====================

class DateTimeEncoder(json.JSONEncoder):
    """
    Custom JSON encoder for datetime objects
    """
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

def safe_json_loads(json_string, default=None):
    """
    Safely parse JSON - returns default if error
    """
    if not json_string:
        return default or {}
    try:
        return json.loads(json_string)
    except (json.JSONDecodeError, TypeError):
        return default or {}

def safe_json_dumps(obj, default=None):
    """
    Safely convert to JSON string
    """
    try:
        return json.dumps(obj, cls=DateTimeEncoder)
    except (TypeError, ValueError):
        return default or "{}"