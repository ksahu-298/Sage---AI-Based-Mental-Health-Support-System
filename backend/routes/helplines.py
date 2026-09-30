"""
helplines.py - Helplines routes for crisis resources and Indian helpline information

Endpoints:
- GET /api/helplines/all - Get all Indian helplines
- GET /api/helplines/emergency - Get emergency contact numbers
- GET /api/helplines/crisis - Get crisis response information
- GET /api/helplines/kiran - Get KIRAN helpline details
- GET /api/helplines/icall - Get iCall helpline details
"""

from flask import request
from datetime import datetime
from .. import helplines_bp
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..utils.helpers import create_success_response
from ..utils.constants import INDIAN_HELPLINES


@helplines_bp.route('/all', methods=['GET'])
def get_all_helplines():
    """
    Get all Indian mental health helplines
    No authentication required - crisis resources should be accessible to everyone
    """
    return create_success_response({
        'helplines': INDIAN_HELPLINES,
        'total': len(INDIAN_HELPLINES),
        'last_updated': '2024-01-01',
        'disclaimer': "Sage is a wellness companion and not a substitute for professional mental health care. In a medical emergency, please go to your nearest hospital or call 112."
    })


@helplines_bp.route('/emergency', methods=['GET'])
def get_emergency_numbers():
    """
    Get emergency contact numbers (for immediate crisis)
    Returns just the most critical numbers for quick access
    """
    emergency_helplines = [
        {
            'name': 'Emergency Services (India)',
            'number': '112',
            'description': 'For any medical or police emergency - 24/7',
            'priority': 1
        },
        {
            'name': 'KIRAN (Govt of India)',
            'number': '1800-599-0019',
            'description': 'National Mental Health Helpline - 24/7, Toll-free',
            'priority': 2
        },
        {
            'name': 'iCall (TISS)',
            'number': '+91-9152987821',
            'description': 'Free telephone counselling - Mon-Sat, 8 AM - 10 PM',
            'priority': 2
        }
    ]
    
    return create_success_response({
        'emergency_numbers': emergency_helplines,
        'message': "If you're in immediate danger, please call 112 right now."
    })


@helplines_bp.route('/crisis', methods=['GET'])
def get_crisis_response():
    """
    Get crisis response information
    Returns formatted crisis message for display
    """
    crisis_response = {
        'title': "You are not alone.",
        'message': "If you're in distress or thinking about hurting yourself, please reach out to one of these free, confidential helplines in India. Trained humans are ready to listen.",
        'helplines': INDIAN_HELPLINES,
        'emergency': {
            'number': '112',
            'instruction': "In a medical emergency, please go to your nearest hospital or call 112 immediately."
        },
        'disclaimer': "Sage is a wellness companion and not a substitute for professional mental health care."
    }
    
    return create_success_response(crisis_response)


@helplines_bp.route('/kiran', methods=['GET'])
def get_kiran_helpline():
    """
    Get KIRAN helpline details specifically
    """
    kiran = None
    for h in INDIAN_HELPLINES:
        if 'KIRAN' in h['name']:
            kiran = h
            break
    
    if kiran:
        return create_success_response(kiran)
    else:
        return create_success_response({
            'name': 'KIRAN',
            'number': '1800-599-0019',
            'timing': '24×7',
            'coverage': 'All India',
            'description': 'Government of India National Mental Health Helpline'
        })


@helplines_bp.route('/icall', methods=['GET'])
def get_icall_helpline():
    """
    Get iCall helpline details specifically
    """
    icall = None
    for h in INDIAN_HELPLINES:
        if 'iCall' in h['name']:
            icall = h
            break
    
    if icall:
        return create_success_response(icall)
    else:
        return create_success_response({
            'name': 'iCall (TISS)',
            'number': '9152987821',
            'timing': 'Mon–Sat, 8 AM – 10 PM',
            'coverage': 'All India',
            'description': 'Free telephone and email counselling by trained mental health professionals from Tata Institute of Social Sciences.'
        })


@helplines_bp.route('/vandrevala', methods=['GET'])
def get_vandrevala_helpline():
    """
    Get Vandrevala Foundation helpline details
    """
    vandrevala = None
    for h in INDIAN_HELPLINES:
        if 'Vandrevala' in h['name']:
            vandrevala = h
            break
    
    if vandrevala:
        return create_success_response(vandrevala)
    else:
        return create_success_response({
            'name': 'Vandrevala Foundation',
            'number': '1860-2662-345',
            'timing': '24×7, Free',
            'coverage': 'All India',
            'description': 'Free 24/7 mental health support, crisis intervention, and counselling.'
        })


@helplines_bp.route('/aasra', methods=['GET'])
def get_aasra_helpline():
    """
    Get AASRA helpline details
    """
    aasra = None
    for h in INDIAN_HELPLINES:
        if 'AASRA' in h['name']:
            aasra = h
            break
    
    if aasra:
        return create_success_response(aasra)
    else:
        return create_success_response({
            'name': 'AASRA',
            'number': '9820466726',
            'timing': '24×7',
            'coverage': 'All India',
            'description': 'Suicide prevention helpline offering confidential emotional support.'
        })


@helplines_bp.route('/nimhans', methods=['GET'])
def get_nimhans_helpline():
    """
    Get NIMHANS helpline details
    """
    nimhans = None
    for h in INDIAN_HELPLINES:
        if 'NIMHANS' in h['name']:
            nimhans = h
            break
    
    if nimhans:
        return create_success_response(nimhans)
    else:
        return create_success_response({
            'name': 'NIMHANS Helpline',
            'number': '080-46110007',
            'timing': '24×7',
            'coverage': 'All India',
            'description': 'National Institute of Mental Health and Neuro-Sciences toll-free psychosocial helpline.'
        })


@helplines_bp.route('/snehi', methods=['GET'])
def get_snehi_helpline():
    """
    Get Snehi helpline details
    """
    snehi = None
    for h in INDIAN_HELPLINES:
        if 'Snehi' in h['name']:
            snehi = h
            break
    
    if snehi:
        return create_success_response(snehi)
    else:
        return create_success_response({
            'name': 'Snehi',
            'number': '9582208181',
            'timing': '10 AM – 10 PM',
            'coverage': 'All India',
            'description': 'Emotional support helpline for anyone in distress, particularly young adults.'
        })


@helplines_bp.route('/state', methods=['GET'])
def get_state_helplines():
    """
    Get state-specific helplines (optional - for future expansion)
    Query param: state (e.g., 'Maharashtra', 'Delhi', 'Karnataka')
    """
    state = request.args.get('state', '').lower()
    
    # State-specific helplines (expandable)
    state_helplines = {
        'maharashtra': [
            {'name': 'Mumbai Police Mental Health Helpline', 'number': '022-24937333'}
        ],
        'delhi': [
            {'name': 'Delhi Government Mental Health Helpline', 'number': '9868432244'}
        ],
        'karnataka': [
            {'name': 'Bangalore Helpline', 'number': '080-46110007'}
        ]
    }
    
    helplines = state_helplines.get(state, [])
    
    return create_success_response({
        'state': state.capitalize() if state else 'All India',
        'helplines': helplines,
        'message': 'For national helplines, please use /api/helplines/all'
    })


@helplines_bp.route('/resources', methods=['GET'])
def get_mental_health_resources():
    """
    Get additional mental health resources (websites, apps, articles)
    """
    resources = {
        'websites': [
            {'name': 'Mind India', 'url': 'https://mindindia.org', 'description': 'Mental health awareness and resources'},
            {'name': 'The Live Love Laugh Foundation', 'url': 'https://thelivelovelaughfoundation.org', 'description': 'Mental health resources for young Indians'},
            {'name': 'Mpower', 'url': 'https://mpowerminds.com', 'description': 'Mental health awareness and support'}
        ],
        'apps': [
            {'name': 'Calm', 'description': 'Meditation and mindfulness app'},
            {'name': 'Mindhouse', 'description': 'Mental wellness app by Indian creators'}
        ],
        'articles': [
            {'title': 'Understanding Anxiety', 'url': '#'},
            {'title': 'Coping with Depression', 'url': '#'},
            {'title': 'Building Resilience', 'url': '#'}
        ]
    }
    
    return create_success_response(resources)