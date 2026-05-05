"""
app.py - Sage with Groq AI + Google OAuth + Sentiment Analysis + Intelligent Responses
"""

from flask import Flask, jsonify, request, redirect, session
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta, timezone
from urllib.parse import quote_plus
import bcrypt
import json
import secrets
import os
import re
from authlib.integrations.flask_client import OAuth
from dotenv import load_dotenv
from groq import Groq
from sqlalchemy import inspect, text
from textblob import TextBlob

load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

# ==================== GROQ API ====================
GROQ_API_KEY = (os.environ.get('GROQ_API_KEY') or '').strip()
groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None
if groq_client:
    print('Groq API configured (key from GROQ_API_KEY).')
else:
    print('WARNING: GROQ_API_KEY not set — chat uses keyword fallback until you add it to backend/.env')

# ==================== Initialize App ====================
app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": [
    "http://localhost:3000",
    "https://grand-tartufo-dc4f90.netlify.app",
    os.getenv("FRONTEND_URL", "")
]}}, supports_credentials=True) 

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sage.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = 'sage-secret-key-2024'
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=7)
app.config['SECRET_KEY'] = 'sage-oauth-secret-key-2024'

db = SQLAlchemy(app)
jwt = JWTManager(app)

# ==================== GOOGLE OAUTH ====================
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:5000")

oauth = OAuth(app)
google = oauth.register(
    name='google',
    client_id=GOOGLE_CLIENT_ID,
    client_secret=GOOGLE_CLIENT_SECRET,
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'}
)

# ==================== Database Models ====================

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True)
    password_hash = db.Column(db.String(200))
    google_id = db.Column(db.String(100), unique=True, nullable=True)
    avatar = db.Column(db.String(500), nullable=True)
    streak = db.Column(db.Integer, default=0)
    longest_streak = db.Column(db.Integer, default=0)
    last_checkin = db.Column(db.String(20))
    total_checkins = db.Column(db.Integer, default=0)
    badges = db.Column(db.Text, default='[]')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class ChatMessage(db.Model):
    __tablename__ = 'chat_messages'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    message = db.Column(db.Text, nullable=False)
    explanation = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    sentiment = db.Column(db.String(20))
    sentiment_score = db.Column(db.Float)
    sentiment_emotion = db.Column(db.String(50))

class MoodEntry(db.Model):
    __tablename__ = 'mood_entries'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    mood_score = db.Column(db.Integer, nullable=False)
    date = db.Column(db.String(20), nullable=False)
    note = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class JournalEntry(db.Model):
    __tablename__ = 'journal_entries'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(200))
    content = db.Column(db.Text, nullable=False)
    prompt_used = db.Column(db.String(200))
    is_favorite = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# ==================== Helper Functions ====================

def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password, hashed):
    if not hashed:
        return False
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def get_today_date():
    return datetime.now().strftime('%Y-%m-%d')


def get_chat_calendar_day_bounds():
    """
    Calendar-day window for chat history. Messages use naive UTC (utcnow).
    Day boundaries follow SAGE_CHAT_DAY_TZ (default Asia/Kolkata).
    Returns (start_utc_naive, end_utc_naive, date_iso, day_heading).
    """
    tz_name = os.environ.get('SAGE_CHAT_DAY_TZ', 'Asia/Kolkata')
    try:
        from zoneinfo import ZoneInfo
        tz = ZoneInfo(tz_name)
    except Exception:
        tz = timezone.utc
    now_local = datetime.now(tz)
    start_local = now_local.replace(hour=0, minute=0, second=0, microsecond=0)
    end_local = start_local + timedelta(days=1)
    start_utc_naive = start_local.astimezone(timezone.utc).replace(tzinfo=None)
    end_utc_naive = end_local.astimezone(timezone.utc).replace(tzinfo=None)
    date_iso = now_local.strftime('%Y-%m-%d')
    day_heading = now_local.strftime('%A, %d %B %Y')
    return start_utc_naive, end_utc_naive, date_iso, day_heading


def create_success_response(data, message="Success", status=200):
    return jsonify({'success': True, 'message': message, 'data': data}), status

def create_error_response(error, status=400):
    return jsonify({'success': False, 'error': error}), status

def get_mood_emoji(score):
    if score >= 9: return '😍'
    if score >= 7: return '😊'
    if score >= 5: return '🙂'
    if score >= 3: return '😐'
    return '😔'

def analyze_sentiment(text):
    blob = TextBlob(text)
    polarity = blob.sentiment.polarity
    
    text_lower = text.lower()
    emotion = 'neutral'
    
    if 'graduation' in text_lower or 'job' in text_lower:
        emotion = 'anxiety'
    elif 'anxious' in text_lower or 'anxiety' in text_lower:
        emotion = 'anxiety'
    elif 'excited' in text_lower:
        emotion = 'joy'
    elif 'depressed' in text_lower:
        emotion = 'sadness'
    elif 'sad' in text_lower:
        emotion = 'sadness'
    elif 'overwhelmed' in text_lower:
        emotion = 'stress'
    elif 'happy' in text_lower or 'grateful' in text_lower:
        emotion = 'joy'
    
    sentiment = 'positive' if polarity > 0.2 else ('negative' if polarity < -0.2 else 'neutral')
    
    return {'sentiment': sentiment, 'score': round(polarity, 2), 'emotion': emotion}

# ==================== STREAK FUNCTION ====================

def update_streak(user, today, is_deleting=False):
    from datetime import datetime, timedelta
    
    if is_deleting:
        previous_entry = MoodEntry.query.filter(MoodEntry.user_id == user.id, MoodEntry.date < today).order_by(MoodEntry.date.desc()).first()
        if previous_entry:
            user.streak = 1
            user.last_checkin = previous_entry.date
        else:
            user.streak = 0
            user.last_checkin = None
        user.total_checkins = max(0, user.total_checkins - 1)
        db.session.commit()
        return user.streak, []
    
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    last_checkin = user.last_checkin
    
    if not last_checkin:
        user.streak = 1
        user.last_checkin = today
        user.total_checkins = 1
        user.longest_streak = 1
        
        badges = json.loads(user.badges or '[]')
        if 'First Step' not in badges:
            badges.append('First Step')
            user.badges = json.dumps(badges)
        
        db.session.commit()
        return user.streak, ['First Step']
    
    if last_checkin == today:
        return user.streak, []
    
    if last_checkin == yesterday:
        user.streak += 1
        user.last_checkin = today
        user.total_checkins += 1
        
        if user.streak > user.longest_streak:
            user.longest_streak = user.streak
        
        new_badges = []
        badges = json.loads(user.badges or '[]')
        
        if user.streak >= 7 and 'Resilience Star' not in badges:
            new_badges.append('Resilience Star')
            badges.append('Resilience Star')
        if user.streak >= 14 and 'Mindful Warrior' not in badges:
            new_badges.append('Mindful Warrior')
            badges.append('Mindful Warrior')
        if user.streak >= 30 and 'Wellness Champion' not in badges:
            new_badges.append('Wellness Champion')
            badges.append('Wellness Champion')
        
        if new_badges:
            user.badges = json.dumps(badges)
        
        db.session.commit()
        return user.streak, new_badges
    
    else:
        user.streak = 1
        user.last_checkin = today
        user.total_checkins += 1
        db.session.commit()
        return user.streak, []

# ==================== MENTAL HEALTH FILTER ====================

MENTAL_HEALTH_KEYWORDS = [
    'anxious', 'anxiety', 'sad', 'depressed', 'depression', 'happy', 'joy', 'angry', 'anger',
    'stressed', 'stress', 'overwhelmed', 'lonely', 'loneliness', 'scared', 'fear', 'worried',
    'worry', 'nervous', 'hopeless', 'frustrated', 'calm', 'peaceful', 'excited', 'grateful',
    'mental health', 'wellness', 'mindfulness', 'meditation', 'therapy', 'panic', 'trauma',
    'burnout', 'insomnia', 'sleep', 'grief', 'self esteem', 'feel', 'feeling', 'emotion',
    'cope', 'coping', 'breathe', 'breathing', 'relax', 'journal', 'journaling', 'meditate',
    'hello', 'hi', 'hey', 'yes', 'sure', 'ok', 'okay', 'namaste', 'presentation', 'exam', 'study', 'graduation', 'job'
]

OFF_TOPIC_KEYWORDS = [
    'cricket', 'ipl', 'football', 'movie', 'bollywood', 'politics', 'election', 'stock',
    'crypto', 'bitcoin', 'weather', 'recipe', 'cooking', 'travel', 'game', 'gaming', 'python'
]

REJECTION_MESSAGE = """🌿 I am specifically designed to support your mental health.

I can ONLY respond to:
• Emotions (anxiety, sadness, anger, joy, stress, fear)
• Mental health topics (depression, panic, trauma, grief)
• Wellness practices (mindfulness, meditation, journaling)
• Life challenges (exam stress, work pressure, relationships, graduation, job search)

Please share how you're feeling today. 💚"""


def _contains_whole_word(message_lower: str, word: str) -> bool:
    """Match whole tokens only — substring checks falsely flag e.g. 'car' inside 'scared'."""
    return re.search(
        r'(?<![a-z0-9])' + re.escape(word.lower()) + r'(?![a-z0-9])',
        message_lower,
    ) is not None


def is_mental_health_related(message):
    msg_lower = message.lower()
    
    crisis_words = ['suicide', 'kill myself', 'want to die', 'self harm', 'end my life']
    for word in crisis_words:
        if word in msg_lower:
            return True
    
    greetings = ['hi', 'hello', 'hey', 'namaste', 'good morning', 'good afternoon', 'good evening']
    if msg_lower.strip() in greetings:
        return True
    
    affirmative = ['yes', 'sure', 'ok', 'okay', 'yeah', 'yep', 'yes sure']
    if msg_lower.strip() in affirmative:
        return True
    
    for word in OFF_TOPIC_KEYWORDS:
        if _contains_whole_word(msg_lower, word):
            return False
    
    for keyword in MENTAL_HEALTH_KEYWORDS:
        if keyword in msg_lower:
            return True
    
    return False

# ==================== CONVERSATION MEMORY ====================
conversation_context = {}

# ==================== AI RESPONSE GENERATOR (GROQ) ====================

def generate_ai_response(message, user_id=None):
    """Generate response using Groq API - Simplified Working Version"""
    
    print(f"🔍 [DEBUG] Processing message: {message}")
    
    # Crisis detection (always priority)
    crisis_words = ['suicide', 'kill myself', 'want to die', 'self harm', 'end my life', 'better off dead']
    for word in crisis_words:
        if word in message.lower():
            return {
                'response': "🚨 **CRISIS SUPPORT** 🚨\n\nYour safety matters. Please reach out:\n\n📞 iCall: +91-9152987821\n📞 AASRA: +91-9820466726\n📞 KIRAN: 1800-599-0019\n\nYou are not alone. 💚",
                'explanation': "⚠️ CRISIS DETECTED - Immediate helpline redirect"
            }
    
    # Off-topic detection (whole words only — avoids 'car' matching inside 'scared', etc.)
    off_topic = ['cricket', 'football', 'movie', 'politics', 'bmw', 'car', 'crypto', 'stock']
    msg_lower = message.lower()
    for word in off_topic:
        if _contains_whole_word(msg_lower, word):
            return {
                'response': "🌿 I'm here to support your mental health. Let's focus on how you're feeling emotionally. What's on your mind today?",
                'explanation': "Off-topic - Redirected to wellness"
            }
    
    # Get conversation context (reset when calendar day changes)
    _, _, today_key, _ = get_chat_calendar_day_bounds()
    ctx_key = f"ctx_{user_id}"
    if ctx_key not in conversation_context:
        conversation_context[ctx_key] = {'history': [], 'calendar_day': today_key}
    ctx = conversation_context[ctx_key]
    if ctx.get('calendar_day') != today_key:
        ctx['history'] = []
        ctx['calendar_day'] = today_key

    if groq_client is None:
        return intelligent_fallback(message, ctx)
    
    # Build conversation history
    history_messages = []
    for exchange in ctx['history'][-5:]:
        history_messages.append({"role": "user", "content": exchange['user']})
        history_messages.append({"role": "assistant", "content": exchange['sage']})
    
    # SIMPLE SYSTEM PROMPT
    system_prompt = """You are Sage, a compassionate mental health AI companion for India. Be warm, empathetic, and helpful. Keep responses to 2-4 sentences. Use gentle emojis occasionally. Never give medical advice. Validate the user's feelings first, then offer practical suggestions. If the user asks for other methods, provide a different technique than before."""
    
    try:
        print(f"🔍 [DEBUG] Calling Groq API...")
        
        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                *history_messages,
                {"role": "user", "content": message}
            ],
            temperature=0.8,
            max_tokens=300,
            top_p=0.9
        )
        
        ai_response = response.choices[0].message.content.strip()
        print(f"🔍 [DEBUG] Groq API response: {ai_response[:100]}...")
        
        # Save to context
        ctx['history'].append({'user': message, 'sage': ai_response})
        if len(ctx['history']) > 10:
            ctx['history'] = ctx['history'][-10:]
        
        return {
            'response': ai_response,
            'explanation': "🧠 AI-powered by Groq Llama 3 (70B) - Personalized mental health support"
        }
        
    except Exception as e:
        print(f"🔍 [DEBUG] Groq API ERROR: {e}")
        # Fallback to intelligent responses
        return intelligent_fallback(message, ctx)

def intelligent_fallback(message, ctx):
    """Intelligent fallback responses when Groq API is unavailable"""
    msg_lower = message.lower()
    
    # Check if this is a follow-up asking for more methods
    if any(word in msg_lower for word in ['other', 'another', 'more', 'else', 'different']):
        # Check what was previously discussed
        last_response = ""
        if ctx['history']:
            last_response = ctx['history'][-1].get('sage', '').lower()
        
        if 'grounding' in last_response or '5-4-3-2-1' in last_response:
            return {
                'response': "🌬️ Here's another technique: **Box Breathing**\n\nInhale for 4 seconds\nHold for 4 seconds\nExhale for 4 seconds\nHold for 4 seconds\n\nRepeat 5 times. This activates your parasympathetic nervous system. 💚",
                'explanation': "Providing alternative breathing technique"
            }
        elif 'breathing' in last_response or 'box' in last_response:
            return {
                'response': "📝 Here's a different approach: **Journaling**\n\nWrite down three things you're grateful for today. They can be small - a good cup of coffee, a sunny day, a kind message. Gratitude shifts focus. 📔",
                'explanation': "Providing journaling technique"
            }
        else:
            return {
                'response': "🧘 Here's a **Mindfulness Exercise**:\n\nTake 5 deep breaths. Focus only on the sensation of air moving in and out of your body. When your mind wanders, gently bring it back to your breath. 🌿",
                'explanation': "Providing mindfulness exercise"
            }
    
    # Graduation/Job stress
    if 'graduation' in msg_lower or 'job' in msg_lower:
        return {
            'response': "🎓 Congratulations on completing your graduation! That's a huge achievement! 🎉\n\nThe job search period can be stressful. Break it into small daily tasks, set a routine, and remember: one rejection doesn't define your worth. Would you like to talk more about this? 💚",
            'explanation': "Graduation/Job stress support"
        }
    
    # Depression
    if 'depressed' in msg_lower or 'hopeless' in msg_lower:
        return {
            'response': "💙 I'm sorry you're feeling this way. Small steps can help: get out of bed, eat something nourishing, step outside for 5 minutes, or text one person you trust. Would you like me to suggest a gentle activity? 🫂",
            'explanation': "Depression support"
        }
    
    # Mixed emotions (anxious + excited)
    if ('anxious' in msg_lower or 'anxiety' in msg_lower) and ('excited' in msg_lower):
        return {
            'response': "🌟 That's completely normal! Feeling both anxious AND excited is very common - it's called 'anxious excitement.' Try reframing: 'My body is getting ready for something important.' Would you like to try a breathing exercise? 🧘",
            'explanation': "Mixed emotions - Validation and reframing"
        }
    
    # Anxiety
    if any(w in msg_lower for w in ['anxious', 'anxiety', 'worried', 'nervous']):
        return {
            'response': "🌬️ Try the **5-4-3-2-1 grounding technique**:\n\n• 5 things you can SEE 👁️\n• 4 things you can TOUCH ✋\n• 3 things you can HEAR 👂\n• 2 things you can SMELL 👃\n• 1 thing you can TASTE 👅\n\nThis brings you to the present moment. 💚",
            'explanation': "Anxiety - Grounding technique"
        }
    
    # Sadness/Loneliness
    if any(w in msg_lower for w in ['sad', 'lonely', 'down']):
        return {
            'response': "💙 I hear that you're feeling down. Would you like to try writing down one thing you're grateful for today? Even small things count. I'm here to listen. 🫂",
            'explanation': "Sadness - Support"
        }
    
    # Default
    return {
        'response': "🌿 I'm here for you. Could you tell me more about how you're feeling? I can help with anxiety, stress, sadness, or just listen. What's on your mind? 💚",
        'explanation': "General response"
    }

# ==================== AUTH ROUTES ====================

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy'})

@app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    email = data.get('email', '')
    
    if User.query.filter_by(username=username).first():
        return create_error_response("Username already exists", 400)
    
    new_user = User(username=username, email=email, password_hash=hash_password(password))
    db.session.add(new_user)
    db.session.commit()
    access_token = create_access_token(identity=username)
    return create_success_response({'token': access_token, 'user': {'username': username}}, "Registration successful", 201)

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    user = User.query.filter_by(username=username).first()
    if not user or not verify_password(password, user.password_hash):
        return create_error_response("Invalid credentials", 401)
    
    access_token = create_access_token(identity=username)
    return create_success_response({'token': access_token, 'user': {'username': user.username, 'streak': user.streak}}, "Login successful")

# ==================== GOOGLE OAUTH ROUTES ====================

@app.route('/api/auth/google')
def google_login():
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        return redirect(f'{FRONTEND_URL}/index.html?error=google_oauth_not_configured')
    redirect_uri = f'{BACKEND_URL}/api/auth/google/callback'
    return google.authorize_redirect(redirect_uri, prompt='select_account', access_type='offline', include_granted_scopes='true')

@app.route('/api/auth/google/callback')
def google_callback():
    try:
        token = google.authorize_access_token()
        user_info_resp = google.get('https://openidconnect.googleapis.com/v1/userinfo')
        user_info = user_info_resp.json() if user_info_resp else {}
        if not user_info:
            user_info = google.parse_id_token(token, nonce=None)
        
        email = user_info.get('email')
        google_id = user_info.get('sub')
        name = user_info.get('name', '')
        avatar = user_info.get('picture', '')
        
        user = User.query.filter_by(google_id=google_id).first()
        if not user:
            user = User.query.filter_by(email=email).first()
            if user:
                user.google_id = google_id
                user.avatar = avatar
            else:
                base_username = email.split('@')[0].replace('.', '_')
                username = base_username
                counter = 1
                while User.query.filter_by(username=username).first():
                    username = f"{base_username}_{counter}"
                    counter += 1
                user = User(username=username, email=email, google_id=google_id, avatar=avatar, password_hash='', created_at=datetime.utcnow(), badges='[]', streak=0, total_checkins=0)
                db.session.add(user)
        
        db.session.commit()
        access_token = create_access_token(identity=user.username)
        encoded_username = quote_plus(user.username)
        return redirect(f'{FRONTEND_URL}/auth-callback.html?token={access_token}&user={encoded_username}')
    except Exception as e:
        print(f"Google OAuth Error: {e}")
        return redirect(f'{FRONTEND_URL}/index.html?error=google_auth_failed')

# ==================== CHAT ROUTES ====================

@app.route('/api/chat/send', methods=['POST'])
@jwt_required()
def send_message():
    current_user = get_jwt_identity()
    user = User.query.filter_by(username=current_user).first()
    data = request.get_json()
    message = data.get('message', '')
    
    sentiment_data = analyze_sentiment(message)
    
    user_msg = ChatMessage(user_id=user.id, role='user', message=message, sentiment=sentiment_data['sentiment'], sentiment_score=sentiment_data['score'], sentiment_emotion=sentiment_data['emotion'])
    db.session.add(user_msg)
    
    response_data = generate_ai_response(message, user.id)
    
    bot_msg = ChatMessage(user_id=user.id, role='sage', message=response_data['response'], explanation=response_data['explanation'])
    db.session.add(bot_msg)
    db.session.commit()
    
    response_data['sentiment'] = sentiment_data
    response_data['user_message_id'] = user_msg.id
    return create_success_response(response_data)

@app.route('/api/chat/history', methods=['GET'])
@jwt_required()
def get_chat_history():
    current_user = get_jwt_identity()
    user = User.query.filter_by(username=current_user).first()
    day_start, day_end, date_iso, day_heading = get_chat_calendar_day_bounds()
    messages = (
        ChatMessage.query.filter(
            ChatMessage.user_id == user.id,
            ChatMessage.timestamp >= day_start,
            ChatMessage.timestamp < day_end,
        )
        .order_by(ChatMessage.timestamp.asc())
        .all()
    )
    def _msg_row(m):
        row = {
            'id': m.id,
            'role': m.role,
            'message': m.message,
            'explanation': m.explanation,
            'timestamp': m.timestamp.isoformat(),
        }
        if m.role == 'user':
            row['sentiment'] = m.sentiment
            row['sentiment_score'] = m.sentiment_score
            row['sentiment_emotion'] = m.sentiment_emotion
        return row

    return create_success_response({
        'messages': [_msg_row(m) for m in messages],
        'calendar_date': date_iso,
        'day_heading': day_heading,
    })

@app.route('/api/chat/history', methods=['DELETE'])
@jwt_required()
def delete_chat_history():
    current_user = get_jwt_identity()
    user = User.query.filter_by(username=current_user).first()
    ChatMessage.query.filter_by(user_id=user.id).delete()
    db.session.commit()
    return create_success_response(None, "Chat history cleared")

@app.route('/api/chat/sentiment/<int:message_id>', methods=['GET'])
@jwt_required()
def get_message_sentiment(message_id):
    current_user = get_jwt_identity()
    user = User.query.filter_by(username=current_user).first()
    message = ChatMessage.query.filter_by(id=message_id, user_id=user.id, role='user').first()
    if not message:
        return create_error_response("Message not found", 404)
    expl = (
        f'Polarity score {message.sentiment_score}: reads as {message.sentiment}, '
        f'with {message.sentiment_emotion or "neutral"} tone.'
    )
    return create_success_response({
        'sentiment': message.sentiment,
        'score': message.sentiment_score,
        'emotion': message.sentiment_emotion,
        'message': message.message,
        'explanation': expl,
    })

# ==================== MOOD ROUTES ====================

@app.route('/api/mood/record', methods=['POST'])
@jwt_required()
def record_mood():
    current_user = get_jwt_identity()
    user = User.query.filter_by(username=current_user).first()
    data = request.get_json()
    score = data.get('score')
    
    if not user:
        return create_error_response("User not found", 404)
    
    if score is None or score < 1 or score > 10:
        return create_error_response("Score must be between 1 and 10", 400)
    
    today = get_today_date()
    
    if MoodEntry.query.filter_by(user_id=user.id, date=today).first():
        return create_error_response("You have already logged your mood today. Come back tomorrow!", 400)
    
    new_mood = MoodEntry(user_id=user.id, mood_score=score, date=today)
    db.session.add(new_mood)
    
    new_streak, new_badges = update_streak(user, today, False)
    db.session.commit()
    
    message = f"Mood recorded: {score}/10"
    if new_badges:
        message += f" 🎉 New badge: {', '.join(new_badges)}!"
    
    return create_success_response({'score': score, 'streak': new_streak, 'new_badges': new_badges, 'message': message})

@app.route('/api/mood/delete', methods=['DELETE'])
@jwt_required()
def delete_today_mood():
    current_user = get_jwt_identity()
    user = User.query.filter_by(username=current_user).first()
    today = get_today_date()
    
    mood_entry = MoodEntry.query.filter_by(user_id=user.id, date=today).first()
    if not mood_entry:
        return create_error_response("No mood entry found for today", 404)
    
    db.session.delete(mood_entry)
    update_streak(user, today, True)
    db.session.commit()
    return create_success_response(None, "Today's mood entry deleted")

@app.route('/api/mood/weekly', methods=['GET'])
@jwt_required()
def get_weekly_mood():
    current_user = get_jwt_identity()
    user = User.query.filter_by(username=current_user).first()
    weekly_data = []
    for i in range(6, -1, -1):
        date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
        day_name = (datetime.now() - timedelta(days=i)).strftime('%a')
        entry = MoodEntry.query.filter_by(user_id=user.id, date=date).first()
        weekly_data.append({'day': day_name, 'score': entry.mood_score if entry else None})
    
    return create_success_response({'weekly_data': weekly_data})

@app.route('/api/mood/history', methods=['GET'])
@jwt_required()
def get_mood_history():
    current_user = get_jwt_identity()
    user = User.query.filter_by(username=current_user).first()
    entries = MoodEntry.query.filter_by(user_id=user.id).order_by(MoodEntry.date.desc()).limit(30).all()
    return create_success_response([{'date': e.date, 'score': e.mood_score, 'emoji': get_mood_emoji(e.mood_score)} for e in entries])

# ==================== JOURNAL ROUTES ====================

@app.route('/api/journal/list', methods=['GET'])
@jwt_required()
def list_journals():
    current_user = get_jwt_identity()
    user = User.query.filter_by(username=current_user).first()
    entries = JournalEntry.query.filter_by(user_id=user.id).order_by(JournalEntry.created_at.desc()).all()
    return create_success_response({'entries': [{'id': e.id, 'title': e.title, 'content': e.content, 'preview': e.content[:100], 'created_at': e.created_at.isoformat()} for e in entries]})

@app.route('/api/journal/create', methods=['POST'])
@jwt_required()
def create_journal():
    current_user = get_jwt_identity()
    user = User.query.filter_by(username=current_user).first()
    data = request.get_json()
    entry = JournalEntry(user_id=user.id, title=data.get('title', ''), content=data.get('content'))
    db.session.add(entry)
    db.session.commit()
    return create_success_response({'id': entry.id}, "Journal entry created")

@app.route('/api/journal/<int:entry_id>', methods=['DELETE'])
@jwt_required()
def delete_journal(entry_id):
    current_user = get_jwt_identity()
    user = User.query.filter_by(username=current_user).first()
    entry = JournalEntry.query.filter_by(id=entry_id, user_id=user.id).first()
    if not entry:
        return create_error_response("Entry not found", 404)
    db.session.delete(entry)
    db.session.commit()
    return create_success_response(None, "Entry deleted")

# ==================== USER ROUTES ====================

@app.route('/api/user/streak', methods=['GET'])
@jwt_required()
def get_streak():
    current_user = get_jwt_identity()
    user = User.query.filter_by(username=current_user).first()
    return create_success_response({'current_streak': user.streak, 'longest_streak': user.longest_streak, 'total_checkins': user.total_checkins})

@app.route('/api/user/badges', methods=['GET'])
@jwt_required()
def get_badges():
    current_user = get_jwt_identity()
    user = User.query.filter_by(username=current_user).first()
    badges = json.loads(user.badges) if user.badges else []
    return create_success_response({'earned_badges': badges})

@app.route('/api/user/dashboard', methods=['GET'])
@jwt_required()
def get_dashboard():
    current_user = get_jwt_identity()
    user = User.query.filter_by(username=current_user).first()
    
    weekly_data = []
    for i in range(6, -1, -1):
        date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
        day_name = (datetime.now() - timedelta(days=i)).strftime('%a')
        entry = MoodEntry.query.filter_by(user_id=user.id, date=date).first()
        weekly_data.append({'day': day_name, 'score': entry.mood_score if entry else None})
    
    badges = json.loads(user.badges) if user.badges else []
    return create_success_response({
        'user': {'username': user.username, 'streak': user.streak, 'longest_streak': user.longest_streak, 'total_checkins': user.total_checkins},
        'weekly_mood': weekly_data,
        'badges': [{'name': b} for b in badges],
        'recent_journals': [],
        'mood_logged_today': MoodEntry.query.filter_by(user_id=user.id, date=get_today_date()).first() is not None
    })

# ==================== HELPLINES ROUTES ====================

@app.route('/api/helplines/all', methods=['GET'])
def get_helplines():
    return create_success_response({'helplines': [
        {'name': 'KIRAN — Govt of India', 'number': '1800-599-0019', 'timing': '24×7', 'coverage': 'All India', 'description': 'National mental health helpline.'},
        {'name': 'iCall (TISS)', 'number': '+91-9152987821', 'timing': 'Mon–Sat, 8 AM – 10 PM', 'coverage': 'All India', 'description': 'Free counselling by TISS.'},
        {'name': 'AASRA', 'number': '+91-9820466726', 'timing': '24×7', 'coverage': 'All India', 'description': 'Suicide prevention helpline.'},
        {'name': 'Vandrevala Foundation', 'number': '1860-2662-345', 'timing': '24×7', 'coverage': 'All India', 'description': 'Free 24/7 mental health support.'}
    ]})

# ==================== RUN SERVER ====================

def ensure_chat_message_schema():
    """Add sentiment columns when DB was created before ChatMessage model included them."""
    try:
        insp = inspect(db.engine)
        if 'chat_messages' not in insp.get_table_names():
            return
        existing = {c['name'] for c in insp.get_columns('chat_messages')}
        stmts = []
        if 'sentiment' not in existing:
            stmts.append(text('ALTER TABLE chat_messages ADD COLUMN sentiment VARCHAR(20)'))
        if 'sentiment_score' not in existing:
            stmts.append(text('ALTER TABLE chat_messages ADD COLUMN sentiment_score FLOAT'))
        if 'sentiment_emotion' not in existing:
            stmts.append(text('ALTER TABLE chat_messages ADD COLUMN sentiment_emotion VARCHAR(50)'))
        if not stmts:
            return
        with db.engine.begin() as conn:
            for stmt in stmts:
                conn.execute(stmt)
        print('Applied chat_messages schema migration (sentiment columns).')
    except Exception as e:
        print(f'WARNING: chat_messages schema check failed: {e}')


with app.app_context():
    db.create_all()
    ensure_chat_message_schema()

if __name__ == '__main__':
    with app.app_context():
        if not User.query.filter_by(username='testuser').first():
            demo_user = User(username='testuser', password_hash=hash_password('pass123'))
            db.session.add(demo_user)
            db.session.commit()
            print("✅ Demo user: testuser / pass123")
        if not User.query.filter_by(username='riya').first():
            demo_user2 = User(username='riya', password_hash=hash_password('riya123'))
            db.session.add(demo_user2)
            db.session.commit()
            print("✅ Demo user: riya / riya123")
    
    print("\n" + "="*60)
    print("🌿 SAGE WITH GROQ AI")
    print("="*60)
    print("📡 Server: http://localhost:5000")
    print("🔐 Login: testuser / pass123")
    print("🤖 AI Engine: Groq Llama 3 (70B)")
    print("="*60 + "\n")
    
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)