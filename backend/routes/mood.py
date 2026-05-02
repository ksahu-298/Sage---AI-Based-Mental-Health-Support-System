"""
mood.py - Mood tracking routes for daily check-ins and mood history

Endpoints:
- POST /api/mood/record - Record today's mood score
- GET /api/mood/history - Get user's mood history
- GET /api/mood/stats - Get mood statistics (average, trend)
- GET /api/mood/weekly - Get last 7 days mood data for graph
- GET /api/mood/export - Export mood data as CSV
"""

from flask import request, Response
from datetime import datetime, timedelta
import csv
import io
from .. import mood_bp
from ..models import db, User, MoodEntry
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..utils.helpers import (
    validate_mood_score, get_today_date, get_week_ago_date,
    create_success_response, create_error_response, get_mood_emoji
)
from ..services.gamification import GamificationService

# Initialize services
gamification_service = GamificationService()


@mood_bp.route('/record', methods=['POST'])
@jwt_required()
def record_mood():
    """
    Record today's mood score
    Expected JSON: { score: 1-10, note: "optional", time_of_day: "optional" }
    """
    current_username = get_jwt_identity()
    user = User.query.filter_by(username=current_username).first()
    
    if not user:
        return create_error_response("User not found", 404)
    
    data = request.get_json()
    mood_score = data.get('score')
    note = data.get('note', '')
    time_of_day = data.get('time_of_day')
    activity_before = data.get('activity_before')
    sleep_hours = data.get('sleep_hours')
    
    # Validate mood score
    if not validate_mood_score(mood_score):
        return create_error_response("Mood score must be between 1 and 10", 400)
    
    today = get_today_date()
    
    # Check if mood entry already exists for today
    existing_entry = MoodEntry.query.filter_by(
        user_id=user.id, 
        date=today
    ).first()
    
    if existing_entry:
        # Update existing entry
        existing_entry.mood_score = mood_score
        existing_entry.note = note or existing_entry.note
        existing_entry.time_of_day = time_of_day or existing_entry.time_of_day
        existing_entry.activity_before = activity_before or existing_entry.activity_before
        existing_entry.sleep_hours = sleep_hours or existing_entry.sleep_hours
        existing_entry.updated_at = datetime.utcnow()
        mood_entry = existing_entry
        is_new = False
    else:
        # Create new entry
        mood_entry = MoodEntry.create_entry(
            user_id=user.id,
            mood_score=mood_score,
            date=today,
            note=note,
            time_of_day=time_of_day,
            activity_before=activity_before,
            sleep_hours=sleep_hours
        )
        db.session.add(mood_entry)
        is_new = True
    
    # Update streak using gamification service
    streak_result = gamification_service.update_streak(user, today)
    
    # Check for mood-based badges
    # Get all mood entries to check variety
    all_mood_entries = MoodEntry.query.filter_by(user_id=user.id).all()
    new_badges = gamification_service.check_mood_based_badges(user, all_mood_entries)
    
    db.session.commit()
    
    # Generate motivational message
    motivational_message = gamification_service.get_motivational_message(
        user.streak, 
        user.total_checkins,
        streak_result.get('newly_earned_badges', []) + new_badges
    )
    
    return create_success_response({
        'mood': {
            'score': mood_score,
            'emoji': get_mood_emoji(mood_score),
            'date': today,
            'note': note if note else None
        },
        'streak': streak_result['new_streak'],
        'longest_streak': user.longest_streak,
        'is_new_record': streak_result.get('is_new_record', False),
        'new_badges': streak_result.get('newly_earned_badges', []) + new_badges,
        'message': motivational_message,
        'total_checkins': user.total_checkins
    }, "Mood recorded successfully" if is_new else "Mood updated successfully")


@mood_bp.route('/history', methods=['GET'])
@jwt_required()
def get_mood_history():
    """
    Get user's mood history
    Query params: days (default 30), limit (default 30)
    """
    current_username = get_jwt_identity()
    user = User.query.filter_by(username=current_username).first()
    
    if not user:
        return create_error_response("User not found", 404)
    
    # Get parameters
    days = request.args.get('days', 30, type=int)
    limit = request.args.get('limit', 30, type=int)
    
    # Limit to reasonable values
    days = min(days, 365)
    limit = min(limit, 90)
    
    # Calculate date threshold
    threshold_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
    
    # Get mood entries
    mood_entries = MoodEntry.query.filter_by(user_id=user.id)\
        .filter(MoodEntry.date >= threshold_date)\
        .order_by(MoodEntry.date.desc())\
        .limit(limit)\
        .all()
    
    # Reverse for chronological order
    mood_entries = list(reversed(mood_entries))
    
    return create_success_response({
        'entries': [entry.to_dict() for entry in mood_entries],
        'total': MoodEntry.query.filter_by(user_id=user.id).count(),
        'days_range': days
    })


@mood_bp.route('/weekly', methods=['GET'])
@jwt_required()
def get_weekly_mood():
    """
    Get last 7 days mood data for graph display
    Returns array of 7 days with mood scores (null if no entry)
    """
    current_username = get_jwt_identity()
    user = User.query.filter_by(username=current_username).first()
    
    if not user:
        return create_error_response("User not found", 404)
    
    # Get last 7 days dates
    weekly_data = []
    for i in range(6, -1, -1):
        date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
        day_name = (datetime.now() - timedelta(days=i)).strftime('%a')
        
        # Find mood entry for this date
        entry = MoodEntry.query.filter_by(user_id=user.id, date=date).first()
        
        weekly_data.append({
            'date': date,
            'day': day_name,
            'score': entry.mood_score if entry else None,
            'emoji': get_mood_emoji(entry.mood_score) if entry else None,
            'has_entry': entry is not None,
            'note': entry.note if entry else None
        })
    
    # Calculate weekly average (only days with entries)
    scores = [d['score'] for d in weekly_data if d['score'] is not None]
    average = round(sum(scores) / len(scores), 1) if scores else None
    
    return create_success_response({
        'weekly_data': weekly_data,
        'average': average,
        'total_entries_week': len(scores),
        'streak': user.streak
    })


@mood_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_mood_stats():
    """
    Get mood statistics
    Returns: average, trend, best day, worst day, etc.
    """
    current_username = get_jwt_identity()
    user = User.query.filter_by(username=current_username).first()
    
    if not user:
        return create_error_response("User not found", 404)
    
    # Get all mood entries
    all_entries = MoodEntry.query.filter_by(user_id=user.id)\
        .order_by(MoodEntry.date.asc())\
        .all()
    
    if not all_entries:
        return create_success_response({
            'has_data': False,
            'message': 'No mood data yet. Start by logging your first mood!'
        })
    
    # Calculate statistics
    scores = [e.mood_score for e in all_entries]
    average = round(sum(scores) / len(scores), 1)
    
    # Find best and worst days
    best_entry = max(all_entries, key=lambda e: e.mood_score)
    worst_entry = min(all_entries, key=lambda e: e.mood_score)
    
    # Calculate trend (compare last 7 days to previous 7 days)
    last_7_entries = all_entries[-7:] if len(all_entries) >= 7 else all_entries
    previous_7_entries = all_entries[-14:-7] if len(all_entries) >= 14 else []
    
    last_7_avg = sum(e.mood_score for e in last_7_entries) / len(last_7_entries)
    previous_7_avg = sum(e.mood_score for e in previous_7_entries) / len(previous_7_entries) if previous_7_entries else last_7_avg
    
    trend_diff = last_7_avg - previous_7_avg
    
    if trend_diff > 0.5:
        trend = 'improving'
        trend_message = "📈 Your mood has been improving over the last week!"
    elif trend_diff < -0.5:
        trend = 'declining'
        trend_message = "📉 Your mood has been declining. Remember to be gentle with yourself."
    else:
        trend = 'stable'
        trend_message = "📊 Your mood has been stable. Consistency is key!"
    
    # Mood distribution
    distribution = {
        'very_low': len([s for s in scores if s <= 2]),
        'low': len([s for s in scores if 3 <= s <= 4]),
        'okay': len([s for s in scores if 5 <= s <= 6]),
        'good': len([s for s in scores if 7 <= s <= 8]),
        'amazing': len([s for s in scores if 9 <= s <= 10])
    }
    
    return create_success_response({
        'has_data': True,
        'total_entries': len(all_entries),
        'average': average,
        'highest_score': best_entry.mood_score,
        'highest_date': best_entry.date,
        'lowest_score': worst_entry.mood_score,
        'lowest_date': worst_entry.date,
        'trend': trend,
        'trend_message': trend_message,
        'trend_difference': round(trend_diff, 1),
        'distribution': distribution,
        'current_streak': user.streak,
        'longest_streak': user.longest_streak
    })


@mood_bp.route('/export', methods=['GET'])
@jwt_required()
def export_mood_data():
    """
    Export mood data as CSV file
    """
    current_username = get_jwt_identity()
    user = User.query.filter_by(username=current_username).first()
    
    if not user:
        return create_error_response("User not found", 404)
    
    # Get all mood entries
    entries = MoodEntry.query.filter_by(user_id=user.id)\
        .order_by(MoodEntry.date.asc())\
        .all()
    
    # Create CSV
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow(['Date', 'Mood Score', 'Emoji', 'Note', 'Time of Day', 'Sleep Hours', 'Recorded At'])
    
    # Write data
    for entry in entries:
        writer.writerow([
            entry.date,
            entry.mood_score,
            get_mood_emoji(entry.mood_score),
            entry.note or '',
            entry.time_of_day or '',
            entry.sleep_hours or '',
            entry.created_at.strftime('%Y-%m-%d %H:%M:%S') if entry.created_at else ''
        ])
    
    # Create response
    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={
            'Content-Disposition': f'attachment; filename=sage_mood_data_{datetime.now().strftime("%Y%m%d")}.csv'
        }
    )


@mood_bp.route('/check-today', methods=['GET'])
@jwt_required()
def check_today_mood():
    """
    Check if user has logged mood today
    Returns: has_logged_today, today_mood (if exists)
    """
    current_username = get_jwt_identity()
    user = User.query.filter_by(username=current_username).first()
    
    if not user:
        return create_error_response("User not found", 404)
    
    today = get_today_date()
    today_entry = MoodEntry.query.filter_by(user_id=user.id, date=today).first()
    
    if today_entry:
        return create_success_response({
            'has_logged_today': True,
            'today_mood': {
                'score': today_entry.mood_score,
                'emoji': get_mood_emoji(today_entry.mood_score),
                'note': today_entry.note
            },
            'streak_warning': None
        })
    else:
        # Generate streak warning
        warning = gamification_service.get_streak_warning(user.last_checkin)
        
        return create_success_response({
            'has_logged_today': False,
            'today_mood': None,
            'streak_warning': warning
        })


@mood_bp.route('/calendar', methods=['GET'])
@jwt_required()
def get_calendar_data():
    """
    Get mood data for calendar view
    Query params: year, month (optional)
    """
    current_username = get_jwt_identity()
    user = User.query.filter_by(username=current_username).first()
    
    if not user:
        return create_error_response("User not found", 404)
    
    # Get year and month from query params (default to current)
    year = request.args.get('year', type=int)
    month = request.args.get('month', type=int)
    
    now = datetime.now()
    year = year or now.year
    month = month or now.month
    
    # Get first and last day of month
    first_day = datetime(year, month, 1)
    if month == 12:
        last_day = datetime(year + 1, 1, 1) - timedelta(days=1)
    else:
        last_day = datetime(year, month + 1, 1) - timedelta(days=1)
    
    # Get entries for this month
    entries = MoodEntry.query.filter_by(user_id=user.id)\
        .filter(MoodEntry.date >= first_day.strftime('%Y-%m-%d'))\
        .filter(MoodEntry.date <= last_day.strftime('%Y-%m-%d'))\
        .all()
    
    # Create calendar data
    calendar_data = {}
    for entry in entries:
        calendar_data[entry.date] = {
            'score': entry.mood_score,
            'emoji': get_mood_emoji(entry.mood_score),
            'note': entry.note
        }
    
    return create_success_response({
        'year': year,
        'month': month,
        'month_name': first_day.strftime('%B'),
        'calendar_data': calendar_data,
        'total_days': len(entries)
    })