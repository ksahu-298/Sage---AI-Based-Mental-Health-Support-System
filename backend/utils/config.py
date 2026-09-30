"""
constants.py - Central storage for all static data used by Sage
Includes: Indian helplines, crisis keywords, CBT responses, wellness prompts
"""

# ==================== INDIAN MENTAL HEALTH HELPLINES ====================
# Complete list as shown in your screenshot
INDIAN_HELPLINES = [
    {
        'name': 'KIRAN — Govt of India National Helpline',
        'number': '1800-599-0019',
        'timing': '24×7, Toll-free',
        'coverage': 'All India',
        'languages': '13 languages',
        'description': 'Government of India\'s national mental health rehabilitation helpline. Free counselling and referrals.',
        'icon': '🇮🇳'
    },
    {
        'name': 'iCall (TISS)',
        'number': '9152987821',
        'timing': 'Mon–Sat, 8 AM – 10 PM',
        'coverage': 'All India',
        'languages': 'English, Hindi, Marathi',
        'description': 'Free telephone and email counselling by trained mental health professionals from Tata Institute of Social Sciences.',
        'icon': '📞'
    },
    {
        'name': 'Vandrevala Foundation',
        'number': '1860-2662-345',
        'timing': '24×7, Free',
        'coverage': 'All India',
        'languages': 'Multiple',
        'description': 'Free 24/7 mental health support, crisis intervention, and counselling.',
        'icon': '💚'
    },
    {
        'name': 'AASRA',
        'number': '9820466726',
        'timing': '24×7',
        'coverage': 'All India',
        'languages': 'English, Hindi',
        'description': 'Suicide prevention helpline offering confidential emotional support.',
        'icon': '🤝'
    },
    {
        'name': 'NIMHANS Helpline',
        'number': '080-46110007',
        'timing': '24×7',
        'coverage': 'All India',
        'languages': 'Multiple',
        'description': 'National Institute of Mental Health and Neuro-Sciences toll-free psychosocial helpline.',
        'icon': '🏥'
    },
    {
        'name': 'Snehi',
        'number': '9582208181',
        'timing': '10 AM – 10 PM',
        'coverage': 'All India',
        'languages': 'English, Hindi',
        'description': 'Emotional support helpline for anyone in distress, particularly young adults.',
        'icon': '🌿'
    }
]

# ==================== CRISIS DETECTION KEYWORDS ====================
# Immediate redirect to helplines - highest priority
CRISIS_KEYWORDS = [
    # Suicide related
    'suicide', 'suicidal', 'kill myself', 'end my life', 'end my life',
    'want to die', 'i want to die', 'better off dead', 'no reason to live',
    'why should i live', 'i should die', 'take my life',
    
    # Self-harm related
    'self harm', 'self-harm', 'cut myself', 'hurt myself', 'harm myself',
    'injure myself', 'slash my wrist', 'bleed myself',
    
    # Hopelessness (extreme)
    'give up on life', 'i give up', 'cannot go on', 'no hope left',
    'nothing matters anymore', 'worthless', 'i am worthless',
    
    # Urgent help
    'please help me', 'need help immediately', 'emergency mental health',
    'i can\'t do this anymore', 'can\'t take it anymore'
]

# ==================== OFF-TOPIC KEYWORDS ====================
# Topics Sage should NOT respond to (redirects to wellness)
OFF_TOPIC_KEYWORDS = [
    # Sports
    'cricket', 'ipl', 'world cup', 'football', 'soccer', 'match', 'tournament',
    'virat kohli', 'ms dhoni', 'rohit sharma', 'messi', 'ronaldo',
    
    # Entertainment
    'movie', 'film', 'bollywood', 'hollywood', 'netflix', 'prime video',
    'celebrity', 'actor', 'actress', 'song', 'music', 'concert',
    
    # Politics
    'politics', 'election', 'modi', 'rahul gandhi', 'bjp', 'congress',
    'government', 'minister', 'political party', 'voting',
    
    # Finance/Tech
    'stock market', 'crypto', 'bitcoin', 'ethereum', 'investment', 'trading',
    'share market', 'nifty', 'sensex', 'mutual fund',
    
    # Gaming
    'pubg', 'free fire', 'call of duty', 'gaming', 'video game', 'fortnite'
]

# ==================== EMOTION KEYWORDS ====================
# Used for emotion detection when ML is unavailable
EMOTION_KEYWORDS = {
    'sadness': [
        'sad', 'depressed', 'hopeless', 'down', 'gloomy', 'miserable',
        'crying', 'hurt', 'heartbroken', 'lonely', 'alone', 'empty',
        'blue', 'unhappy', 'grief', 'sorrow', 'devastated', 'low'
    ],
    'anxiety': [
        'anxious', 'nervous', 'worried', 'panic', 'overthinking', 'scared',
        'fear', 'terrified', 'restless', 'tense', 'uneasy', 'dread',
        'paranoid', 'phobia', 'panic attack', 'racing thoughts'
    ],
    'anger': [
        'angry', 'frustrated', 'mad', 'annoyed', 'irritated', 'rage',
        'furious', 'bitter', 'resentful', 'hostile', 'agitated', 'pissed'
    ],
    'stress': [
        'stressed', 'overwhelmed', 'pressure', 'burnout', 'tired', 'exhausted',
        'burnt out', 'drained', 'fatigued', 'heavy', 'too much'
    ],
    'joy': [
        'happy', 'joy', 'grateful', 'wonderful', 'excited', 'great', 'good',
        'blessed', 'thankful', 'peaceful', 'content', 'cheerful', 'glad'
    ],
    'fear': [
        'fear', 'scared', 'terrified', 'horror', 'frightened', 'petrified',
        'dreading', 'apprehensive', 'intimidated'
    ],
    'neutral': [
        'okay', 'fine', 'alright', 'so-so', 'meh', 'normal', 'usual'
    ]
}

# ==================== INTENT KEYWORDS ====================
# Detects what user wants to do
INTENT_KEYWORDS = {
    'journaling': [
        'journal', 'write', 'diary', 'reflection', 'record thoughts',
        'write down', 'note', 'document'
    ],
    'mindfulness': [
        'meditate', 'mindful', 'breathe', 'relax', 'calm', 'grounding',
        'presence', 'awareness', 'breathing exercise'
    ],
    'stress_support': [
        'stress', 'anxiety help', 'coping', 'manage stress', 'relief',
        'overwhelmed help', 'calm down'
    ],
    'sleep': [
        'sleep', 'insomnia', 'can\'t sleep', 'rest', 'nightmare',
        'trouble sleeping', 'wake up'
    ],
    'gratitude': [
        'grateful', 'thankful', 'appreciation', 'blessed', 'fortunate'
    ]
}

# ==================== CBT RESPONSE TEMPLATES ====================
# Therapist-guided responses based on detected emotion
CBT_RESPONSES = {
    'sadness': {
        'strategy': 'Behavioral Activation',
        'template': """💙 I hear that you're feeling down. That's a valid emotion, and you're not alone in it.

When we feel sad, our minds often want to withdraw. But here's a gentle CBT technique called **Behavioral Activation** - small actions can slowly lift our mood.

Would you be willing to try one tiny thing right now?
• Write down one small thing you're grateful for today
• Text or call someone you trust
• Step outside for 2 minutes of fresh air

What feels most overwhelming right now - feeling stuck, lonely, or something else?"""
    },
    
    'anxiety': {
        'strategy': 'Grounding & Cognitive Restructuring',
        'template': """🌬️ Anxiety can feel overwhelming, but you're safe right now. Let's try a grounding technique together:

**The 5-4-3-2-1 Method:**
• 5 things you can SEE around you
• 4 things you can TOUCH
• 3 things you can HEAR
• 2 things you can SMELL
• 1 thing you can TASTE

How do you feel after trying that? Anxiety often lives in the future - let's bring you back to the present moment."""
    },
    
    'anger': {
        'strategy': 'Emotion Regulation',
        'template': """⚡ Anger is a signal, not a problem. It tells us something matters to us.

Let's use the **STOP skill** from DBT:
• **S** - Stop. Freeze for a moment.
• **T** - Take a breath. Deep breath in, out slowly.
• **O** - Observe. What's happening in your body right now?
• **P** - Proceed. What would help most right now?

Would you like to explore what's underneath the anger?"""
    },
    
    'stress': {
        'strategy': 'Cognitive Reframing',
        'template': """🍃 That sounds really heavy, and it makes sense that you're feeling this pressure.

When our mind is stressed, it often turns pressure into thoughts like "I'll never manage" or "everything depends on this."

For this moment, try making things smaller: pick just ONE thing you can do in the next 20 minutes, then take a 5-minute break. Small steps calm the brain more than forcing everything at once.

What feels most overwhelming right now - the amount to do, fear of results, or difficulty focusing?"""
    },
    
    'joy': {
        'strategy': 'Savoring & Gratitude',
        'template': """🌟 I'm so glad you're feeling this positivity! In CBT, we call this an opportunity to **savor** - to really soak in the good moments.

Would you like to:
• Write down what contributed to this feeling
• Share this moment with someone
• Or simply sit with this feeling for 30 seconds

You deserve to feel good."""
    },
    
    'neutral': {
        'strategy': 'Wellness Maintenance',
        'template': """✨ Thank you for checking in. Mental wellness isn't just about managing difficult emotions - it's also about building resilience during neutral times.

Would you like to explore:
• A quick mindfulness exercise (2 minutes)
• A journaling prompt about your day
• Some stress management techniques for future use

What feels right for you right now?"""
    },
    
    'fear': {
        'strategy': 'Exposure & Response Prevention',
        'template': """🌿 Fear is our mind trying to protect us - but sometimes it overprotects.

Let's test this fear gently. Ask yourself:
• What evidence do I have that this will happen?
• What's a more balanced way to see this?
• What would I tell a friend in this situation?

Would you like to break down this fear into smaller, manageable pieces?"""
    }
}

# ==================== JOURNALING PROMPTS ====================
DAILY_JOURNAL_PROMPTS = [
    "What are three things you're grateful for today?",
    "How are you feeling right now, without judgment?",
    "What's one small win you had today?",
    "What's something you'd like to let go of?",
    "Describe a moment today that made you smile.",
    "What's one kind thing you can do for yourself tomorrow?",
    "What emotion showed up most today, and where did you feel it in your body?",
    "If you could say 'no' to one thing tomorrow, what would it be?",
    "What's a thought that kept coming back today?",
    "Write a short letter of compassion to yourself."
]

# ==================== DISCLAIMER TEXT ====================
DISCLAIMER = "Sage is a wellness companion and not a substitute for professional mental health care. In a medical emergency, please go to your nearest hospital or call 112."

CRISIS_DISCLAIMER = "⚠️ If you're in immediate danger or have seriously hurt yourself, please call emergency services (112) right now. These helplines have trained professionals ready to support you."

# ==================== WELCOME MESSAGES ====================
WELCOME_MESSAGES = [
    "Hello 🌿 I'm Sage, your mental wellness companion. How are you feeling today?",
    "Welcome back, friend. What's on your mind today?",
    "Ready for a gentle check-in? How's your heart feeling right now?",
    "I'm here, without judgment. Share whatever feels right."
]