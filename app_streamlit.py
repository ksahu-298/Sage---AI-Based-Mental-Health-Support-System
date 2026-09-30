import streamlit as st
import sqlite3
import os
import re
import json
import hashlib
from datetime import datetime, timedelta
import pandas as pd
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ==================== PAGE CONFIG & THEME ====================
st.set_page_config(
    page_title="Sage — AI Mental Health Support Companion",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Premium Sage Aesthetic
st.markdown("""
<style>
    /* Main Theme Palette */
    :root {
        --primary-green: #2D6A4F;
        --secondary-green: #52B788;
        --accent-mint: #D8F3DC;
        --bg-sage: #F5F7F2;
        --text-dark: #1B4332;
        --card-bg: #FFFFFF;
    }
    
    /* Global Styles */
    .stApp {
        background-color: #F5F7F2;
        font-family: 'Inter', sans-serif;
    }
    
    /* Header Banner */
    .sage-header {
        background: linear-gradient(135deg, #1B4332 0%, #2D6A4F 50%, #40916C 100%);
        padding: 2rem 2.5rem;
        border-radius: 16px;
        color: white;
        box-shadow: 0 10px 25px rgba(45, 106, 79, 0.15);
        margin-bottom: 2rem;
    }
    .sage-header h1 {
        font-size: 2.2rem;
        font-weight: 700;
        margin: 0;
        color: #FFFFFF !important;
        display: flex;
        align-items: center;
        gap: 12px;
    }
    .sage-header p {
        font-size: 1.05rem;
        color: #D8F3DC;
        margin-top: 0.5rem;
        margin-bottom: 0;
    }

    /* Cards */
    .sage-card {
        background: white;
        border-radius: 14px;
        padding: 1.5rem;
        border: 1px solid #E2E8E0;
        box-shadow: 0 4px 12px rgba(0,0,0,0.03);
        margin-bottom: 1rem;
    }
    
    /* Badge Pill */
    .badge-pill {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: #E8F5E9;
        color: #1B4332;
        border: 1px solid #A5D6A7;
        padding: 6px 14px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.88rem;
        margin: 4px;
    }
    .badge-locked {
        background: #F3F4F6;
        color: #9CA3AF;
        border: 1px solid #E5E7EB;
    }

    /* Chat Bubbles */
    .user-bubble {
        background-color: #2D6A4F;
        color: white;
        padding: 12px 18px;
        border-radius: 18px 18px 2px 18px;
        margin: 8px 0;
        max-width: 80%;
        margin-left: auto;
        font-size: 0.98rem;
    }
    .sage-bubble {
        background-color: #FFFFFF;
        color: #1B4332;
        border: 1px solid #E2E8E0;
        padding: 14px 20px;
        border-radius: 18px 18px 18px 2px;
        margin: 8px 0;
        max-width: 85%;
        font-size: 0.98rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.02);
    }
</style>
""", unsafe_allow_html=True)

# ==================== DATABASE ENGINE ====================
DB_FILE = "sage_app.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            streak INTEGER DEFAULT 0,
            longest_streak INTEGER DEFAULT 0,
            last_checkin TEXT,
            total_checkins INTEGER DEFAULT 0,
            badges TEXT DEFAULT '[]'
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS chat_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            role TEXT NOT NULL,
            message TEXT NOT NULL,
            explanation TEXT,
            sentiment TEXT,
            sentiment_score REAL,
            emotion TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS mood_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            mood_score INTEGER NOT NULL,
            date TEXT NOT NULL,
            note TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS journal_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT,
            content TEXT NOT NULL,
            prompt_used TEXT,
            is_favorite INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    conn.commit()
    conn.close()

init_db()

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

# ==================== AUTH & USER MANAGEMENT ====================
def hash_pass(password):
    return hashlib.sha256(password.encode()).hexdigest()

def get_or_create_user(username, password=None):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = c.fetchone()
    
    if not user and password:
        pw_hash = hash_pass(password)
        c.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", (username, pw_hash))
        conn.commit()
        c.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = c.fetchone()
    
    conn.close()
    return user

if "user" not in st.session_state:
    guest_user = get_or_create_user("demo_user", "demo123")
    st.session_state.user = dict(guest_user) if guest_user else None

def refresh_user_state():
    if st.session_state.user:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE id = ?", (st.session_state.user['id'],))
        u = c.fetchone()
        conn.close()
        if u:
            st.session_state.user = dict(u)

# ==================== CONSTANTS & HELPLINES ====================
INDIAN_HELPLINES = [
    {"name": "KIRAN (Govt of India)", "number": "1800-599-0019", "timing": "24×7 Toll-Free", "desc": "National Mental Health Rehabilitation Helpline"},
    {"name": "iCall (TISS)", "number": "+91-9152987821", "timing": "Mon–Sat, 8 AM – 10 PM", "desc": "Free telephone & email counselling by TISS professionals"},
    {"name": "Vandrevala Foundation", "number": "1860-2662-345", "timing": "24×7 Toll-Free", "desc": "24/7 Crisis intervention and mental health support"},
    {"name": "AASRA", "number": "+91-9820466726", "timing": "24×7", "desc": "Confidential suicide prevention & emotional distress support"},
    {"name": "NIMHANS Helpline", "number": "080-46110007", "timing": "24×7", "desc": "National Institute of Mental Health Psychosocial Helpline"},
    {"name": "Snehi", "number": "+91-9582208181", "timing": "10 AM – 10 PM", "desc": "Emotional support helpline for youth and families"}
]

JOURNAL_PROMPTS = [
    "What are three small things you felt grateful for today?",
    "How are you feeling right now, without judging your emotions?",
    "What's one challenge you faced today, and how did you handle it?",
    "Describe a moment today that brought a gentle smile to your face.",
    "What is one kind thought you can offer yourself right now?",
    "If you could let go of one worry for the rest of the day, what would it be?",
    "What emotion showed up most today, and where did you feel it in your body?"
]

# ==================== LIGHTWEIGHT SENTIMENT ANALYZER ====================
def analyze_sentiment_fast(text):
    """Fast, zero-dependency rule-based sentiment & emotion analyzer"""
    text_lower = text.lower()
    
    pos_words = ['happy', 'great', 'good', 'excited', 'grateful', 'blessed', 'calm', 'peaceful', 'love', 'joy', 'wonderful']
    neg_words = ['sad', 'depressed', 'anxious', 'scared', 'worried', 'angry', 'terrible', 'bad', 'hurt', 'hopeless', 'stressed']
    
    pos_count = sum(1 for w in pos_words if w in text_lower)
    neg_count = sum(1 for w in neg_words if w in text_lower)
    
    score = (pos_count - neg_count) * 0.3
    score = max(-1.0, min(1.0, score))
    
    emotion = "neutral"
    if any(k in text_lower for k in ["anxious", "anxiety", "nervous", "scared", "worried", "panic"]):
        emotion = "anxiety"
    elif any(k in text_lower for k in ["sad", "depressed", "down", "lonely", "grief", "hopeless"]):
        emotion = "sadness"
    elif any(k in text_lower for k in ["angry", "frustrated", "mad", "annoyed"]):
        emotion = "anger"
    elif any(k in text_lower for k in ["happy", "excited", "grateful", "joy", "good"]):
        emotion = "joy"
    elif any(k in text_lower for k in ["stressed", "overwhelmed", "exhausted", "burnout"]):
        emotion = "stress"

    sentiment = "positive" if score > 0.1 else ("negative" if score < -0.1 else "neutral")
    return {"sentiment": sentiment, "score": round(score, 2), "emotion": emotion}

def check_crisis(text):
    crisis_keywords = ['suicide', 'kill myself', 'want to die', 'end my life', 'self harm', 'hurt myself', 'better off dead']
    text_lower = text.lower()
    for kw in crisis_keywords:
        if kw in text_lower:
            return True
    return False

def generate_sage_response(message, chat_history):
    # 1. Crisis Check
    if check_crisis(message):
        return {
            "response": "🚨 **CRISIS SUPPORT NOTICE** 🚨\n\nYour life and well-being matter deeply. Please connect with immediate professional help:\n\n• **KIRAN Helpline:** 1800-599-0019 (24×7)\n• **iCall (TISS):** +91-9152987821\n• **AASRA:** +91-9820466726\n• **National Emergency:** 112\n\nYou do not have to carry this alone. 💚",
            "explanation": "⚠️ CRISIS TRIGGER DETECTED — Redirected to emergency Indian helplines."
        }
        
    # 2. Check Groq API Key
    groq_key = os.getenv("GROQ_API_KEY", "").strip()
    if "user_groq_key" in st.session_state and st.session_state.user_groq_key:
        groq_key = st.session_state.user_groq_key
        
    if groq_key:
        try:
            from groq import Groq
            client = Groq(api_key=groq_key)
            
            history_messages = []
            for item in chat_history[-6:]:
                # Chat rows use "sage" in the database, but Groq expects
                # assistant messages to use the OpenAI-compatible role name.
                role = "assistant" if item.get("role") == "sage" else item.get("role")
                if role in {"user", "assistant"}:
                    history_messages.append({"role": role, "content": item["message"]})
                
            system_prompt = """You are Sage, an empathetic mental-health and emotional-wellness companion for India.
- Only assist with mental health, emotions, stress, coping skills, mood reflection, journaling, and crisis-support resources.
- If asked about an unrelated topic (including general facts, companies, or programming), do not answer that request. Briefly explain that Sage focuses on mental wellness and invite the user to ask about something in that area.
- For in-scope topics, be supportive and gentle. Validate feelings and offer a practical coping step when useful.
- Keep replies concise (usually 2-4 sentences) and use emojis sparingly.
- Never diagnose or claim to replace a doctor or therapist."""

            available_models = ["qwen/qwen3.8-27b", "openai/gpt-oss-20b", "allam-2-7b"]
            ai_text = None
            used_model = None

            for m_name in available_models:
                try:
                    comp = client.chat.completions.create(
                        model=m_name,
                        messages=[
                            {"role": "system", "content": system_prompt},
                            *history_messages,
                            {"role": "user", "content": message}
                        ],
                        temperature=0.7,
                        max_tokens=250
                    )
                    ai_text = comp.choices[0].message.content.strip()
                    used_model = m_name
                    break
                except Exception:
                    continue

            if ai_text:
                return {
                    "response": ai_text,
                    "explanation": f"🧠 AI Generated via Groq ({used_model}) — Empathetic CBT Companion"
                }
        except Exception:
            pass # Fallback below
            
    # 3. Intelligent Fallback Engine
    msg_lower = message.lower()
    if any(phrase in msg_lower for phrase in [
        "what are you capable of", "what can you do", "what can you help",
        "how can you help", "your capabilities", "what do you do"
    ]):
        return {
            "response": "🌿 I can support mental-wellness check-ins, help you reflect on your mood, suggest simple coping exercises, support journaling, and point you to helplines. I’m an AI companion, not a substitute for professional mental-health care.",
            "explanation": "Capability question → Described Sage's supported features and limits"
        }
    if any(w in msg_lower for w in ['anxious', 'anxiety', 'worried', 'scared', 'panic']):
        return {
            "response": "🌬️ I hear how overwhelming things feel right now. Let's try the **5-4-3-2-1 Grounding Method**:\n\n• 5 things you can SEE 👁️\n• 4 things you can TOUCH ✋\n• 3 things you can HEAR 👂\n• 2 things you can SMELL 👃\n• 1 thing you can TASTE 👅\n\nTake a slow breath. What is one object you notice right now?",
            "explanation": "Anxiety Detected → Guided 5-4-3-2-1 Grounding Technique"
        }
    elif any(w in msg_lower for w in ['sad', 'depressed', 'down', 'lonely']):
        return {
            "response": "💙 Thank you for sharing how you feel. Sadness can feel heavy, and it is okay to give yourself space to rest. Would you be open to writing down one small thing you appreciated today, or taking a short 2-minute walk?",
            "explanation": "Sadness Detected → Behavioral Activation & Validation"
        }
    elif any(w in msg_lower for w in ['stressed', 'overwhelmed', 'exam', 'job', 'work']):
        return {
            "response": "🍃 That sounds like a lot of pressure to hold all at once. Try **Box Breathing**: Inhale for 4 seconds, hold for 4, exhale for 4, hold for 4. What is just one small task you can focus on for the next 15 minutes?",
            "explanation": "Stress Detected → Cognitive De-escalation & Box Breathing"
        }
    else:
        return {
            "response": "🌿 I’m Sage, and I focus on mental health and emotional well-being, so I can’t help with that topic. I can support you with mood check-ins, coping strategies, journaling, or helpline information.",
            "explanation": "Out-of-scope or unrecognized topic → Redirected to Sage's mental-wellness purpose"
        }

# ==================== SIDEBAR & NAVIGATION ====================
with st.sidebar:
    st.image("https://img.icons8.com/color/96/lotus.png", width=60)
    st.title("Sage Companion")
    st.caption("AI Mental Health & Wellness Support")
    
    nav_option = st.radio(
        "Navigate",
        ["💬 AI Chat", "📊 Mood Dashboard", "📔 Personal Journal", "🇮🇳 Helplines Directory", "🏅 Badges & Progress", "⚙️ Settings"],
        index=0
    )
    
    st.divider()
    
    refresh_user_state()
    user_info = st.session_state.user
    if user_info:
        st.markdown(f"**Logged in as:** `{user_info['username']}`")
        col_s1, col_s2 = st.columns(2)
        col_s1.metric("🔥 Streak", f"{user_info['streak']} days")
        col_s2.metric("⭐ Total Logs", f"{user_info['total_checkins']}")
        
    st.divider()
    with st.expander("🔑 Custom Groq API Key"):
        custom_key = st.text_input("Enter Groq API Key (Optional)", type="password", key="groq_input")
        if custom_key:
            st.session_state.user_groq_key = custom_key
            st.success("Custom Groq Key saved for session!")

# ==================== MAIN PAGE ROUTING ====================

# -------------------- 1. AI CHAT PAGE --------------------
if nav_option == "💬 AI Chat":
    st.markdown("""
    <div class="sage-header">
        <h1>🌿 Chat with Sage</h1>
        <p>A safe, non-judgmental space to express your feelings and receive supportive CBT guidance.</p>
    </div>
    """, unsafe_allow_html=True)
    
    user_id = st.session_state.user['id']
    
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM chat_messages WHERE user_id = ? ORDER BY timestamp ASC", (user_id,))
    chat_rows = [dict(r) for r in c.fetchall()]
    conn.close()
    
    for msg in chat_rows:
        if msg['role'] == 'user':
            st.markdown(f"<div class='user-bubble'><strong>You:</strong><br>{msg['message']}</div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div class='sage-bubble'><strong>Sage 🌿:</strong><br>{msg['message']}</div>", unsafe_allow_html=True)
            if msg['explanation']:
                with st.expander("🧠 Why Sage responded this way (Explainable AI)"):
                    st.write(msg['explanation'])
                    if msg.get('sentiment'):
                        st.caption(f"Sentiment Detected: `{msg.get('sentiment')}` (Score: {msg.get('sentiment_score', 0)}) | Emotion: `{msg.get('emotion')}`")

    st.write("---")
    user_input = st.chat_input("Type how you are feeling or what's on your mind...")
    
    if user_input:
        sentiment_res = analyze_sentiment_fast(user_input)
        
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("""
            INSERT INTO chat_messages (user_id, role, message, sentiment, sentiment_score, emotion)
            VALUES (?, 'user', ?, ?, ?, ?)
        """, (user_id, user_input, sentiment_res['sentiment'], sentiment_res['score'], sentiment_res['emotion']))
        conn.commit()
        
        ai_res = generate_sage_response(user_input, chat_rows)
        
        c.execute("""
            INSERT INTO chat_messages (user_id, role, message, explanation)
            VALUES (?, 'sage', ?, ?)
        """, (user_id, ai_res['response'], ai_res['explanation']))
        conn.commit()
        conn.close()
        
        st.rerun()

# -------------------- 2. MOOD DASHBOARD --------------------
elif nav_option == "📊 Mood Dashboard":
    st.markdown("""
    <div class="sage-header">
        <h1>📊 Mood Dashboard & Streak Tracker</h1>
        <p>Log your daily emotional state, build consistency, and view mood trends over time.</p>
    </div>
    """, unsafe_allow_html=True)
    
    user_id = st.session_state.user['id']
    today_str = datetime.now().strftime('%Y-%m-%d')
    
    col1, col2 = st.columns([1, 1.2])
    
    with col1:
        st.subheader("📝 Record Today's Mood")
        
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("SELECT * FROM mood_entries WHERE user_id = ? AND date = ?", (user_id, today_str))
        today_entry = c.fetchone()
        
        if today_entry:
            st.info(f"✅ You have logged your mood for today: **{today_entry['mood_score']}/10**")
            if st.button("🗑️ Reset Today's Mood Entry"):
                c.execute("DELETE FROM mood_entries WHERE user_id = ? AND date = ?", (user_id, today_str))
                conn.commit()
                conn.close()
                st.rerun()
        else:
            mood_score = st.slider("Rate your mood today (1 = Extremely Low, 10 = Outstanding):", 1, 10, 7)
            mood_note = st.text_input("Optional note or reflection (e.g. slept well, exam stress):")
            
            emoji_map = {10: "😍", 9: "🥳", 8: "😊", 7: "🙂", 6: "😌", 5: "😐", 4: "🙁", 3: "😔", 2: "😖", 1: "😭"}
            st.markdown(f"Selected Mood Emoji: **{emoji_map.get(mood_score, '🙂')} ({mood_score}/10)**")
            
            if st.button("💾 Save Mood Check-in", type="primary"):
                c.execute("INSERT INTO mood_entries (user_id, mood_score, date, note) VALUES (?, ?, ?, ?)",
                          (user_id, mood_score, today_str, mood_note))
                
                user_info = st.session_state.user
                last_c = user_info.get('last_checkin')
                yesterday_str = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
                
                new_streak = user_info['streak']
                if last_c == yesterday_str:
                    new_streak += 1
                elif last_c != today_str:
                    new_streak = 1
                    
                longest_streak = max(user_info['longest_streak'], new_streak)
                total_c = user_info['total_checkins'] + 1
                
                badges = json.loads(user_info.get('badges') or '[]')
                if 'First Step' not in badges:
                    badges.append('First Step')
                if new_streak >= 7 and 'Resilience Star' not in badges:
                    badges.append('Resilience Star')
                if new_streak >= 14 and 'Mindful Warrior' not in badges:
                    badges.append('Mindful Warrior')
                if new_streak >= 30 and 'Wellness Champion' not in badges:
                    badges.append('Wellness Champion')
                    
                c.execute("""
                    UPDATE users 
                    SET streak = ?, longest_streak = ?, last_checkin = ?, total_checkins = ?, badges = ?
                    WHERE id = ?
                """, (new_streak, longest_streak, today_str, total_c, json.dumps(badges), user_id))
                
                conn.commit()
                conn.close()
                st.success("🎉 Mood logged successfully! Streak updated.")
                st.rerun()
        conn.close()

    with col2:
        st.subheader("📈 30-Day Mood Trend")
        conn = get_db_connection()
        df_mood = pd.read_sql_query(
            "SELECT date, mood_score FROM mood_entries WHERE user_id = ? ORDER BY date ASC LIMIT 30",
            conn, params=(user_id,)
        )
        conn.close()
        
        if not df_mood.empty:
            df_chart = df_mood.set_index("date")
            st.line_chart(df_chart, y="mood_score", height=280)
        else:
            st.info("No mood entries logged yet. Log your first check-in on the left!")

# -------------------- 3. PERSONAL JOURNAL --------------------
elif nav_option == "📔 Personal Journal":
    st.markdown("""
    <div class="sage-header">
        <h1>📔 Personal Reflective Journal</h1>
        <p>Express your inner thoughts, record daily insights, and explore CBT self-reflection prompts.</p>
    </div>
    """, unsafe_allow_html=True)
    
    user_id = st.session_state.user['id']
    
    col_j1, col_j2 = st.columns([1.2, 1])
    
    with col_j1:
        st.subheader("✍️ Create New Entry")
        
        if st.button("🎲 Generate Random Reflection Prompt"):
            import random
            st.session_state.active_prompt = random.choice(JOURNAL_PROMPTS)
            
        prompt_text = st.session_state.get('active_prompt', '')
        if prompt_text:
            st.info(f"💡 **Prompt:** {prompt_text}")
            
        j_title = st.text_input("Entry Title", placeholder="e.g. Reflection on work today...")
        j_content = st.text_area("Write your thoughts...", height=200, placeholder="Write freely without judgment...")
        
        if st.button("💾 Save Journal Entry", type="primary"):
            if not j_content.strip():
                st.error("Please write some content before saving.")
            else:
                conn = get_db_connection()
                c = conn.cursor()
                c.execute("""
                    INSERT INTO journal_entries (user_id, title, content, prompt_used)
                    VALUES (?, ?, ?, ?)
                """, (user_id, j_title if j_title else "Untitled Entry", j_content, prompt_text))
                conn.commit()
                conn.close()
                st.session_state.active_prompt = ''
                st.success("✨ Journal entry saved securely!")
                st.rerun()

    with col_j2:
        st.subheader("📜 Recent Journal Entries")
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("SELECT * FROM journal_entries WHERE user_id = ? ORDER BY created_at DESC", (user_id,))
        entries = [dict(r) for r in c.fetchall()]
        conn.close()
        
        if not entries:
            st.info("No journal entries created yet. Write your first entry on the left!")
        else:
            for entry in entries:
                with st.expander(f"📖 {entry['title']} ({entry['created_at'][:10]})"):
                    if entry['prompt_used']:
                        st.caption(f"Prompt: {entry['prompt_used']}")
                    st.write(entry['content'])
                    
                    if st.button("🗑️ Delete Entry", key=f"del_{entry['id']}"):
                        conn = get_db_connection()
                        c = conn.cursor()
                        c.execute("DELETE FROM journal_entries WHERE id = ?", (entry['id'],))
                        conn.commit()
                        conn.close()
                        st.success("Deleted!")
                        st.rerun()

# -------------------- 4. HELPLINES DIRECTORY --------------------
elif nav_option == "🇮🇳 Helplines Directory":
    st.markdown("""
    <div class="sage-header">
        <h1>🇮🇳 National Mental Health Helplines</h1>
        <p>Free, confidential, and professional support available 24/7 across India.</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.error("🚨 **National Emergency Number:** Call **112** for immediate medical emergencies or life safety risks.")
    
    cols = st.columns(2)
    for idx, helpline in enumerate(INDIAN_HELPLINES):
        with cols[idx % 2]:
            st.markdown(f"""
            <div class="sage-card">
                <h3 style="color:#1B4332; margin-bottom:6px;">{helpline['name']}</h3>
                <p style="font-size:1.1rem; font-weight:700; color:#2D6A4F; margin-bottom:8px;">📞 {helpline['number']}</p>
                <p style="font-size:0.88rem; color:#4B5563;">⏱️ <strong>Timings:</strong> {helpline['timing']}</p>
                <p style="font-size:0.92rem; color:#374151; margin-top:8px;">{helpline['desc']}</p>
            </div>
            """, unsafe_allow_html=True)

# -------------------- 5. BADGES & PROGRESS --------------------
elif nav_option == "🏅 Badges & Progress":
    st.markdown("""
    <div class="sage-header">
        <h1>🏅 Achievements & Badges</h1>
        <p>Celebrate your commitment to mental wellness and self-care consistency.</p>
    </div>
    """, unsafe_allow_html=True)
    
    user_info = st.session_state.user
    unlocked_badges = json.loads(user_info.get('badges') or '[]')
    
    all_badges = [
        {"name": "First Step", "desc": "Complete your 1st mood check-in", "icon": "👣"},
        {"name": "Resilience Star", "desc": "Maintain a 7-day mood check-in streak", "icon": "⭐"},
        {"name": "Mindful Warrior", "desc": "Maintain a 14-day streak", "icon": "🧘"},
        {"name": "Wellness Champion", "desc": "Maintain a 30-day streak", "icon": "🏆"},
        {"name": "Journal Keeper", "desc": "Save at least 5 journal entries", "icon": "📔"},
        {"name": "Emotion Explorer", "desc": "Engage in 10 chat conversations with Sage", "icon": "🎭"}
    ]
    
    st.subheader("Your Badges Showcase")
    cols_b = st.columns(3)
    for idx, b in enumerate(all_badges):
        is_unlocked = b['name'] in unlocked_badges
        with cols_b[idx % 3]:
            if is_unlocked:
                st.markdown(f"""
                <div class="sage-card" style="border: 2px solid #52B788; background: #F0FDF4;">
                    <h2 style="margin:0;">{b['icon']}</h2>
                    <h4 style="color:#1B4332; margin:6px 0;">{b['name']}</h4>
                    <span class="badge-pill">✅ Unlocked</span>
                    <p style="font-size:0.85rem; color:#4B5563; margin-top:8px;">{b['desc']}</p>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="sage-card" style="opacity:0.6;">
                    <h2 style="margin:0;">🔒</h2>
                    <h4 style="color:#6B7280; margin:6px 0;">{b['name']}</h4>
                    <span class="badge-pill badge-locked">Locked</span>
                    <p style="font-size:0.85rem; color:#9CA3AF; margin-top:8px;">{b['desc']}</p>
                </div>
                """, unsafe_allow_html=True)

# -------------------- 6. SETTINGS & ACCOUNT --------------------
elif nav_option == "⚙️ Settings":
    st.markdown("""
    <div class="sage-header">
        <h1>⚙️ Account Settings</h1>
        <p>Manage your login credentials, data privacy, or switch users.</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.subheader("Account Information")
    st.json({
        "Username": st.session_state.user['username'],
        "Account Created": st.session_state.user['created_at'],
        "Streak": f"{st.session_state.user['streak']} Days",
        "Total Check-ins": st.session_state.user['total_checkins']
    })
    
    st.write("---")
    st.subheader("Switch Account / Login")
    with st.form("login_form"):
        new_user = st.text_input("Username")
        new_pass = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login / Register Account")
        
        if submitted and new_user and new_pass:
            u = get_or_create_user(new_user, new_pass)
            if u:
                st.session_state.user = dict(u)
                st.success(f"Successfully logged in as {new_user}!")
                st.rerun()
