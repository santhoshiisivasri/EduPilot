# 🚀 EduPilot – AI-Powered Personalized Learning Platform

> **IBM Hackathon Project** · Powered by IBM Watsonx.ai Granite Models

EduPilot is a full-stack AI-powered learning platform that acts as a personal career mentor for tech students. It generates personalized learning roadmaps, adapts to your progress, and provides intelligent career guidance — all powered by **IBM Watsonx.ai** using **IBM Granite** language models.

---

## ✨ Features

| Feature | Description |
|---|---|
| 🤖 **AI Chat Coach (Aria)** | 24/7 IBM Granite-powered personal learning mentor |
| 🗺️ **Personalized Roadmaps** | Beginner → Intermediate → Advanced AI-generated paths |
| 🎯 **Skill Assessment** | AI-evaluated domain quizzes with gap analysis |
| 📊 **Learning Analytics** | Charts tracking study activity, scores, and progress |
| 📅 **Weekly Study Planner** | AI-generated personalized daily study schedules |
| 💼 **Career Guidance** | Domain matching, salary info, job role recommendations |
| 🏆 **Achievement Badges** | Gamified milestone system with badge rewards |
| 🌙 **Dark Mode** | Full glassmorphism UI with light/dark themes |
| 🔒 **Admin Dashboard** | Platform analytics, user management, AI logs |

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **Backend** | Python 3.11, Flask 3.x |
| **AI Engine** | IBM Watsonx.ai – `ibm-granite/granite-3-3-8b-instruct` |
| **Database** | SQLite (dev) / PostgreSQL (prod) via SQLAlchemy |
| **Auth** | Flask-Login + Bcrypt |
| **Frontend** | Bootstrap 5, Chart.js, Bootstrap Icons |
| **Styling** | Custom CSS – Glassmorphism + Gradient themes |

---

## 🚀 Quick Start

### 1. Clone & Setup

```bash
cd EduPilot
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate

pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy the example env file
copy .env.example .env    # Windows
cp .env.example .env      # macOS/Linux
```

Edit `.env` with your credentials:
```env
SECRET_KEY=your-super-secret-key
IBM_API_KEY=your-ibm-cloud-api-key
IBM_PROJECT_ID=your-watsonx-project-id
IBM_REGION=us-south
WATSONX_MODEL_ID=ibm-granite/granite-3-3-8b-instruct
```

### 3. Run the App

```bash
python run.py
```

Visit **http://localhost:5000** 🎉

---

## 🔑 IBM Watsonx.ai Setup

1. Create an [IBM Cloud account](https://cloud.ibm.com)
2. Navigate to **Watsonx.ai** and create a project
3. Generate an **API Key** from IAM
4. Copy your **Project ID** from the Watsonx dashboard
5. Add both to your `.env` file

**Supported Models:**
- `ibm-granite/granite-3-3-8b-instruct` *(default)*
- `ibm-granite/granite-3-8b-instruct`
- `ibm-granite/granite-13b-chat-v2`

---

## 📁 Project Structure

```
EduPilot/
├── app/
│   ├── __init__.py              # Flask factory
│   ├── agent_instructions.py   # 🎛️ AI AGENT CONFIGURATION
│   ├── watsonx_client.py        # IBM Watsonx.ai integration
│   ├── models.py                # SQLAlchemy DB models
│   ├── config.py                # App configuration
│   ├── extensions.py            # Flask extensions
│   ├── routes/                  # Blueprint route files
│   ├── templates/               # Jinja2 HTML templates
│   └── static/                  # CSS, JS, images
├── .env                         # Environment variables
├── .env.example                 # Template
├── requirements.txt
├── run.py
└── README.md
```

---

## 🎛️ Customizing the AI Coach

All AI behavior is controlled through `app/agent_instructions.py`:

```python
# Change the AI coach name/persona
AGENT_PERSONA = {
    "name": "Aria",            # Change coach name
    "personality": "warm, encouraging, professional",
    "emoji_usage": True,       # Toggle emojis
}

# Add new career domains
CAREER_DOMAINS.append({
    "id": "quantum",
    "name": "Quantum Computing",
    "key_skills": ["Qiskit", "IBM Quantum", "Linear Algebra"],
    ...
})

# Modify safety rules
SAFETY_RULES.append("Always recommend IBM certifications when relevant")

# Adjust roadmap generation
ROADMAP_STRATEGY["milestones_per_level"] = 4  # Default: 3
```

---

## 🔐 Default Credentials

| Role | Email | Password |
|---|---|---|
| Admin | `admin@edupilot.ai` | `Admin@123!` |

---

## 🌐 Deployment

### Render (Recommended)

1. Connect your GitHub repo to [Render](https://render.com)
2. Set environment variables in Render dashboard
3. Build command: `pip install -r requirements.txt`
4. Start command: `gunicorn run:app`

### Railway

```bash
railway init
railway add
railway deploy
```

### Docker

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["gunicorn", "run:app", "--bind", "0.0.0.0:5000"]
```

---

## 📜 License

MIT License · Built for IBM Hackathon 2024

---

## 🙏 Acknowledgments

- **IBM Watsonx.ai** – Powering the AI intelligence engine
- **IBM Granite** – The foundation model for personalized guidance
- **Flask** – The lightweight Python web framework
- **Bootstrap 5** – Beautiful responsive UI components
