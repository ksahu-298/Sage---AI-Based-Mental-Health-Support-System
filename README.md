<div align="center">

<a href="https://git.io/typing-svg">
  <img src="https://readme-typing-svg.demolab.com?font=Fira+Code&weight=600&size=26&pause=1000&color=6B8F71&center=true&vCenter=true&width=600&lines=Sage+%F0%9F%A7%98;AI+Mental+Health+%26+Wellness+Companion;Mood+Tracking+%C2%B7+Journaling+%C2%B7+AI+Chat" alt="Typing SVG" />
</a>

<br/>

<img src="https://img.shields.io/badge/status-active-87A96B?style=flat-square" />
<img src="https://img.shields.io/badge/license-MIT-9CAF88?style=flat-square" />
<img src="https://img.shields.io/badge/made%20with-%E2%9D%A4%EF%B8%8F%20%26%20Python-4A5D45?style=flat-square" />

</div>

<br/>

**Live demo:** [sage-mentalhealthassistant.streamlit.app](https://sage-mentalhealthassistant.streamlit.app/)

<br/>

## 🌿 About Sage

**Sage** is an AI-powered mental health and wellness companion built as an interactive Streamlit app. It gives people a private space to check in on how they're feeling, track their mood over time, journal, and chat with an empathetic AI companion — with built-in crisis detection that redirects to real Indian helplines when needed.

<br/>

## ✨ Features

| Feature | Description |
|---|---|
| 💬 **AI Chat Companion** | Empathetic, CBT-style conversations powered by Groq, scoped strictly to mental wellness topics |
| 🧠 **Explainable Responses** | Each AI reply can be expanded to show the detected sentiment/emotion and why Sage responded that way |
| 🚨 **Crisis Detection** | Messages are screened for crisis language and immediately redirected to national helplines and the emergency number |
| 📊 **Mood Dashboard** | Daily mood check-ins (1–10 scale) with notes, visualized as a 30-day trend chart |
| 🔥 **Streaks & Badges** | Tracks check-in streaks and unlocks badges (First Step, Resilience Star, Mindful Warrior, Wellness Champion, and more) |
| 📔 **Personal Journal** | Free-form journaling with optional CBT-style reflection prompts, saved per user |
| 🇮🇳 **Helplines Directory** | A directory of national mental health helplines (KIRAN, iCall, Vandrevala Foundation, AASRA, NIMHANS, Snehi) |
| 🔐 **Simple Account System** | Username/password accounts (SHA-256 hashed) backed by SQLite |

<br/>

## 🛠️ Tech Stack

<div align="center">

![Python](https://img.shields.io/badge/Python-4A5D45?style=for-the-badge&logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-6B8F71?style=for-the-badge&logo=streamlit&logoColor=white)
![Groq](https://img.shields.io/badge/Groq-87A96B?style=for-the-badge)
![SQLite](https://img.shields.io/badge/SQLite-4A5D45?style=for-the-badge&logo=sqlite&logoColor=white)
![Pandas](https://img.shields.io/badge/Pandas-6B8F71?style=for-the-badge&logo=pandas&logoColor=white)

</div>

<br/>

## 🏗️ How It Works

```
┌─────────────┐      ┌──────────────────┐      ┌─────────────┐
│  Streamlit  │─────▶│  App logic in    │─────▶│   SQLite    │
│   Frontend  │◀─────│  app_streamlit.py│◀─────│  Database   │
└─────────────┘      └────────┬─────────┘      └─────────────┘
                               │
                   ┌───────────┴────────────┐
                   │  Groq LLM (chat +      │
                   │  rule-based sentiment/  │
                   │  crisis-keyword checks) │
                   └────────────────────────┘
```

- **Chat:** every message is first checked for crisis keywords. If none are found, it's sent to Groq (with a system prompt that keeps Sage scoped to mental-wellness topics) using a fallback list of models (`qwen/qwen3.8-27b`, `openai/gpt-oss-20b`, `allam-2-7b`). If no Groq key is available or all models fail, a rule-based fallback responds based on detected keywords (anxiety, sadness, stress, etc.).
- **Sentiment:** a lightweight, zero-dependency keyword-based analyzer tags each user message with a sentiment, score and emotion, shown in an "explainable AI" expander under each reply.
- **Data:** users, chat history, mood entries and journal entries are all stored in a local SQLite database (`sage_app.db`), created automatically on first run.

<br/>

## 🚀 Getting Started

### Prerequisites
- Python 3.9+
- pip
- A Groq API key (optional — the app works with a rule-based fallback if omitted)

### Installation

```bash
# Clone the repository
git clone https://github.com/ksahu-298/Sage---AI-Based-Mental-Health-Support-System.git
cd Sage---AI-Based-Mental-Health-Support-System

# Create a virtual environment
python -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Add your GROQ_API_KEY

# Run the app
streamlit run app_streamlit.py
```

The app will open at `http://localhost:8501`.

> You can also paste a Groq API key directly into the sidebar ("Custom Groq API Key") for a single session, without setting up `.env`.

<br/>

## 🔑 Environment Variables

Create a `.env` file in the root directory:

```env
GROQ_API_KEY=your_groq_api_key
```

> ⚠️ Never commit your `.env` file or `sage_app.db` — both are already covered by `.gitignore`. If a key is ever exposed, rotate it immediately.

<br/>

## 📁 Project Structure

```
Sage/
├── app_streamlit.py     # Main Streamlit application (UI, routing, DB, chat logic)
├── sage_app.db           # SQLite database (auto-created, gitignored)
├── requirements.txt
├── .env.example
└── .gitignore
```

<br/>

## 🗺️ Roadmap

- [ ] Move sentiment/emotion detection from keyword-based to a proper NLP model
- [ ] Add stronger authentication (password policy, hashed session tokens)
- [ ] Add data export for a user's own mood and journal history
- [ ] Expand badge system and add reminders for check-in streaks

<br/>

## ⚠️ A Note on Scope

Sage is a wellness companion, not a replacement for professional care. It includes crisis-keyword detection that surfaces national helplines, but it is not a clinical or emergency service. In an active emergency, contact local emergency services directly.

<br/>

## 🤝 Contributing

Contributions, issues, and feature requests are welcome. Feel free to check the [issues page](../../issues) or open a pull request.

<br/>

## 📄 License

This project is licensed under the MIT License.

<br/>

<div align="center">
<i>Built with care, one commit at a time. 🌱</i>
</div>
