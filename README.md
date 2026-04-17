# 🎓 UpSkill AI — Career Development Platform

> An AI-powered platform for resume analysis, mock interviews, skill gap analysis, and career coaching.

[![Status](https://img.shields.io/badge/Status-Production%20Ready-success)]()
[![Tests](https://img.shields.io/badge/Tests-Passing-success)]()
[![Security](https://img.shields.io/badge/Security-Hardened-success)]()
[![Python](https://img.shields.io/badge/Python-3.9+-blue)]()
[![Flask](https://img.shields.io/badge/Flask-2.3.3-lightgrey)]()

---

## 📋 Table of Contents

- [Quick Start](#-quick-start)
- [Features](#-features)
- [Architecture](#-architecture)
- [API Documentation](#-api-documentation)
- [Email System Setup](#-email-system-setup)
- [Security](#-security)
- [Testing](#-testing)
- [Deployment](#-deployment)
- [Troubleshooting](#-troubleshooting)

---

## ⚡ Quick Start

Get up and running in under 5 minutes:

```bash
# 1. Clone and navigate to the project
cd "UpSkill AI-Skill Assistant"

# 2. Set up the backend
cd backend
cp .env.example .env
# Edit .env with your API keys (see Environment Variables section)

# 3. Install dependencies and start the backend
pip install -r requirements.txt
python run.py

# 4. Start the frontend (new terminal)
cd ../frontend
python server.py

# 5. Open in browser
# http://localhost:8000
```

---

## 🎯 Features

### ✅ Resume Analysis
- **ATS Scoring** — AI-powered resume scoring against job descriptions
- **Skill Detection** — Automatically extract and categorize your skills
- **Gap Analysis** — Identify missing skills for your target role
- **AI Suggestions** — Get personalized, actionable improvement tips

### ✅ Mock Interviews
- **AI Interviewer** — Practice with an intelligent conversational AI
- **Real-time Feedback** — Instant evaluation after every answer
- **Multiple Roles** — Software Engineering, Product, Design, and more
- **Proctoring** — Optional camera monitoring for exam integrity
- **Performance Tracking** — Monitor improvement over time

### ✅ Skill Gap Analysis
- **Readiness Score** — Know exactly how prepared you are
- **Learning Path** — Receive a personalized, prioritized roadmap
- **Priority Skills** — Focus only on what matters most
- **Resource Recommendations** — Curated learning materials per skill

### ✅ Career Coach
- **AI Chat** — Ask career questions anytime, 24/7
- **Context-Aware** — Remembers your profile and past sessions
- **Expert Advice** — Salary negotiation, interview prep, career pivots

### ✅ Analytics Dashboard
- **Performance Trends** — Visual charts of your progress
- **Insights** — Understand your strengths and weaknesses
- **Achievements** — Celebrate milestones
- **History** — Review all past activities

### ✅ Email Notifications
- **Welcome Email** — Sent on successful registration
- **Login Alerts** — Security notification on each login
- **Non-blocking Delivery** — Emails sent in background threads; API stays fast

---

## 🏗️ Architecture

### Backend (Flask)
```
backend/
├── app/
│   ├── routes/           # API endpoints (auth, AI, interview)
│   ├── services/         # Business logic & AI integrations
│   ├── hardening.py      # Rate limiting & security middleware
│   ├── error_handlers.py # Centralized error handling
│   ├── database.py       # Database setup & management
│   └── validators.py     # Request validation
├── logs/                 # Application logs
├── requirements.txt      # Python dependencies
├── run.py                # App entry point
└── setup.py              # Database initialization
```

### Frontend (Vanilla JS)
```
frontend/
├── js/
│   ├── api-v2.js           # Production API client
│   ├── network-monitor.js  # Offline/online state detection
│   ├── api-utils.js        # Shared utility functions
│   ├── interview.js        # Mock interview logic
│   └── skill-gap.js        # Skill gap analysis logic
├── css/
│   └── styles.css          # Global design system
└── *.html                  # Application pages
```

### Tech Stack

| Layer | Technology |
|---|---|
| Backend Framework | Flask 2.3.3 |
| Authentication | Flask-JWT-Extended |
| AI / LLM | Groq AI (Llama 3) |
| Database | SQLite |
| PDF Parsing | PyPDF2 |
| Frontend | Vanilla JS (ES6+), HTML5, CSS3 |
| CORS | Flask-CORS |

---

## 📊 API Documentation

### Base URL
- **Development:** `http://localhost:5000`

### Authentication
```http
POST /api/auth/register    # Register a new user
POST /api/auth/login       # Login and receive JWT
GET  /api/auth/me          # Get current user profile
```

### Resume
```http
POST /api/ai/resume/upload           # Upload and analyze a resume
GET  /api/ai/resume/history          # Get past resume analyses
POST /api/ai/resume/ats-optimization # ATS optimization suggestions
```

### Interview
```http
POST /api/interview/start    # Start a new mock interview session
POST /api/interview/answer   # Submit an answer
POST /api/interview/end      # End the session and get feedback
GET  /api/interview/history  # Get past interview sessions
```

### Skills
```http
POST /api/ai/skills/analyze-gaps      # Identify skill gaps for a role
POST /api/ai/skills/learning-path     # Generate a learning roadmap
POST /api/ai/skills/assess-readiness  # Get a readiness score
```

### Career Coach
```http
POST /api/ai/chat/message   # Send a message to the AI coach
POST /api/ai/chat/clear     # Clear the current chat session
```

### Standard Response Format
```json
{
  "success": true,
  "data": { "..." },
  "error": null
}
```

---

## 📧 Email System Setup

The email system sends welcome and login-alert emails in background threads, so API response times are never affected.

### 1. Configure Environment Variables

In `backend/.env`, add the following:

```env
# Email System
EMAIL_ENABLED=true
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USER=your-email@gmail.com
EMAIL_PASS=your-app-password       # Use Gmail App Password, NOT your account password
EMAIL_FROM_NAME=UpSkill AI
```

> **Gmail Users:** Go to [Google Account → Security → 2-Step Verification → App passwords](https://myaccount.google.com/apppasswords) and generate an app password for "Mail".

### 2. Disable Email (Optional)

To run the app without email (e.g., during local development):

```env
EMAIL_ENABLED=false
```

All features work normally — emails are simply skipped and logged.

### 3. How It Works

```
User registers / logs in
        │
        ▼
API processes request instantly (~100ms)
        │
        ├── Returns response to user ✅
        │
        └── Background thread sends email (~2–5s) 📧
```

Email never blocks the API. If sending fails, the error is logged and the app continues normally.

---

## 🔒 Security

### Backend
- ✅ **Rate Limiting** — Prevent brute-force and abuse
- ✅ **JWT Authentication** — Stateless, secure token-based auth
- ✅ **Input Validation** — All inputs sanitized before processing
- ✅ **CORS Configuration** — Restricted to allowed origins
- ✅ **Security Headers** — XSS, clickjacking, MIME-sniffing protection
- ✅ **Error Sanitization** — Sensitive details never leak to clients
- ✅ **Structured Logging** — All activity tracked in `logs/`

### Frontend
- ✅ **Secure Token Storage** — JWT stored and managed safely
- ✅ **Auto Logout** — Triggered automatically on token expiry
- ✅ **Network Monitoring** — Detects and handles offline state
- ✅ **Client-side Validation** — Immediate feedback before API calls

---

## 🧪 Testing

### Run Automated Tests
```bash
cd backend
python test_integration.py
```

### Test Coverage

| Area | Status |
|---|---|
| Health Check | ✅ Passing |
| User Registration | ✅ Passing |
| User Login | ✅ Passing |
| JWT Authentication | ✅ Passing |
| Dashboard | ✅ Passing |
| Resume API | ✅ Passing |
| Interview API | ✅ Passing |
| Career Coach | ✅ Passing |
| Error Handling | ✅ Passing |
| Rate Limiting | ✅ Passing |
| CORS | ✅ Passing |

---

## 🚀 Deployment

### Development
```bash
# Terminal 1 — Backend
cd backend
python run.py

# Terminal 2 — Frontend
cd frontend
python server.py
```

### Production (Gunicorn + Nginx)
```bash
# Install Gunicorn
pip install gunicorn

# Run backend with 4 workers
gunicorn -w 4 -b 0.0.0.0:5000 "app:create_app()"

# Configure Nginx as a reverse proxy to port 5000
# Serve the frontend/ folder as static files
```

### Environment Variables Reference

| Variable | Required | Description |
|---|---|---|
| `GROQ_API_KEY` | ✅ Yes | Groq AI API key for LLM features |
| `JWT_SECRET_KEY` | ✅ Yes | Secret key for JWT signing |
| `EMAIL_ENABLED` | No | `true` / `false` (default: `false`) |
| `EMAIL_HOST` | No | SMTP host (e.g., `smtp.gmail.com`) |
| `EMAIL_PORT` | No | SMTP port (e.g., `587`) |
| `EMAIL_USER` | No | SMTP username / email address |
| `EMAIL_PASS` | No | SMTP password / app password |
| `EMAIL_FROM_NAME` | No | Sender display name |

---

## 🛠️ Troubleshooting

### Backend won't start
```bash
# Verify your .env file has required keys
cat backend/.env

# Check if port 5000 is already in use
netstat -ano | findstr :5000   # Windows
lsof -i :5000                  # macOS/Linux
```

### Frontend can't connect to backend
```bash
# Confirm backend is running and healthy
curl http://localhost:5000/health

# Check CORS settings in backend/app/__init__.py
```

### Tests failing
- Ensure the backend server is running before executing tests
- Verify all required environment variables are set in `.env`
- Check `backend/logs/error.log` for detailed error messages

### Emails not sending
- Confirm `EMAIL_ENABLED=true` in `.env`
- Use a Gmail **App Password**, not your regular account password
- Check `backend/logs/` for SMTP error messages
- Test with `EMAIL_ENABLED=false` first to rule out non-email issues

---

## 📈 Performance

| Metric | Target |
|---|---|
| Page Load Time | < 2 seconds |
| API Response Time | < 500ms average |
| Max File Upload | 5 MB |
| Concurrent Users | 100+ |
| Email Delivery | 2–5 seconds (background) |

---

## 📝 License

Proprietary — All rights reserved.

---

## 🎉 Acknowledgments

Built with:
- [Flask](https://flask.palletsprojects.com/) — Backend web framework
- [Groq AI](https://groq.com/) — Ultra-fast LLM inference
- [Flask-JWT-Extended](https://flask-jwt-extended.readthedocs.io/) — JWT authentication

---

**Version:** 1.0.0 &nbsp;|&nbsp; **Status:** Production Ready ✅ &nbsp;|&nbsp; **Updated:** April 2026
