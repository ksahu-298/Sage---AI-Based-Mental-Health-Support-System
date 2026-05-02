"""
services/__init__.py - Service layer initialization and exports

This file:
1. Makes the services folder a proper Python package
2. Exports all service modules for easy importing
3. Provides convenient access to business logic functions

Services contain:
- NLP/ML logic (emotion detection, intent classification)
- Response generation (CBT-based replies)
- Crisis detection (suicide/self-harm patterns)
- Gamification (streaks, badges, rewards)
"""

# Import all service modules for easy access
from .nlp_service import NLPService, EmotionDetector, IntentClassifier
from .response_generator import ResponseGenerator, CBTResponseGenerator
from .crisis_detector import CrisisDetector, CrisisHandler
from .gamification import GamificationService, BadgeManager, StreakManager

# Create singleton instances for easy import
# This allows: from services import nlp_service
nlp_service = NLPService()
response_generator = ResponseGenerator()
crisis_detector = CrisisDetector()
gamification_service = GamificationService()

# Define what gets exported when someone does: from services import *
__all__ = [
    # Service classes
    'NLPService',
    'EmotionDetector', 
    'IntentClassifier',
    'ResponseGenerator',
    'CBTResponseGenerator',
    'CrisisDetector',
    'CrisisHandler',
    'GamificationService',
    'BadgeManager',
    'StreakManager',
    
    # Singleton instances
    'nlp_service',
    'response_generator', 
    'crisis_detector',
    'gamification_service'
]