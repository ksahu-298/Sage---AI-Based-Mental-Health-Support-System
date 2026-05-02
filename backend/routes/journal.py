"""
journal.py - Journal routes for creating, reading, updating, and deleting journal entries

Endpoints:
- POST /api/journal/create - Create a new journal entry
- GET /api/journal/list - Get user's journal entries
- GET /api/journal/:id - Get specific journal entry
- PUT /api/journal/:id - Update journal entry
- DELETE /api/journal/:id - Delete journal entry
- GET /api/journal/prompts - Get journaling prompts
- GET /api/journal/export - Export all journal entries
"""

from flask import request, Response
from datetime import datetime
import csv
import io
import json
from .. import journal_bp
from ..models import db, User, JournalEntry
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..utils.helpers import (
    sanitize_input, truncate_text, create_success_response, create_error_response
)
from ..models.journal import JournalPromptLibrary


@journal_bp.route('/create', methods=['POST'])
@jwt_required()
def create_journal_entry():
    """
    Create a new journal entry
    Expected JSON: { content, title (optional), prompt_used (optional), mood_score (optional), emotion_tags (optional) }
    """
    current_username = get_jwt_identity()
    user = User.query.filter_by(username=current_username).first()
    
    if not user:
        return create_error_response("User not found", 404)
    
    data = request.get_json()
    content = data.get('content', '').strip()
    title = data.get('title', '').strip()
    prompt_used = data.get('prompt_used', '')
    mood_score = data.get('mood_score')
    emotion_tags = data.get('emotion_tags', '')
    
    # Validate content
    if not content:
        return create_error_response("Journal content cannot be empty", 400)
    
    # Sanitize inputs
    content = sanitize_input(content)
    content = truncate_text(content, 10000)  # Max 10,000 characters
    if title:
        title = sanitize_input(title)
        title = truncate_text(title, 200)
    
    # Create journal entry
    journal_entry = JournalEntry.create_entry(
        user_id=user.id,
        content=content,
        title=title if title else None,
        prompt_used=prompt_used if prompt_used else None,
        mood_score=mood_score,
        emotion_tags=emotion_tags if emotion_tags else None
    )
    
    db.session.add(journal_entry)
    db.session.commit()
    
    # Check for journal-based badges
    from ..services.gamification import GamificationService
    gamification = GamificationService()
    
    # Count total journal entries
    journal_count = JournalEntry.query.filter_by(user_id=user.id).count()
    new_badges = gamification.check_journal_based_badges(user, journal_count)
    
    if new_badges:
        db.session.commit()
    
    return create_success_response({
        'entry': journal_entry.to_dict(),
        'new_badges': new_badges if new_badges else None,
        'total_entries': journal_count
    }, "Journal entry created successfully", 201)


@journal_bp.route('/list', methods=['GET'])
@jwt_required()
def list_journal_entries():
    """
    Get user's journal entries
    Query params: limit (default 20), offset (default 0), favorite (optional)
    """
    current_username = get_jwt_identity()
    user = User.query.filter_by(username=current_username).first()
    
    if not user:
        return create_error_response("User not found", 404)
    
    # Get parameters
    limit = request.args.get('limit', 20, type=int)
    offset = request.args.get('offset', 0, type=int)
    favorite_only = request.args.get('favorite', 'false').lower() == 'true'
    
    # Limit max
    limit = min(limit, 50)
    
    # Build query
    query = JournalEntry.query.filter_by(user_id=user.id)
    
    if favorite_only:
        query = query.filter_by(is_favorite=True)
    
    # Get total count
    total = query.count()
    
    # Get paginated entries
    entries = query.order_by(JournalEntry.created_at.desc())\
        .offset(offset)\
        .limit(limit)\
        .all()
    
    return create_success_response({
        'entries': [entry.to_dict() for entry in entries],
        'total': total,
        'limit': limit,
        'offset': offset,
        'has_more': offset + limit < total
    })


@journal_bp.route('/<int:entry_id>', methods=['GET'])
@jwt_required()
def get_journal_entry(entry_id):
    """
    Get a specific journal entry by ID
    """
    current_username = get_jwt_identity()
    user = User.query.filter_by(username=current_username).first()
    
    if not user:
        return create_error_response("User not found", 404)
    
    entry = JournalEntry.query.filter_by(id=entry_id, user_id=user.id).first()
    
    if not entry:
        return create_error_response("Journal entry not found", 404)
    
    return create_success_response(entry.to_dict())


@journal_bp.route('/<int:entry_id>', methods=['PUT'])
@jwt_required()
def update_journal_entry(entry_id):
    """
    Update a journal entry
    Expected JSON: { content, title (optional), mood_score (optional), emotion_tags (optional) }
    """
    current_username = get_jwt_identity()
    user = User.query.filter_by(username=current_username).first()
    
    if not user:
        return create_error_response("User not found", 404)
    
    entry = JournalEntry.query.filter_by(id=entry_id, user_id=user.id).first()
    
    if not entry:
        return create_error_response("Journal entry not found", 404)
    
    data = request.get_json()
    
    # Update fields if provided
    if 'content' in data:
        new_content = data['content'].strip()
        if new_content:
            entry.content = sanitize_input(new_content)
            entry.content = truncate_text(entry.content, 10000)
    
    if 'title' in data:
        new_title = data['title'].strip()
        entry.title = sanitize_input(new_title) if new_title else None
    
    if 'mood_score' in data:
        entry.mood_score = data['mood_score']
    
    if 'emotion_tags' in data:
        entry.emotion_tags = data['emotion_tags']
    
    if 'is_favorite' in data:
        entry.is_favorite = data['is_favorite']
    
    entry.updated_at = datetime.utcnow()
    db.session.commit()
    
    return create_success_response(entry.to_dict(), "Journal entry updated successfully")


@journal_bp.route('/<int:entry_id>', methods=['DELETE'])
@jwt_required()
def delete_journal_entry(entry_id):
    """
    Delete a journal entry
    """
    current_username = get_jwt_identity()
    user = User.query.filter_by(username=current_username).first()
    
    if not user:
        return create_error_response("User not found", 404)
    
    entry = JournalEntry.query.filter_by(id=entry_id, user_id=user.id).first()
    
    if not entry:
        return create_error_response("Journal entry not found", 404)
    
    db.session.delete(entry)
    db.session.commit()
    
    return create_success_response(None, "Journal entry deleted successfully")


@journal_bp.route('/<int:entry_id>/favorite', methods=['POST'])
@jwt_required()
def toggle_favorite(entry_id):
    """
    Toggle favorite status of a journal entry
    """
    current_username = get_jwt_identity()
    user = User.query.filter_by(username=current_username).first()
    
    if not user:
        return create_error_response("User not found", 404)
    
    entry = JournalEntry.query.filter_by(id=entry_id, user_id=user.id).first()
    
    if not entry:
        return create_error_response("Journal entry not found", 404)
    
    entry.toggle_favorite()
    db.session.commit()
    
    return create_success_response({
        'is_favorite': entry.is_favorite
    }, "Favorite status updated")


@journal_bp.route('/prompts', methods=['GET'])
@jwt_required()
def get_journal_prompts():
    """
    Get journaling prompts
    Query params: emotion (optional) - get prompts for specific emotion
    """
    current_username = get_jwt_identity()
    user = User.query.filter_by(username=current_username).first()
    
    if not user:
        return create_error_response("User not found", 404)
    
    emotion = request.args.get('emotion')
    
    if emotion:
        prompts = JournalPromptLibrary.get_prompts_by_emotion(emotion)
    else:
        prompts = JournalPromptLibrary.get_all_prompts()
    
    # Return random selection of prompts (up to 10)
    import random
    selected_prompts = random.sample(prompts, min(10, len(prompts)))
    
    return create_success_response({
        'prompts': selected_prompts,
        'total_available': len(prompts),
        'emotion_filter': emotion
    })


@journal_bp.route('/prompts/random', methods=['GET'])
@jwt_required()
def get_random_prompt():
    """
    Get a single random journaling prompt
    Query params: category (optional) - general, anxiety, sadness, gratitude, reflection
    """
    current_username = get_jwt_identity()
    user = User.query.filter_by(username=current_username).first()
    
    if not user:
        return create_error_response("User not found", 404)
    
    category = request.args.get('category')
    
    prompt = JournalPromptLibrary.get_random_prompt(category)
    
    return create_success_response({
        'prompt': prompt,
        'category': category or 'random'
    })


@journal_bp.route('/export', methods=['GET'])
@jwt_required()
def export_journal():
    """
    Export all journal entries as CSV
    """
    current_username = get_jwt_identity()
    user = User.query.filter_by(username=current_username).first()
    
    if not user:
        return create_error_response("User not found", 404)
    
    # Get all entries
    entries = JournalEntry.query.filter_by(user_id=user.id)\
        .order_by(JournalEntry.created_at.asc())\
        .all()
    
    # Create CSV
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow(['ID', 'Title', 'Content', 'Prompt Used', 'Mood Score', 'Emotion Tags', 'Is Favorite', 'Created At', 'Updated At'])
    
    # Write data
    for entry in entries:
        writer.writerow([
            entry.id,
            entry.title or '',
            entry.content,
            entry.prompt_used or '',
            entry.mood_score or '',
            entry.emotion_tags or '',
            'Yes' if entry.is_favorite else 'No',
            entry.created_at.strftime('%Y-%m-%d %H:%M:%S') if entry.created_at else '',
            entry.updated_at.strftime('%Y-%m-%d %H:%M:%S') if entry.updated_at else ''
        ])
    
    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={
            'Content-Disposition': f'attachment; filename=sage_journal_{datetime.now().strftime("%Y%m%d")}.csv'
        }
    )


@journal_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_journal_stats():
    """
    Get journal statistics
    Returns: total entries, average length, most used prompts, etc.
    """
    current_username = get_jwt_identity()
    user = User.query.filter_by(username=current_username).first()
    
    if not user:
        return create_error_response("User not found", 404)
    
    entries = JournalEntry.query.filter_by(user_id=user.id).all()
    
    if not entries:
        return create_success_response({
            'has_entries': False,
            'message': 'No journal entries yet. Write your first entry to see stats!'
        })
    
    # Calculate statistics
    total_entries = len(entries)
    total_words = sum(entry.get_word_count() for entry in entries)
    avg_length = total_words // total_entries if total_entries > 0 else 0
    
    # Count entries by month
    entries_by_month = {}
    for entry in entries:
        month_key = entry.created_at.strftime('%Y-%m') if entry.created_at else 'unknown'
        entries_by_month[month_key] = entries_by_month.get(month_key, 0) + 1
    
    # Find most used prompt
    prompt_count = {}
    for entry in entries:
        if entry.prompt_used:
            prompt_count[entry.prompt_used] = prompt_count.get(entry.prompt_used, 0) + 1
    
    most_used_prompt = max(prompt_count.items(), key=lambda x: x[1])[0] if prompt_count else None
    
    # Calculate writing streak (consecutive days with journal entries)
    # This is a simplified version
    writing_streak = 0
    if entries:
        dates = sorted(set(e.created_at.date() for e in entries if e.created_at))
        from datetime import timedelta
        streak = 1
        for i in range(len(dates) - 1, 0, -1):
            if dates[i] - dates[i-1] == timedelta(days=1):
                streak += 1
            else:
                break
        writing_streak = streak
    
    return create_success_response({
        'has_entries': True,
        'total_entries': total_entries,
        'total_words': total_words,
        'average_words_per_entry': avg_length,
        'writing_streak': writing_streak,
        'entries_by_month': entries_by_month,
        'most_used_prompt': most_used_prompt,
        'favorite_entries': sum(1 for e in entries if e.is_favorite)
    })