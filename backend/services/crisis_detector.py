"""
crisis_detector.py - Crisis Detection Service for immediate safety intervention

Priority: HIGHEST (this runs before any other processing)
Purpose: Detect suicide/self-harm keywords and redirect to professional helplines

Key principles:
- Safety first - never take risks with crisis content
- Provide immediate helpline numbers
- Be compassionate and non-judgmental
- Never leave the user alone in the response
"""

import re
from datetime import datetime
from ..utils.constants import INDIAN_HELPLINES, CRISIS_KEYWORDS

class CrisisDetector:
    """
    Detects crisis-level content in user messages
    This is the first line of safety defense
    """
    
    def __init__(self):
        self.crisis_keywords = CRISIS_KEYWORDS
        self.helplines = INDIAN_HELPLINES
        
        # Compile regex patterns for faster matching
        self.compiled_patterns = [re.compile(rf'\b{re.escape(keyword)}\b', re.IGNORECASE) 
                                  for keyword in self.crisis_keywords]
        
        # Context words that might indicate passive vs active risk
        self.passive_indicators = ['sometimes', 'sometimes i feel', 'i think about', 'in the past']
        self.active_indicators = ['going to', 'plan to', 'today', 'right now', 'need help now']
        
        # Store recent crisis detections for admin alerts (optional)
        self.recent_crisis_alerts = []
    
    def analyze_message(self, text):
        """
        Analyze message for crisis content
        
        Returns:
        - is_crisis: boolean
        - severity: 'low', 'medium', 'high', 'immediate'
        - keywords_found: list of matched keywords
        - recommended_action: what to do
        """
        if not text or not text.strip():
            return {
                'is_crisis': False,
                'severity': None,
                'keywords_found': [],
                'recommended_action': None,
                'context_clues': []
            }
        
        text_lower = text.lower()
        matched_keywords = []
        
        # Check for crisis keywords
        for keyword in self.crisis_keywords:
            if keyword in text_lower:
                matched_keywords.append(keyword)
        
        # Determine severity based on keyword types
        severity = self._determine_severity(matched_keywords, text_lower)
        
        # Check context clues for additional info
        context_clues = self._analyze_context(text_lower)
        
        is_crisis = len(matched_keywords) > 0
        
        # Recommended action based on severity
        if is_crisis:
            if severity == 'immediate':
                recommended_action = 'SHOW_HELPLINES_IMMEDIATE'
            elif severity == 'high':
                recommended_action = 'SHOW_HELPLINES_URGENT'
            elif severity == 'medium':
                recommended_action = 'SHOW_HELPLINES_AND_CHECK_IN'
            else:
                recommended_action = 'ASK_MORE_AND_OFFER_HELPLINES'
        else:
            recommended_action = 'NORMAL_RESPONSE'
        
        # Log crisis for audit (without storing full message)
        if is_crisis and severity in ['high', 'immediate']:
            self._log_crisis_alert(keywords=matched_keywords, severity=severity)
        
        return {
            'is_crisis': is_crisis,
            'severity': severity,
            'keywords_found': matched_keywords,
            'recommended_action': recommended_action,
            'context_clues': context_clues
        }
    
    def _determine_severity(self, keywords, full_text):
        """
        Determine crisis severity based on keywords and context
        """
        if not keywords:
            return None
        
        # Immediate severity keywords - active planning
        immediate_keywords = ['kill myself', 'ending it', 'take my life', 'going to die']
        for kw in immediate_keywords:
            if kw in ' '.join(keywords) or kw in full_text:
                return 'immediate'
        
        # High severity keywords
        high_keywords = ['suicide', 'self harm', 'cut myself', 'hurt myself']
        for kw in high_keywords:
            if kw in ' '.join(keywords) or kw in full_text:
                # Check if it's passive or active
                if any(indicator in full_text for indicator in self.active_indicators):
                    return 'immediate'
                return 'high'
        
        # Medium severity
        medium_keywords = ['want to die', 'no reason to live', 'better off dead']
        for kw in medium_keywords:
            if kw in ' '.join(keywords) or kw in full_text:
                return 'medium'
        
        return 'low'
    
    def _analyze_context(self, text):
        """
        Analyze context around crisis keywords
        For example: "I used to feel suicidal but I'm better now" vs "I feel suicidal"
        """
        clues = {
            'has_passive_language': False,
            'has_active_language': False,
            'has_past_tense': False,
            'has_hopelessness': False,
            'has_request_for_help': False
        }
        
        # Check for passive vs active language
        if any(indicator in text for indicator in self.passive_indicators):
            clues['has_passive_language'] = True
        
        if any(indicator in text for indicator in self.active_indicators):
            clues['has_active_language'] = True
        
        # Check for past tense (might indicate historical, not current)
        past_words = ['used to', 'in the past', 'previously', 'before', 'was']
        if any(word in text for word in past_words):
            clues['has_past_tense'] = True
        
        # Check for hopelessness language
        hopeless_words = ['hopeless', 'nothing matters', 'no point', 'why bother']
        if any(word in text for word in hopeless_words):
            clues['has_hopelessness'] = True
        
        # Check if user is explicitly asking for help
        help_words = ['help me', 'need help', 'please help', 'what should i do']
        if any(word in text for word in help_words):
            clues['has_request_for_help'] = True
        
        return clues
    
    def _log_crisis_alert(self, keywords, severity):
        """
        Log crisis detection for audit (anonymous)
        Do NOT store the actual user message for privacy
        """
        alert = {
            'timestamp': datetime.now().isoformat(),
            'severity': severity,
            'keywords': keywords[:3],  # Store only first 3 keywords
            'action_taken': 'HELPLINES_DISPLAYED'
        }
        
        self.recent_crisis_alerts.append(alert)
        
        # Keep only last 100 alerts
        if len(self.recent_crisis_alerts) > 100:
            self.recent_crisis_alerts = self.recent_crisis_alerts[-100:]
        
        # Optional: In production, you could send email alert to admin
        # self._send_admin_alert(alert)
    
    def get_helpline_response(self, severity='high'):
        """
        Generate appropriate helpline response based on severity
        """
        if severity == 'immediate':
            return self._get_immediate_crisis_response()
        elif severity == 'high':
            return self._get_urgent_crisis_response()
        else:
            return self._get_standard_crisis_response()
    
    def _get_immediate_crisis_response(self):
        """Most urgent response - immediate action required"""
        helplines_text = self._format_helplines(top_n=3)
        
        return {
            'response': f"""🚨 **IMMEDIATE SUPPORT NEEDED** 🚨

What you're sharing is very serious. Your safety is the number one priority right now.

**Please contact a crisis helpline IMMEDIATELY:**

{helplines_text}

**📞 Emergency Services (India):** 112

You don't have to face this alone. These professionals are trained to help people who feel exactly the way you're feeling right now.

Please reach out to one of these numbers now. I will stay right here with you.

Would you like me to help you find the nearest hospital or mental health emergency service?""",
            'explanation': "⚠️ IMMEDIATE CRISIS - Active suicide/self-harm planning detected. Highest priority response with multiple helplines and emergency number.",
            'severity': 'immediate',
            'requires_immediate_action': True
        }
    
    def _get_urgent_crisis_response(self):
        """Urgent response for high severity"""
        helplines_text = self._format_helplines(top_n=4)
        
        return {
            'response': f"""🚨 **Please reach out for support right now** 🚨

I'm hearing that you're in significant distress. This is important, and you deserve immediate support.

**Free & Confidential Helplines in India:**

{helplines_text}

You matter. These professionals are ready to listen right now. Would you like me to stay with you while you consider calling?""",
            'explanation': "⚠️ URGENT CRISIS - Self-harm or suicidal ideation detected. Providing helpline information with compassionate urgency.",
            'severity': 'high',
            'requires_immediate_action': True
        }
    
    def _get_standard_crisis_response(self):
        """Standard response for crisis keywords without immediate planning"""
        helplines_text = self._format_helplines(top_n=3)
        
        return {
            'response': f"""💚 **You are not alone**

Thank you for being honest about how you're feeling. What you're sharing is important, and there are people who want to support you.

**Here are some resources that can help:**

{helplines_text}

Would you like to talk more about what's going on? I'm here to listen, and these professionals can provide specialized support if you need it.""",
            'explanation': "⚠️ CRISIS KEYWORDS DETECTED - Providing helpline information preventively. No immediate action plan detected but offering resources.",
            'severity': 'medium',
            'requires_immediate_action': False
        }
    
    def _format_helplines(self, top_n=4):
        """Format helplines as readable text"""
        lines = []
        for helpline in self.helplines[:top_n]:
            lines.append(f"📞 **{helpline['name']}**: {helpline['number']}")
            lines.append(f"   ⏰ {helpline['timing']} | 📍 {helpline['coverage']}")
            lines.append("")
        
        return '\n'.join(lines)
    
    def get_all_helplines(self):
        """Return all helplines for the dedicated helplines page"""
        return self.helplines
    
    def get_kiran_helpline(self):
        """Return KIRAN helpline info"""
        for h in self.helplines:
            if 'KIRAN' in h['name']:
                return h
        return None
    
    def get_icall_helpline(self):
        """Return iCall helpline info"""
        for h in self.helplines:
            if 'iCall' in h['name']:
                return h
        return None
    
    def is_crisis_message(self, text):
        """Quick boolean check if message contains crisis content"""
        result = self.analyze_message(text)
        return result['is_crisis']


class CrisisHandler:
    """Simplified handler for crisis detection"""
    
    def __init__(self):
        self.detector = CrisisDetector()
    
    def check_and_respond(self, message_text):
        """
        Check message and return appropriate crisis response if needed
        Returns: (is_crisis, response_data)
        """
        analysis = self.detector.analyze_message(message_text)
        
        if analysis['is_crisis']:
            response = self.detector.get_helpline_response(analysis['severity'])
            return True, response
        else:
            return False, None
    
    def get_helplines_page_data(self):
        """Get complete helplines data for the dedicated helplines page"""
        return {
            'helplines': self.detector.get_all_helplines(),
            'disclaimer': "Sage is a wellness companion and not a substitute for professional mental health care. In a medical emergency, please go to your nearest hospital or call 112.",
            'emergency_number': '112',
            'updated_at': datetime.now().strftime('%Y-%m-%d')
        }