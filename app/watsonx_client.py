"""
EduPilot – IBM Watsonx.ai Granite Client
Handles all communication with the IBM Watsonx.ai API.
"""
import os
import json
import logging
from flask import current_app

logger = logging.getLogger(__name__)

# IBM Watsonx.ai SDK
try:
    from ibm_watsonx_ai import APIClient, Credentials
    from ibm_watsonx_ai.foundation_models import ModelInference
    from ibm_watsonx_ai.metanames import GenTextParamsMetaNames as GenParams
    WATSONX_AVAILABLE = True
except ImportError:
    WATSONX_AVAILABLE = False
    logger.warning("ibm-watsonx-ai not installed. Using mock responses.")


class WatsonxClient:
    """Client wrapper for IBM Watsonx.ai Granite models."""

    def __init__(self, api_key: str, project_id: str, region: str = "us-south"):
        self.api_key = api_key
        self.project_id = project_id
        self.region = region
        self.model = None
        self._initialized = False

        if api_key and project_id and api_key != 'your-ibm-cloud-api-key-here':
            self._initialize()

    def _initialize(self):
        """Initialize the IBM Watsonx.ai client."""
        if not WATSONX_AVAILABLE:
            print("[EduPilot] ibm-watsonx-ai SDK not installed. Using mock AI responses.")
            return

        try:
            url = f"https://{self.region}.ml.cloud.ibm.com"
            model_id = os.environ.get('WATSONX_MODEL_ID', 'ibm/granite-4-h-small')

            print(f"[EduPilot] Connecting to IBM Watsonx.ai...")
            print(f"[EduPilot]   URL       : {url}")
            print(f"[EduPilot]   Model     : {model_id}")
            print(f"[EduPilot]   Project   : {self.project_id[:12]}...")

            credentials = Credentials(
                url=url,
                api_key=self.api_key
            )

            self.model = ModelInference(
                model_id=model_id,
                credentials=credentials,
                project_id=self.project_id,
                params={
                    "max_tokens": int(os.environ.get('MAX_TOKENS', 1024)),
                    "temperature": float(os.environ.get('TEMPERATURE', 0.7)),
                    "top_p": 0.9,
                }
            )
            self._initialized = True
            print(f"[EduPilot] IBM Watsonx.ai CONNECTED! Model: {model_id}")

        except Exception as e:
            print(f"[EduPilot] IBM Watsonx.ai FAILED: {e}")
            logger.error(f"Failed to initialize Watsonx.ai client: {e}")
            self._initialized = False


    def chat(self, messages: list, system_prompt: str = "") -> str:
        """
        Send a chat conversation to IBM Watsonx.ai Granite.

        Args:
            messages: List of {'role': 'user'/'assistant', 'content': str}
            system_prompt: System instructions for the model

        Returns:
            str: AI-generated response text
        """
        if not self._initialized or not self.model:
            return self._mock_response(messages)

        try:
            # Build messages with system prompt
            formatted_messages = []
            if system_prompt:
                formatted_messages.append({
                    "role": "system",
                    "content": system_prompt
                })
            formatted_messages.extend(messages)

            response = self.model.chat(messages=formatted_messages)

            # Extract text from response
            if response and 'choices' in response:
                return response['choices'][0]['message']['content']
            elif response and 'results' in response:
                return response['results'][0].get('generated_text', '')
            else:
                logger.warning(f"Unexpected response structure: {response}")
                return self._mock_response(messages)

        except Exception as e:
            logger.error(f"Watsonx.ai chat error: {e}")
            return self._fallback_response(str(e))

    def generate_roadmap(self, profile_data: dict, domain: str, system_prompt: str) -> dict:
        """
        Generate a structured learning roadmap using IBM Granite.

        Args:
            profile_data: Student profile information
            domain: Target career domain
            system_prompt: Agent system instructions

        Returns:
            dict: Structured roadmap with milestones
        """
        prompt = f"""Generate a comprehensive, personalized learning roadmap for a student with the following profile:

Student Profile:
- Education: {profile_data.get('education', 'Not specified')}
- Career Goal: {profile_data.get('career_goal', domain)}
- Current Skills: {', '.join(profile_data.get('skills', [])) or 'Beginner (no prior skills)'}
- Experience Level: {profile_data.get('experience_level', 'beginner')}
- Study Hours/Week: {profile_data.get('study_hours', 10)} hours
- Learning Style: {profile_data.get('learning_style', 'mixed')}

Target Domain: {domain}

Generate a roadmap with exactly 3 levels (beginner, intermediate, advanced).
Each level must have exactly 3 milestones.
Each milestone must include:
- title: Clear, specific milestone name
- description: What will be learned and accomplished
- duration_weeks: Realistic duration (1-4 weeks)
- resources: List of 4 specific courses/tutorials with provider names
- projects: List of 2 hands-on project ideas
- certifications: List of 1-2 relevant certifications

IMPORTANT: Return ONLY valid JSON in this exact format:
{{
  "domain": "{domain}",
  "title": "Complete {domain} Roadmap",
  "estimated_months": <number>,
  "levels": {{
    "beginner": [
      {{
        "order": 1,
        "title": "milestone title",
        "description": "what you'll learn",
        "duration_weeks": 2,
        "resources": ["Resource 1 (Provider)", "Resource 2 (Provider)", "Resource 3 (Provider)", "Resource 4 (Provider)"],
        "projects": ["Project 1 description", "Project 2 description"],
        "certifications": ["Certification Name"]
      }}
    ],
    "intermediate": [...],
    "advanced": [...]
  }}
}}"""

        if not self._initialized or not self.model:
            return self._mock_roadmap(domain)

        try:
            messages = [{"role": "user", "content": prompt}]
            response_text = self.chat(messages, system_prompt)

            # Parse JSON from response
            start = response_text.find('{')
            end = response_text.rfind('}') + 1
            if start != -1 and end > start:
                json_str = response_text[start:end]
                return json.loads(json_str)
            else:
                return self._mock_roadmap(domain)

        except (json.JSONDecodeError, Exception) as e:
            logger.error(f"Roadmap generation error: {e}")
            return self._mock_roadmap(domain)

    def generate_weekly_plan(self, profile_data: dict, current_milestone: str,
                              study_hours: int, system_prompt: str) -> dict:
        """Generate a personalized weekly study plan."""
        prompt = f"""Create a detailed weekly study plan for:
- Current Milestone: {current_milestone}
- Available Study Hours: {study_hours} hours/week
- Learning Style: {profile_data.get('learning_style', 'mixed')}

Return ONLY valid JSON:
{{
  "week_theme": "theme of the week",
  "total_hours": {study_hours},
  "days": {{
    "Monday": {{"tasks": ["task1", "task2"], "hours": 1.5, "focus": "topic"}},
    "Tuesday": {{"tasks": ["task1", "task2"], "hours": 1.5, "focus": "topic"}},
    "Wednesday": {{"tasks": ["task1", "task2"], "hours": 1.5, "focus": "topic"}},
    "Thursday": {{"tasks": ["task1", "task2"], "hours": 1.5, "focus": "topic"}},
    "Friday": {{"tasks": ["task1", "task2"], "hours": 1.5, "focus": "topic"}},
    "Saturday": {{"tasks": ["task1"], "hours": 1.0, "focus": "project work"}},
    "Sunday": {{"tasks": ["review"], "hours": 0.5, "focus": "revision & rest"}}
  }},
  "goals": ["Weekly goal 1", "Weekly goal 2", "Weekly goal 3"],
  "motivation": "An encouraging message for the week"
}}"""

        if not self._initialized or not self.model:
            return self._mock_weekly_plan(study_hours)

        try:
            messages = [{"role": "user", "content": prompt}]
            response_text = self.chat(messages, system_prompt)
            start = response_text.find('{')
            end = response_text.rfind('}') + 1
            if start != -1 and end > start:
                return json.loads(response_text[start:end])
            return self._mock_weekly_plan(study_hours)
        except Exception as e:
            logger.error(f"Weekly plan generation error: {e}")
            return self._mock_weekly_plan(study_hours)

    def evaluate_assessment(self, domain: str, questions: list, answers: dict,
                             system_prompt: str) -> dict:
        """AI-evaluate a skill assessment and provide feedback."""
        qa_text = "\n".join(
            f"Q{i+1}: {q['question']}\nStudent Answer: {answers.get(str(i), 'No answer')}\n"
            for i, q in enumerate(questions)
        )

        prompt = f"""Evaluate this {domain} skill assessment:

{qa_text}

Return ONLY valid JSON:
{{
  "score": <0-100>,
  "grade": "Excellent/Good/Average/Needs Improvement",
  "strengths": ["strength1", "strength2"],
  "gaps": ["gap1", "gap2"],
  "recommendations": ["specific recommendation 1", "specific recommendation 2", "specific recommendation 3"],
  "next_steps": "What the student should focus on next",
  "feedback": "Overall encouraging feedback message (2-3 sentences)"
}}"""

        if not self._initialized or not self.model:
            return {"score": 65, "grade": "Good", "strengths": ["Problem solving"],
                    "gaps": ["Advanced concepts"], "recommendations": ["Practice more projects"],
                    "next_steps": "Continue with intermediate topics",
                    "feedback": "Great effort! Keep learning consistently."}

        try:
            messages = [{"role": "user", "content": prompt}]
            response_text = self.chat(messages, system_prompt)
            start = response_text.find('{')
            end = response_text.rfind('}') + 1
            if start != -1 and end > start:
                return json.loads(response_text[start:end])
        except Exception as e:
            logger.error(f"Assessment evaluation error: {e}")

        return {"score": 60, "grade": "Good", "strengths": [], "gaps": [],
                "recommendations": ["Continue studying"], "next_steps": "Keep going!",
                "feedback": "You're making great progress!"}

    # ─── Mock Responses (used when API is not configured) ──────────────
    def _mock_response(self, messages: list) -> str:
        """Return a helpful mock response when API is not configured."""
        last_msg = messages[-1]['content'].lower() if messages else ""

        if any(w in last_msg for w in ['hello', 'hi', 'start', 'begin']):
            return ("👋 Hello! I'm **Aria**, your EduPilot AI Learning Coach!\n\n"
                    "I'm powered by IBM Watsonx.ai (Granite), but it looks like the API key "
                    "hasn't been configured yet.\n\n"
                    "To enable full AI capabilities:\n"
                    "1. Get your IBM Cloud API Key from [cloud.ibm.com](https://cloud.ibm.com)\n"
                    "2. Get your Watsonx Project ID from [watsonx.ai](https://watsonx.ai)\n"
                    "3. Add them to your `.env` file\n\n"
                    "Once configured, I can create personalized learning roadmaps, "
                    "weekly study plans, skill assessments, and career guidance just for you! 🚀")

        return ("I'm **Aria**, your EduPilot AI Coach! 🎓\n\n"
                "**Note:** The IBM Watsonx.ai API is not yet configured. "
                "Please add your `IBM_API_KEY` and `IBM_PROJECT_ID` to the `.env` file "
                "to unlock full AI-powered personalized learning guidance.\n\n"
                "In the meantime, explore your dashboard, complete your profile, "
                "and check out the course roadmaps! 💪")

    def _fallback_response(self, error: str) -> str:
        return ("I encountered a temporary issue connecting to IBM Watsonx.ai. 🔧\n\n"
                "Please try again in a moment. If the issue persists, check your "
                "API credentials in the `.env` file.\n\n"
                f"*Technical detail: {error[:100]}*")

    def _mock_roadmap(self, domain: str) -> dict:
        """Generate a structured mock roadmap for demo purposes."""
        return {
            "domain": domain,
            "title": f"Complete {domain} Roadmap",
            "estimated_months": 9,
            "levels": {
                "beginner": [
                    {
                        "order": 1,
                        "title": f"{domain} Fundamentals",
                        "description": f"Build a solid foundation in {domain} core concepts and tools.",
                        "duration_weeks": 3,
                        "resources": [
                            f"{domain} for Beginners (freeCodeCamp - YouTube)",
                            f"Introduction to {domain} (Coursera - Google)",
                            f"{domain} Crash Course (Codecademy)",
                            f"{domain} Full Course (Udemy - 100 Days)"
                        ],
                        "projects": [
                            f"Build your first {domain} project",
                            f"Complete 5 {domain} exercises on HackerRank"
                        ],
                        "certifications": [f"Google {domain} Foundations Certificate"]
                    },
                    {
                        "order": 2,
                        "title": "Core Concepts Deep Dive",
                        "description": "Master the essential building blocks and best practices.",
                        "duration_weeks": 4,
                        "resources": [
                            "Official Documentation Deep Dive",
                            "Intermediate Course (edX - MIT)",
                            "Hands-on Exercises (LeetCode Easy)",
                            "YouTube Tutorial Series (Traversy Media)"
                        ],
                        "projects": [
                            "Build a portfolio-worthy personal project",
                            "Contribute to a beginner-friendly open source repo"
                        ],
                        "certifications": ["IBM Skills Network Beginner Badge"]
                    },
                    {
                        "order": 3,
                        "title": "First Project Launch",
                        "description": "Apply your beginner skills to build and deploy a complete project.",
                        "duration_weeks": 3,
                        "resources": [
                            "GitHub Portfolio Guide",
                            "Deployment Tutorial (Netlify/Vercel/Heroku)",
                            "Code Review Best Practices (YouTube)",
                            "Beginner Projects Playlist (Fireship)"
                        ],
                        "projects": [
                            "Build and deploy a full beginner project",
                            "Write a README and document your project"
                        ],
                        "certifications": [f"{domain} Essentials Certificate"]
                    }
                ],
                "intermediate": [
                    {
                        "order": 1,
                        "title": "Intermediate Frameworks & Tools",
                        "description": "Learn the frameworks and tools used by professionals.",
                        "duration_weeks": 4,
                        "resources": [
                            "Professional Framework Course (Udemy - Best Seller)",
                            "Tool Mastery Series (Pluralsight)",
                            "Real-World Projects Tutorial (Frontend Mentor)",
                            "Design Patterns & Best Practices (O'Reilly)"
                        ],
                        "projects": [
                            "Build a full-featured web application",
                            "Clone a popular app from scratch"
                        ],
                        "certifications": [f"AWS/Azure Professional Certification"]
                    },
                    {
                        "order": 2,
                        "title": "APIs, Databases & Integration",
                        "description": "Connect real data sources and build production-grade features.",
                        "duration_weeks": 3,
                        "resources": [
                            "REST API Masterclass (YouTube - TechWithTim)",
                            "Database Design Course (freeCodeCamp)",
                            "System Design Intro (ByteByteGo)",
                            "Integration Testing Guide (Official Docs)"
                        ],
                        "projects": [
                            "Build a CRUD app with real database",
                            "Create and document a public API"
                        ],
                        "certifications": ["MongoDB Developer Associate"]
                    },
                    {
                        "order": 3,
                        "title": "Intermediate Capstone Project",
                        "description": "Build a complex, multi-feature project for your portfolio.",
                        "duration_weeks": 4,
                        "resources": [
                            "Capstone Project Guide (Coursera)",
                            "Code Quality & Refactoring (SonarQube)",
                            "Agile Development Basics (Atlassian)",
                            "Open Source Contribution Guide (GitHub)"
                        ],
                        "projects": [
                            "Build a production-level capstone project",
                            "Submit to GitHub and get code review"
                        ],
                        "certifications": ["Professional Developer Certificate"]
                    }
                ],
                "advanced": [
                    {
                        "order": 1,
                        "title": "Advanced Architecture & Patterns",
                        "description": "Master advanced architectural patterns used at scale.",
                        "duration_weeks": 4,
                        "resources": [
                            "System Design Interview (ByteByteGo Book)",
                            "Advanced Patterns Course (Pluralsight Expert)",
                            "Architecture Deep Dive (InfoQ Articles)",
                            "Open Source Code Reading"
                        ],
                        "projects": [
                            "Design and implement a scalable system",
                            "Write technical blog posts about your learnings"
                        ],
                        "certifications": ["Senior/Professional Level Certification"]
                    },
                    {
                        "order": 2,
                        "title": "Performance, Security & DevOps",
                        "description": "Optimize, secure, and deploy applications like a pro.",
                        "duration_weeks": 3,
                        "resources": [
                            "Performance Optimization Course (Google)",
                            "Security Best Practices (OWASP)",
                            "Docker & Kubernetes Fundamentals (KodeKloud)",
                            "CI/CD Pipeline Guide (GitHub Actions)"
                        ],
                        "projects": [
                            "Set up CI/CD pipeline for a personal project",
                            "Conduct a security audit on your app"
                        ],
                        "certifications": ["AWS/Azure/GCP Associate Certification"]
                    },
                    {
                        "order": 3,
                        "title": "Job Readiness & Interview Prep",
                        "description": "Prepare for technical interviews and land your dream job.",
                        "duration_weeks": 4,
                        "resources": [
                            "LeetCode 75 (Must-do Problems)",
                            "System Design Interview (YouTube - Mock Interviews)",
                            "Resume & Portfolio Workshop (Google Career Certificates)",
                            "Behavioral Interview Prep (Levels.fyi)"
                        ],
                        "projects": [
                            "Finalize and polish your portfolio",
                            "Complete 50 LeetCode problems"
                        ],
                        "certifications": ["Professional Cloud/Domain Certification"]
                    }
                ]
            }
        }

    def _mock_weekly_plan(self, study_hours: int) -> dict:
        daily_hours = round(study_hours / 6, 1)
        return {
            "week_theme": "Building Strong Foundations",
            "total_hours": study_hours,
            "days": {
                "Monday": {"tasks": ["Watch tutorial videos (1hr)", "Take notes & summarize"], "hours": daily_hours, "focus": "New Concepts"},
                "Tuesday": {"tasks": ["Practice exercises (45min)", "Review Monday notes"], "hours": daily_hours, "focus": "Practice"},
                "Wednesday": {"tasks": ["Work on mini-project", "Read documentation"], "hours": daily_hours, "focus": "Hands-on"},
                "Thursday": {"tasks": ["Continue project", "Watch advanced tutorial"], "hours": daily_hours, "focus": "Deep Work"},
                "Friday": {"tasks": ["Complete project milestone", "Push to GitHub"], "hours": daily_hours, "focus": "Completion"},
                "Saturday": {"tasks": ["Explore new tools", "Read community blogs"], "hours": round(daily_hours * 0.7, 1), "focus": "Exploration"},
                "Sunday": {"tasks": ["Weekly review & reflection", "Plan next week"], "hours": 0.5, "focus": "Rest & Review"}
            },
            "goals": [
                "Complete this week's milestone",
                "Build one mini-project",
                "Practice 30 minutes daily"
            ],
            "motivation": "Every expert was once a beginner. You're exactly where you need to be! 🌟"
        }


# ─── Global client instance ────────────────────────────────
_watsonx_client = None


def get_watsonx_client() -> WatsonxClient:
    """Get or create the global Watsonx.ai client instance.
    Re-initializes if previously failed (e.g. after env vars are set).
    """
    global _watsonx_client

    # Always re-read from env in case vars were set after import
    api_key    = os.environ.get('IBM_API_KEY', '')
    project_id = os.environ.get('IBM_PROJECT_ID', '')
    region     = os.environ.get('IBM_REGION', 'us-south')

    # Re-create if not initialized or credentials changed
    if _watsonx_client is None or not _watsonx_client._initialized:
        _watsonx_client = WatsonxClient(api_key, project_id, region)

    return _watsonx_client
