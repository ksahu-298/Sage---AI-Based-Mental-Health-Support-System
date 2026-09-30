"""
chat.py - Chat routes for sending messages and retrieving conversation history

Endpoints:
- POST /api/chat/send - Send a message to Sage
- GET /api/chat/history - Get user's chat history
- GET /api/chat/history/:id - Get specific message
- POST /api/chat/feedback/:id - Rate Sage's response
- DELETE /api/chat/history - Clear chat history
"""

from flask import request, jsonify
from datetime import datetime
import json
from .. import chat_bp
from ..models import db, User, ChatMessage
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..utils.helpers import (
    sanitize_input, truncate_text, is_valid_message,
    create_success_response, create_error_response
)
from ..services.nlp_service import NLPService
from ..services.response_generator import ResponseGenerator
from ..services.crisis_detector import CrisisDetector
from ..services.gamification import GamificationService

# Initialize services
nlp_service = NLPService()
response_generator = ResponseGenerator()
crisis_detector = CrisisDetector()
gamification_service = GamificationService()


@chat_bp.route('/send', methods=['POST'])
@jwt_required()
def send_message():
    """
    Send a message to Sage and get a response
    Expected JSON: { message }
    Returns: { response, explanation, emotion, intent }
    """
    current_username = get_jwt_identity()
    user = User.query.filter_by(username=current_username).first()
    
    if not user:
        return create_error_response("User not found", 404)
    
    data = request.get_json()
    user_message = data.get('message', '').strip()
    
    # Validate message
    if not is_valid_message(user_message):
        return create_error_response("Message cannot be empty", 400)
    
    # Sanitize input
    user_message = sanitize_input(user_message)
    user_message = truncate_text(user_message, 2000)
    
    # Save user message to database
    user_msg = ChatMessage.create_user_message(user.id, user_message)
    db.session.add(user_msg)
    db.session.commit()
    
    # STEP 1: Check for crisis keywords (highest priority)
    crisis_analysis = crisis_detector.analyze_message(user_message)
    
    if crisis_analysis['is_crisis']:
        # Get crisis response with helplines
        crisis_response = crisis_detector.get_helpline_response(crisis_analysis['severity'])
        
        # Save bot response
        bot_msg = ChatMessage.create_sage_response(
            user.id,
            crisis_response['response'],
            explanation=crisis_response['explanation'],
            emotion='crisis',
            intent='crisis_support',
            is_crisis=True
        )
        db.session.add(bot_msg)
        db.session.commit()
        
        return create_success_response({
            'response': crisis_response['response'],
            'explanation': crisis_response['explanation'],
            'emotion': 'crisis',
            'intent': 'crisis_support',
            'is_crisis': True,
            'helplines': crisis_detector.get_all_helplines()[:4]
        })
    
    # STEP 2: Check for off-topic content
    is_off_topic, off_topic_keyword = crisis_detector.detector.detect_off_topic(user_message)
    
    if is_off_topic:
        off_topic_response = response_generator.generate_off_topic_response(off_topic_keyword)
        
        bot_msg = ChatMessage.create_sage_response(
            user.id,
            off_topic_response['response'],
            explanation=off_topic_response['explanation'],
            emotion='off_topic',
            intent='redirect'
        )
        db.session.add(bot_msg)
        db.session.commit()
        
        return create_success_response({
            'response': off_topic_response['response'],
            'explanation': off_topic_response['explanation'],
            'emotion': 'off_topic',
            'intent': 'redirect',
            'is_off_topic': True
        })
    
    # STEP 3: Analyze message for emotion and intent
    analysis = nlp_service.analyze_message(user_message)
    
    # STEP 4: Generate response based on analysis
    response_data = response_generator.generate_response(
        analysis,
        user_message,
        user.username
    )
    
    # STEP 5: Save bot response to database
    bot_msg = ChatMessage.create_sage_response(
        user.id,
        response_data['response'],
        explanation=response_data['explanation'],
        emotion=analysis['emotion'],
        intent=analysis['intent'],
        confidence=analysis.get('emotion_confidence', 0.5)
    )
    db.session.add(bot_msg)
    db.session.commit()
    
    # STEP 6: Update chat count for gamification (optional)
    chat_count = ChatMessage.query.filter_by(
        user_id=user.id, 
        role='user'
    ).count()
    
    # Check for chat-based badges
    new_badges = gamification_service.check_chat_based_badges(user, chat_count)
    if new_badges:
        db.session.commit()
    
    # Return response
    return create_success_response({
        'response': response_data['response'],
        'explanation': response_data['explanation'],
        'emotion': analysis['emotion'],
        'intent': analysis['intent'],
        'emotion_confidence': analysis.get('emotion_confidence'),
        'technique': response_data.get('technique'),
        'new_badges': new_badges if new_badges else None
    })


@chat_bp.route('/history', methods=['GET'])
@jwt_required()
def get_chat_history():
    """
    Get user's chat history
    Query params: limit (default 50), offset (default 0)
    """
    current_username = get_jwt_identity()
    user = User.query.filter_by(username=current_username).first()
    
    if not user:
        return create_error_response("User not found", 404)
    
    # Get pagination parameters
    limit = request.args.get('limit', 50, type=int)
    offset = request.args.get('offset', 0, type=int)
    
    # Limit max messages
    limit = min(limit, 100)
    
    # Get messages
    messages = ChatMessage.query.filter_by(user_id=user.id)\
        .order_by(ChatMessage.timestamp.desc())\
        .offset(offset)\
        .limit(limit)\
        .all()
    
    # Reverse to show chronological order
    messages = list(reversed(messages))
    
    return create_success_response({
        'messages': [msg.to_dict() for msg in messages],
        'total': ChatMessage.query.filter_by(user_id=user.id).count(),
        'limit': limit,
        'offset': offset
    })


@chat_bp.route('/history/<int:message_id>', methods=['GET'])
@jwt_required()
def get_single_message(message_id):
    """
    Get a specific message by ID
    """
    current_username = get_jwt_identity()
    user = User.query.filter_by(username=current_username).first()
    
    if not user:
        return create_error_response("User not found", 404)
    
    message = ChatMessage.query.filter_by(id=message_id, user_id=user.id).first()
    
    if not message:
        return create_error_response("Message not found", 404)
    
    return create_success_response(message.to_dict())


@chat_bp.route('/feedback/<int:message_id>', methods=['POST'])
@jwt_required()
def submit_feedback(message_id):
    """
    Submit feedback for a Sage response
    Expected JSON: { rating (1-5), was_helpful (boolean) }
    """
    current_username = get_jwt_identity()
    user = User.query.filter_by(username=current_username).first()
    
    if not user:
        return create_error_response("User not found", 404)
    
    message = ChatMessage.query.filter_by(id=message_id, user_id=user.id).first()
    
    if not message:
        return create_error_response("Message not found", 404)
    
    # Only allow feedback on bot messages
    if message.role != 'sage':
        return create_error_response("Can only provide feedback on Sage responses", 400)
    
    data = request.get_json()
    
    rating = data.get('rating')
    was_helpful = data.get('was_helpful')
    
    if rating is not None:
        if 1 <= rating <= 5:
            message.user_rating = rating
        else:
            return create_error_response("Rating must be between 1 and 5", 400)
    
    if was_helpful is not None:
        message.was_helpful = was_helpful
    
    db.session.commit()
    
    return create_success_response(None, "Feedback submitted successfully")


@chat_bp.route('/history', methods=['DELETE'])
@jwt_required()
def clear_chat_history():
    """
    Clear all chat history for the current user
    """
    current_username = get_jwt_identity()
    user = User.query.filter_by(username=current_username).first()
    
    if not user:
        return create_error_response("User not found", 404)
    
    # Delete all chat messages for this user
    ChatMessage.query.filter_by(user_id=user.id).delete()
    db.session.commit()
    
    return create_success_response(None, "Chat history cleared successfully")


@chat_bp.route('/context', methods=['GET'])
@jwt_required()
def get_conversation_context():
    """
    Get recent conversation context (last 10 messages)
    Useful for UI to show context without loading full history
    """
    current_username = get_jwt_identity()
    user = User.query.filter_by(username=current_username).first()
    
    if not user:
        return create_error_response("User not found", 404)
    
    # Get last 10 messages
    messages = ChatMessage.query.filter_by(user_id=user.id)\
        .order_by(ChatMessage.timestamp.desc())\
        .limit(10)\
        .all()
    
    messages = list(reversed(messages))
    
    return create_success_response({
        'messages': [msg.to_preview_dict() for msg in messages],
        'count': len(messages)
    })


@chat_bp.route('', methods=['GET'])
@jwt_required()
def chat_index():
    """
    Chat index endpoint - just a placeholder
    Returns basic chat info
    """
    current_username = get_jwt_identity()
    user = User.query.filter_by(username=current_username).first()
    
    total_messages = ChatMessage.query.filter_by(user_id=user.id).count() if user else 0
    
    return create_success_response({
        'status': 'active',
        'bot_name': 'Sage',
        'total_messages': total_messages,
        'message': "Sage is ready to support your mental wellness journey."
    })