"""
response_generator.py - CBT-based Response Generator for Sage

Generates empathetic, therapeutic responses based on:
- Detected emotion (sadness, anxiety, anger, joy, fear, neutral)
- User intent (journaling, mindfulness, stress, sleep, gratitude)
- Conversation context (optional)

Follows CBT (Cognitive Behavioral Therapy) guidelines:
- Validation first
- Psychoeducation second
- Practical technique third
- Gentle follow-up question
"""

import random
from ..utils.constants import CBT_RESPONSES

class ResponseGenerator:
    """Main response generator for Sage bot"""
    
    def __init__(self):
        self.response_templates = CBT_RESPONSES
    
    def generate_response(self, analysis_result, user_message=None, user_name=None):
        """
        Generate a response based on emotion and intent analysis
        
        Parameters:
        - analysis_result: dict from nlp_service.analyze_message()
        - user_message: original user message (for context)
        - user_name: user's name for personalization
        
        Returns:
        - dict with 'response', 'explanation', 'technique', 'follow_up'
        """
        emotion = analysis_result.get('emotion', 'neutral')
        intent = analysis_result.get('intent', 'general')
        sentiment = analysis_result.get('sentiment', 'neutral')
        
        # Get base response template for this emotion
        base_response = self._get_response_for_emotion(emotion, intent)
        
        # Personalize with user name if available
        if user_name and '{name}' in base_response['template']:
            base_response['template'] = base_response['template'].replace('{name}', user_name)
        
        # Add intent-specific enhancements
        enhanced_response = self._enhance_for_intent(base_response, intent)
        
        # Add follow-up question
        follow_up = self._get_follow_up_question(emotion, intent)
        
        # Combine everything
        full_response = enhanced_response['template']
        
        # Add technique suggestion if applicable
        if enhanced_response.get('technique'):
            full_response += f"\n\n**{enhanced_response['technique']}**"
        
        # Add follow-up
        full_response += f"\n\n{follow_up}"
        
        # Generate explanation (XAI)
        explanation = self._generate_explanation(emotion, intent, analysis_result)
        
        return {
            'response': full_response,
            'explanation': explanation,
            'technique': enhanced_response.get('technique'),
            'emotion_detected': emotion,
            'intent_detected': intent,
            'sentiment': sentiment,
            'follow_up_question': follow_up
        }
    
    def _get_response_for_emotion(self, emotion, intent):
        """
        Get appropriate response template based on emotion
        """
        # Use emotion-specific template from constants
        if emotion in self.response_templates:
            template_info = self.response_templates[emotion]
            return {
                'template': template_info['template'],
                'technique': template_info.get('strategy', 'CBT Technique'),
                'validation_level': 'high'
            }
        
        # Fallback for unknown emotions
        return {
            'template': """✨ Thank you for sharing that with me. I'm here to support you.

Would you like to try a quick mindfulness exercise together, or would you prefer to just talk about what's on your mind?

Either way, you're doing something important for your wellbeing by being here.""",
            'technique': 'Active Listening',
            'validation_level': 'medium'
        }
    
    def _enhance_for_intent(self, base_response, intent):
        """
        Add specific guidance based on user intent
        """
        enhanced = base_response.copy()
        
        intent_additions = {
            'journaling': {
                'prefix': "📔 Here's a journaling prompt you might find helpful: ",
                'technique': "Journaling Prompt"
            },
            'mindfulness': {
                'prefix': "🧘 Let's practice a quick mindfulness exercise: ",
                'technique': "Mindfulness Exercise"
            },
            'stress_support': {
                'prefix': "🌬️ Let's try a stress-relief technique together: ",
                'technique': "Stress Management Technique"
            },
            'sleep': {
                'prefix': "🌙 Quality sleep is essential for mental health. ",
                'technique': "Sleep Hygiene Tips"
            },
            'gratitude': {
                'prefix': "💛 That's beautiful. Let's build on that: ",
                'technique': "Gratitude Practice"
            }
        }
        
        if intent in intent_additions:
            addition = intent_additions[intent]
            if enhanced.get('technique'):
                enhanced['technique'] = addition['technique']
        
        return enhanced
    
    def _get_follow_up_question(self, emotion, intent):
        """
        Generate a gentle follow-up question to continue conversation
        """
        follow_ups = {
            'sadness': [
                "What would feel most supportive for you right now?",
                "Would you like to explore what's contributing to this feeling?",
                "What's one small thing that could bring you a moment of comfort?"
            ],
            'anxiety': [
                "Would you like to try a grounding exercise together?",
                "What thoughts are going through your mind right now?",
                "Can you notice where in your body you're feeling this anxiety?"
            ],
            'anger': [
                "What do you think your anger is trying to tell you?",
                "Would taking a few deep breaths help right now?",
                "What would help you feel more at ease in this moment?"
            ],
            'joy': [
                "Would you like to share more about what's making you feel this way?",
                "How can you carry this positive feeling into the rest of your day?",
                "Would you like to journal about this positive moment?"
            ],
            'fear': [
                "What evidence do you have that this fear might come true?",
                "What would you tell a friend who had this fear?",
                "What's one small step you could take to feel safer?"
            ],
            'neutral': [
                "Is there anything specific on your mind today?",
                "Would you like to explore a wellness topic together?",
                "How can I support you today?"
            ]
        }
        
        # Get emotion-specific follow-ups, with fallback to neutral
        options = follow_ups.get(emotion, follow_ups['neutral'])
        return random.choice(options)
    
    def _generate_explanation(self, emotion, intent, analysis_result):
        """
        Generate XAI explanation (Why Sage said this)
        Used for the "Why Sage said this" button
        """
        confidence = analysis_result.get('emotion_confidence', 0.5)
        confidence_text = "high confidence" if confidence > 0.7 else "moderate confidence" if confidence > 0.5 else "preliminary assessment"
        
        emotion_descriptions = {
            'sadness': "sadness or low mood",
            'anxiety': "anxiety or worry",
            'anger': "anger or frustration",
            'joy': "positive emotions",
            'fear': "fear or concern",
            'neutral': "neutral emotional state"
        }
        
        intent_descriptions = {
            'journaling': "interest in expressive writing",
            'mindfulness': "interest in present-moment awareness",
            'stress_support': "need for stress management support",
            'sleep': "concern about rest and sleep",
            'gratitude': "focus on appreciation and gratitude",
            'general': "general wellness conversation"
        }
        
        emotion_text = emotion_descriptions.get(emotion, "various emotions")
        intent_text = intent_descriptions.get(intent, "wellness support")
        
        explanation = f"🧠 Sage detected {emotion_text} with {confidence_text}, and {intent_text}. "
        explanation += "Based on CBT principles, Sage offered validation followed by a practical technique tailored to your emotional state. "
        explanation += "This approach combines emotional support with actionable coping strategies."
        
        return explanation
    
    def generate_crisis_response(self):
        """
        Special response for crisis/suicide detection
        Returns helpline information and safety message
        """
        from ..utils.constants import INDIAN_HELPLINES
        
        helpline_text = ""
        for helpline in INDIAN_HELPLINES[:4]:  # Show top 4 helplines
            helpline_text += f"• **{helpline['name']}**: {helpline['number']} ({helpline['timing']})\n"
        
        response = f"""🚨 **You matter. You are not alone.** 🚨

I'm deeply concerned about what you're sharing. Your safety is the most important thing right now.

**Please reach out to one of these free, confidential helplines in India:**

{helpline_text}

**📞 Emergency Helpline:** 112 (24/7 for any emergency)

These are trained professionals who can provide immediate support. You don't have to go through this alone.

Would you like me to stay with you while you consider reaching out to one of these helplines?"""
        
        explanation = "⚠️ CRISIS DETECTED - Immediate safety protocol activated. Detected keywords indicating self-harm or suicidal ideation. Redirecting to professional helplines as per safety guidelines."
        
        return {
            'response': response,
            'explanation': explanation,
            'is_crisis': True,
            'helplines_provided': True
        }
    
    def generate_off_topic_response(self, detected_topic):
        """
        Response for off-topic messages (sports, politics, etc.)
        Gently redirects to wellness topics
        """
        response = f"""🧘 I notice you mentioned something about "{detected_topic}".

I'm designed specifically to support your mental wellness journey. While I'd love to chat about many topics, my training is focused on helping with feelings, stress, mindfulness, journaling, and emotional wellbeing.

**Let's gently shift back to what matters for your mental health:** How are you feeling emotionally today? Is there something on your mind you'd like to talk about?"""
        
        explanation = f"🚫 Off-topic content detected ('{detected_topic}'). Redirected to wellness conversation per design guidelines."
        
        return {
            'response': response,
            'explanation': explanation,
            'redirected': True
        }
    
    def generate_welcome_message(self, user_name=None):
        """
        Welcome message for new conversations or returning users
        """
        welcome_messages = [
            "🌿 Hello! I'm Sage, your mental wellness companion. How are you feeling today?",
            "Welcome back, friend. What's on your mind today? I'm here to listen without judgment.",
            "Ready for a gentle check-in? How's your heart feeling right now?",
            "I'm here, completely present for you. Share whatever feels right."
        ]
        
        response = random.choice(welcome_messages)
        if user_name:
            response = f"👋 Hello {user_name}! " + response.lower()
        
        explanation = "🎯 Welcome message - setting the tone for a safe, supportive conversation. Reminding user that Sage is non-judgmental and focused on their wellbeing."
        
        return {
            'response': response,
            'explanation': explanation
        }


class CBTResponseGenerator:
    """Simplified interface for the response generator"""
    
    def __init__(self):
        self.generator = ResponseGenerator()
    
    def respond(self, message, analysis_result, user_name=None):
        """Generate a response (main method)"""
        return self.generator.generate_response(analysis_result, message, user_name)
    
    def crisis_respond(self):
        """Generate crisis helpline response"""
        return self.generator.generate_crisis_response()
    
    def off_topic_respond(self, topic):
        """Generate off-topic redirect response"""
        return self.generator.generate_off_topic_response(topic)
    
    def welcome(self, user_name=None):
        """Generate welcome message"""
        return self.generator.generate_welcome_message(user_name)