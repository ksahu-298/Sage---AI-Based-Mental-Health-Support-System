"""
user.py - User routes for profile, settings, streak, and badges

Endpoints:
- GET /api/user/profile - Get user profile
- PUT /api/user/profile - Update user profile
- GET /api/user/streak - Get streak information
- GET /api/user/badges - Get user's badges
- GET /api/user/badges/all - Get all available badges
- PUT /api/user/preferences - Update user preferences
- DELETE /api/user/account - Delete user account
"""

from flask import request
from datetime import datetime
from .. import user_bp
from ..models import db, User, MoodEntry, JournalEntry, ChatMessage, UserSession
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..utils.helpers import (
    sanitize_input, validate_email, validate_username,
    create_success_response, create_error_response
)
from ..services.gamification import GamificationService, BadgeManager

# Initialize services
gamification_service = GamificationService()
badge_manager = BadgeManager()


@user_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """
    Get user profile information
    Returns: username, email, avatar, streak, badges, etc.
    """
    current_username = get_jwt_identity()
    user = User.query.filter_by(username=current_username).first()
    
    if not user:
        return create_error_response("User not found", 404)
    
    # Get additional stats
    mood_count = MoodEntry.query.filter_by(user_id=user.id).count()
    journal_count = JournalEntry.query.filter_by(user_id=user.id).count()
    chat_count = ChatMessage.query.filter_by(user_id=user.id, role='user').count()
    
    return create_success_response({
        'profile': user.to_dict(),
        'stats': {
            'mood_entries': mood_count,
            'journal_entries': journal_count,
            'chat_messages': chat_count
        }
    })


@user_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    """
    Update user profile
    Expected JSON: { username (optional), email (optional), avatar (optional) }
    """
    current_username = get_jwt_identity()
    user = User.query.filter_by(username=current_username).first()
    
    if not user:
        return create_error_response("User not found", 404)
    
    data = request.get_json()
    changes_made = False
    
    # Update username
    if 'username' in data:
        new_username = data['username'].strip()
        if new_username != user.username:
            if not validate_username(new_username):
                return create_error_response("Username must be 3-20 characters (letters, numbers, underscore)", 400)
            
            # Check if username is taken
            if User.query.filter_by(username=new_username).first():
                return create_error_response("Username already taken", 409)
            
            user.username = new_username
            changes_made = True
    
    # Update email
    if 'email' in data:
        new_email = data['email'].strip() if data['email'] else None
        if new_email != user.email:
            if new_email and not validate_email(new_email):
                return create_error_response("Invalid email format", 400)
            
            if new_email and User.query.filter_by(email=new_email).first():
                return create_error_response("Email already registered", 409)
            
            user.email = new_email
            changes_made = True
    
    # Update avatar
    if 'avatar' in data:
        user.avatar = data['avatar']
        changes_made = True
    
    if changes_made:
        user.updated_at = datetime.utcnow()
        db.session.commit()
    
    return create_success_response({
        'profile': user.to_dict()
    }, "Profile updated successfully" if changes_made else "No changes made")


@user_bp.route('/streak', methods=['GET'])
@jwt_required()
def get_streak():
    """
    Get user streak information
    Returns: current_streak, longest_streak, last_checkin, total_checkins
    """
    current_username = get_jwt_identity()
    user = User.query.filter_by(username=current_username).first()
    
    if not user:
        return create_error_response("User not found", 404)
    
    # Get streak info from gamification service
    from ..services.gamification import StreakManager
    streak_info = StreakManager.get_streak_info(user)
    
    # Get progress to next badge
    progress = gamification_service.get_user_progress_stats(
        user,
        MoodEntry.query.filter_by(user_id=user.id).count(),
        JournalEntry.query.filter_by(user_id=user.id).count(),
        ChatMessage.query.filter_by(user_id=user.id, role='user').count()
    )
    
    return create_success_response({
        'current_streak': streak_info['current_streak'],
        'longest_streak': streak_info['longest_streak'],
        'last_checkin': streak_info['last_checkin'],
        'total_checkins': streak_info['total_checkins'],
        'streak_percentage': progress.get('streak_percentage', 0),
        'next_badges': progress.get('next_badges', [])[:3]  # Show next 3 badges
    })


@user_bp.route('/badges', methods=['GET'])
@jwt_required()
def get_my_badges():
    """
    Get user's earned badges
    Returns: list of badges with details
    """
    current_username = get_jwt_identity()
    user = User.query.filter_by(username=current_username).first()
    
    if not user:
        return create_error_response("User not found", 404)
    
    # Get all badges with earned status
    all_badges = badge_manager.get_user_badges(user)
    
    # Separate earned and locked
    earned = [b for b in all_badges if b['earned']]
    locked = [b for b in all_badges if not b['earned']]
    
    return create_success_response({
        'earned_badges': earned,
        'locked_badges': locked[:10],  # Show only next 10 locked badges
        'total_earned': len(earned),
        'total_available': len(all_badges),
        'completion_percentage': round((len(earned) / len(all_badges)) * 100, 1) if all_badges else 0
    })


@user_bp.route('/badges/all', methods=['GET'])
@jwt_required()
def get_all_badges():
    """
    Get all available badges in the system (for badge gallery)
    """
    current_username = get_jwt_identity()
    user = User.query.filter_by(username=current_username).first()
    
    if not user:
        return create_error_response("User not found", 404)
    
    all_badges = badge_manager.get_user_badges(user)
    
    return create_success_response({
        'badges': all_badges,
        'total': len(all_badges)
    })


@user_bp.route('/preferences', methods=['GET'])
@jwt_required()
def get_preferences():
    """
    Get user preferences
    Returns: notification settings, theme, etc.
    """
    current_username = get_jwt_identity()
    user = User.query.filter_by(username=current_username).first()
    
    if not user:
        return create_error_response("User not found", 404)
    
    return create_success_response(user.preferences)


@user_bp.route('/preferences', methods=['PUT'])
@jwt_required()
def update_preferences():
    """
    Update user preferences
    Expected JSON: { preferences object }
    """
    current_username = get_jwt_identity()
    user = User.query.filter_by(username=current_username).first()
    
    if not user:
        return create_error_response("User not found", 404)
    
    data = request.get_json()
    
    # Merge with existing preferences
    current_prefs = user.preferences
    current_prefs.update(data)
    user.preferences = current_prefs
    
    db.session.commit()
    
    return create_success_response(user.preferences, "Preferences updated successfully")


@user_bp.route('/account', methods=['DELETE'])
@jwt_required()
def delete_account():
    """
    Delete user account and all associated data
    This is permanent and cannot be undone
    """
    current_username = get_jwt_identity()
    user = User.query.filter_by(username=current_username).first()
    
    if not user:
        return create_error_response("User not found", 404)
    
    # Get confirmation from request
    data = request.get_json()
    confirmation = data.get('confirm', False)
    
    if not confirmation:
        return create_error_response("Please confirm account deletion by setting confirm=true", 400)
    
    # Store user info for logging (optional)
    deleted_username = user.username
    deleted_email = user.email
    
    # Delete all related data (cascade should handle this, but explicit for safety)
    ChatMessage.query.filter_by(user_id=user.id).delete()
    MoodEntry.query.filter_by(user_id=user.id).delete()
    JournalEntry.query.filter_by(user_id=user.id).delete()
    UserSession.query.filter_by(user_id=user.id).delete()
    
    # Delete the user
    db.session.delete(user)
    db.session.commit()
    
    return create_success_response(None, f"Account '{deleted_username}' has been permanently deleted")


@user_bp.route('/dashboard', methods=['GET'])
@jwt_required()
def get_dashboard_data():
    """
    Get all data needed for the user dashboard
    One endpoint to rule them all - reduces API calls
    """
    current_username = get_jwt_identity()
    user = User.query.filter_by(username=current_username).first()
    
    if not user:
        return create_error_response("User not found", 404)
    
    # Get mood data for last 7 days
    from ..routes.mood import get_weekly_mood
    from ..routes.mood import get_weekly_mood as get_weekly_mood_func
    
    # Get weekly mood (simulate call)
    weekly_mood = []
    from datetime import datetime, timedelta
    from ..utils.helpers import get_mood_emoji
    
    for i in range(6, -1, -1):
        date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
        day_name = (datetime.now() - timedelta(days=i)).strftime('%a')
        entry = MoodEntry.query.filter_by(user_id=user.id, date=date).first()
        weekly_mood.append({
            'date': date,
            'day': day_name,
            'score': entry.mood_score if entry else None,
            'emoji': get_mood_emoji(entry.mood_score) if entry else None,
            'has_entry': entry is not None
        })
    
    # Get streak info
    from ..services.gamification import StreakManager
    streak_info = StreakManager.get_streak_info(user)
    
    # Get badges (earned only)
    all_badges = badge_manager.get_user_badges(user)
    earned_badges = [b for b in all_badges if b['earned']]
    
    # Get recent journal entries (last 3)
    recent_journals = JournalEntry.query.filter_by(user_id=user.id)\
        .order_by(JournalEntry.created_at.desc())\
        .limit(3)\
        .all()
    
    # Check if mood logged today
    today = datetime.now().strftime('%Y-%m-%d')
    mood_today = MoodEntry.query.filter_by(user_id=user.id, date=today).first()
    
    # Get streak warning
    streak_warning = None
    if not mood_today:
        from ..services.gamification import GamificationService
        gs = GamificationService()
        streak_warning = gs.get_streak_warning(user.last_checkin)
    
    return create_success_response({
        'user': {
            'username': user.username,
            'avatar': user.avatar,
            'streak': streak_info['current_streak'],
            'longest_streak': streak_info['longest_streak'],
            'total_checkins': streak_info['total_checkins']
        },
        'weekly_mood': weekly_mood,
        'badges': earned_badges[:5],  # Top 5 badges for dashboard
        'recent_journals': [j.to_preview_dict() for j in recent_journals],
        'mood_logged_today': mood_today is not None,
        'today_mood_score': mood_today.mood_score if mood_today else None,
        'streak_warning': streak_warning,
        'has_journals': len(recent_journals) > 0
    })