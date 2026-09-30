<div align="center">

<a href="https://git.io/typing-svg">
  <img src="https://readme-typing-svg.demolab.com?font=Fira+Code&weight=600&size=26&pause=1000&color=6B8F71&center=true&vCenter=true&width=600&lines=Sage+%F0%9F%A7%98;AI-Powered+Mental+Health+Companion;Mood+Tracking+%C2%B7+Journaling+%C2%B7+Secure+Auth" alt="Typing SVG" />
</a>

<br/>

<img src="https://img.shields.io/badge/status-active-87A96B?style=flat-square" />
<img src="https://img.shields.io/badge/license-MIT-9CAF88?style=flat-square" />
<img src="https://img.shields.io/badge/made%20with-%E2%9D%A4%EF%B8%8F%20%26%20Python-4A5D45?style=flat-square" />

</div>

<br/>

## 🌿 About Sage

**Sage** is an AI-powered mental health support chatbot built to give people a private, judgment-free space to check in with themselves. It combines conversational AI with structured self-reflection tools — mood tracking and daily journaling — backed by a secure, authenticated backend.

This isn't a toy chatbot wrapper. It's a full-stack application with real auth (Google OAuth + JWT), a persistent database, and a backend built to handle actual user sessions safely.

<br/>

## ✨ Features

| Feature | Description |
|---|---|
| 💬 **AI Chat Support** | Conversational interface for mental health check-ins |
| 📊 **Mood Tracking** | Log and visualize mood patterns over time |
| 📓 **Daily Journaling** | Private journal entries tied to user accounts |
| 🔐 **Google OAuth Login** | Secure sign-in without password management overhead |
| 🎟️ **JWT Authentication** | Stateless, secure session handling across requests |
| 🗄️ **Persistent Storage** | SQLite-backed data layer for users, moods, and journal entries |

<br/>

## 🛠️ Tech Stack

<div align="center">

![Python](https://img.shields.io/badge/Python-4A5D45?style=for-the-badge&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-6B8F71?style=for-the-badge&logo=flask&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-87A96B?style=for-the-badge&logo=sqlite&logoColor=white)
![JWT](https://img.shields.io/badge/JWT-4A5D45?style=for-the-badge&logo=jsonwebtokens&logoColor=white)
![Google OAuth](https://img.shields.io/badge/Google_OAuth-6B8F71?style=for-the-badge&logo=google&logoColor=white)

</div>

<br/>

## 🏗️ Architecture

```
┌─────────────┐      ┌──────────────┐      ┌─────────────┐
│   Client    │─────▶│  Flask API   │─────▶│   SQLite    │
│ (Frontend)  │◀─────│   Backend    │◀─────│  Database   │
└─────────────┘      └──────┬───────┘      └─────────────┘
                             │
                      ┌──────┴───────┐
                      │  Google OAuth │
                      │  + JWT Auth   │
                      └──────────────┘
```

<br/>

## 🚀 Getting Started

### Prerequisites
- Python 3.9+
- pip
- A Google Cloud project with OAuth 2.0 credentials

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
# Fill in your Google OAuth client ID/secret, JWT secret key, etc.

# Run the app
python app.py
```

The app will be available at `http://localhost:5000`.

<br/>

## 🔑 Environment Variables

Create a `.env` file in the root directory with the following:

```env
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
JWT_SECRET_KEY=your_jwt_secret
FLASK_SECRET_KEY=your_flask_secret
DATABASE_URL=sqlite:///sage.db
```

> ⚠️ Never commit your `.env` file. It's already included in `.gitignore` — keep it that way.

<br/>

## 📁 Project Structure

```
Sage/
├── app.py                 # Application entry point
├── config.py               # Configuration & environment loading
├── models/                  # Database models
├── routes/                  # API routes (auth, mood, journal, chat)
├── auth/                    # OAuth + JWT logic
├── templates/                # Frontend templates
├── static/                   # CSS/JS assets
├── requirements.txt
└── .env.example
```

<br/>

## 🗺️ Roadmap

- [ ] Add mood analytics dashboard with trend visualization
- [ ] Expand chatbot with context-aware conversation memory
- [ ] Add reminders/notifications for journaling streaks
- [ ] Deploy to a live hosted environment

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
