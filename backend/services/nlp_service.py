"""
nlp_service.py - Natural Language Processing Service for emotion and intent detection

Features:
- Emotion detection (sadness, anxiety, anger, joy, fear, neutral)
- Intent classification (journaling, mindfulness, stress, sleep, gratitude)
- Sentiment analysis (positive, negative, neutral)
- Confidence scoring for explainable AI
- Multi-language support (English, Hindi basic)
"""

import re
from textblob import TextBlob
from ..utils.constants import EMOTION_KEYWORDS, INTENT_KEYWORDS

class NLPService:
    """Main NLP service for emotion and intent detection"""
    
    def __init__(self):
        """Initialize the NLP service"""
        self.emotion_keywords = EMOTION_KEYWORDS
        self.intent_keywords = INTENT_KEYWORDS
    
    def analyze_message(self, text):
        """
        Complete analysis of a user message
        Returns: emotion, intent, sentiment, confidence
        """
        if not text or not text.strip():
            return {
                'emotion': 'neutral',
                'intent': 'general',
                'sentiment': 'neutral',
                'confidence': 0.0,
                'explanation': 'No message provided'
            }
        
        # Clean and preprocess text
        cleaned_text = self._preprocess_text(text)
        
        # Detect emotion (with confidence)
        emotion_result = self.detect_emotion(cleaned_text)
        
        # Detect intent
        intent_result = self.detect_intent(cleaned_text)
        
        # Analyze sentiment
        sentiment_result = self.analyze_sentiment(cleaned_text)
        
        # Combine results
        return {
            'emotion': emotion_result['emotion'],
            'emotion_confidence': emotion_result['confidence'],
            'intent': intent_result['intent'],
            'intent_confidence': intent_result['confidence'],
            'sentiment': sentiment_result['sentiment'],
            'sentiment_score': sentiment_result['polarity'],
            'explanation': self._generate_explanation(emotion_result, intent_result),
            'keywords_detected': emotion_result.get('keywords', []),
            'original_text': text,
            'cleaned_text': cleaned_text
        }
    
    def detect_emotion(self, text):
        """
        Detect primary emotion from text
        Returns: emotion label (sadness, anxiety, anger, joy, fear, neutral)
        """
        text_lower = text.lower()
        
        # Try TextBlob sentiment first (for polarity)
        blob = TextBlob(text)
        polarity = blob.sentiment.polarity
        subjectivity = blob.sentiment.subjectivity
        
        # Keyword-based emotion detection (more specific)
        emotion_scores = {
            'sadness': 0,
            'anxiety': 0,
            'anger': 0,
            'joy': 0,
            'fear': 0,
            'neutral': 0
        }
        
        # Score based on keyword matches
        detected_keywords = []
        for emotion, keywords in self.emotion_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    emotion_scores[emotion] += 1
                    detected_keywords.append(keyword)
        
        # Adjust based on sentiment polarity
        if polarity < -0.3:
            if emotion_scores['sadness'] == 0 and emotion_scores['anxiety'] == 0:
                emotion_scores['sadness'] += 1
        elif polarity > 0.3:
            emotion_scores['joy'] += 1
        
        # Special handling for anxiety vs sadness
        anxiety_words = ['anxious', 'nervous', 'worry', 'panic', 'overthinking']
        sadness_words = ['sad', 'depressed', 'hopeless', 'down', 'gloomy']
        
        anxiety_count = sum(1 for w in anxiety_words if w in text_lower)
        sadness_count = sum(1 for w in sadness_words if w in text_lower)
        
        if anxiety_count > sadness_count and anxiety_count > 0:
            emotion_scores['anxiety'] += anxiety_count
        elif sadness_count > anxiety_count and sadness_count > 0:
            emotion_scores['sadness'] += sadness_count
        
        # Get the highest scoring emotion
        max_score = max(emotion_scores.values())
        if max_score == 0:
            detected_emotion = 'neutral'
            confidence = 0.5
        else:
            # Get emotion(s) with max score
            max_emotions = [e for e, s in emotion_scores.items() if s == max_score]
            detected_emotion = max_emotions[0] if max_emotions else 'neutral'
            # Calculate confidence based on score relative to total
            total_score = sum(emotion_scores.values())
            confidence = max_score / total_score if total_score > 0 else 0.5
            confidence = min(confidence, 0.95)  # Cap at 95%
        
        return {
            'emotion': detected_emotion,
            'confidence': round(confidence, 2),
            'scores': emotion_scores,
            'keywords': detected_keywords[:5]  # Top 5 keywords
        }
    
    def detect_intent(self, text):
        """
        Detect user intent (what they want to do)
        Returns: journaling, mindfulness, stress, sleep, gratitude, general
        """
        text_lower = text.lower()
        
        intent_scores = {
            'journaling': 0,
            'mindfulness': 0,
            'stress_support': 0,
            'sleep': 0,
            'gratitude': 0,
            'general': 0
        }
        
        # Score based on intent keywords
        for intent, keywords in self.intent_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    intent_scores[intent] += 1
        
        # Check for question patterns
        if '?' in text:
            intent_scores['general'] += 1
        
        # Check for action verbs
        action_verbs = ['help', 'advice', 'suggest', 'recommend', 'tell']
        for verb in action_verbs:
            if verb in text_lower:
                intent_scores['general'] += 0.5
        
        # Get highest scoring intent
        max_score = max(intent_scores.values())
        if max_score == 0:
            detected_intent = 'general'
            confidence = 0.5
        else:
            max_intents = [i for i, s in intent_scores.items() if s == max_score]
            detected_intent = max_intents[0] if max_intents else 'general'
            total_score = sum(intent_scores.values())
            confidence = max_score / total_score if total_score > 0 else 0.5
            confidence = min(confidence, 0.9)
        
        return {
            'intent': detected_intent,
            'confidence': round(confidence, 2),
            'scores': intent_scores
        }
    
    def analyze_sentiment(self, text):
        """
        Analyze sentiment polarity and subjectivity
        Returns: sentiment (positive, negative, neutral), polarity score
        """
        blob = TextBlob(text)
        polarity = blob.sentiment.polarity  # -1 (negative) to +1 (positive)
        subjectivity = blob.sentiment.subjectivity  # 0 (objective) to 1 (subjective)
        
        if polarity > 0.2:
            sentiment = 'positive'
        elif polarity < -0.2:
            sentiment = 'negative'
        else:
            sentiment = 'neutral'
        
        return {
            'sentiment': sentiment,
            'polarity': round(polarity, 2),
            'subjectivity': round(subjectivity, 2)
        }
    
    def detect_crisis_keywords(self, text):
        """
        Special detection for crisis/suicide keywords
        Returns: True if crisis keywords found
        """
        from ..utils.constants import CRISIS_KEYWORDS
        
        text_lower = text.lower()
        found_keywords = []
        
        for keyword in CRISIS_KEYWORDS:
            if keyword in text_lower:
                found_keywords.append(keyword)
        
        return {
            'is_crisis': len(found_keywords) > 0,
            'keywords_found': found_keywords
        }
    
    def detect_off_topic(self, text):
        """
        Check if message is off-topic (sports, politics, etc.)
        Returns: True if off-topic
        """
        from ..utils.constants import OFF_TOPIC_KEYWORDS
        
        text_lower = text.lower()
        
        for keyword in OFF_TOPIC_KEYWORDS:
            if keyword in text_lower:
                return True, keyword
        
        return False, None
    
    def _preprocess_text(self, text):
        """
        Clean and preprocess text for better analysis
        """
        # Convert to lowercase
        text = text.lower()
        
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        # Remove special characters (but keep punctuation)
        text = re.sub(r'[^\w\s\?\!\.\,]', '', text)
        
        return text
    
    def _generate_explanation(self, emotion_result, intent_result):
        """
        Generate human-readable explanation of analysis
        Used for XAI (why Sage responded this way)
        """
        emotion = emotion_result['emotion']
        intent = intent_result['intent']
        emotion_confidence = emotion_result['confidence']
        
        explanation_parts = []
        
        # Emotion explanation
        emotion_names = {
            'sadness': 'sadness or low mood',
            'anxiety': 'anxiety or worry',
            'anger': 'anger or frustration',
            'joy': 'positive emotions',
            'fear': 'fear or concern',
            'neutral': 'neutral emotions'
        }
        
        emotion_text = emotion_names.get(emotion, 'various emotions')
        explanation_parts.append(f"Detected {emotion_text}")
        
        if emotion_confidence > 0.7:
            explanation_parts.append("with high confidence")
        
        # Intent explanation
        intent_names = {
            'journaling': 'interest in journaling',
            'mindfulness': 'interest in mindfulness or meditation',
            'stress_support': 'seeking stress management support',
            'sleep': 'concern about sleep',
            'gratitude': 'expressing or seeking gratitude',
            'general': 'general wellness conversation'
        }
        
        intent_text = intent_names.get(intent, 'general conversation')
        explanation_parts.append(f"and {intent_text}")
        
        return ' '.join(explanation_parts)


class EmotionDetector:
    """Simplified emotion detector for specific use cases"""
    
    @staticmethod
    def is_positive(text):
        """Check if message has positive sentiment"""
        blob = TextBlob(text)
        return blob.sentiment.polarity > 0.1
    
    @staticmethod
    def is_negative(text):
        """Check if message has negative sentiment"""
        blob = TextBlob(text)
        return blob.sentiment.polarity < -0.1
    
    @staticmethod
    def get_dominant_emotion(text):
        """Get the most prominent emotion in text"""
        nlp = NLPService()
        result = nlp.detect_emotion(text)
        return result['emotion'], result['confidence']


class IntentClassifier:
    """Simplified intent classifier"""
    
    @staticmethod
    def classify(text):
        """Classify user intent"""
        nlp = NLPService()
        result = nlp.detect_intent(text)
        return result['intent'], result['confidence']