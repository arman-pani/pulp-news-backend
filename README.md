# Odia GenAI Backend

A robust FastAPI-based backend designed to scrape Odia news, summarize articles using Large Language Models (LLMs), and serve them through a secure API with Firebase Cloud Messaging (FCM) notifications.

---

## 🚀 Features

- **Automated Scraping**: Periodically scrapes news from multiple Odia sources.
- **AI Summarization**: Uses OpenRouter/LLMs to generate concise summaries of news articles in Odia.
- **Secure Authentication**: Implements guest JWT-based authentication with access and refresh tokens.
- **Dynamic Notifications**: Integrated with Firebase Cloud Messaging (FCM) for real-time news alerts.
- **Background Jobs**: Standalone cron runner for scraping, cleanup, and notification dispatch.
- **Database Migrations**: Managed via Alembic for reliable schema evolution.

---

## 🛠️ Tech Stack

- **Framework**: [FastAPI](https://fastapi.tiangolo.com/)
- **Database**: PostgreSQL with [SQLModel](https://sqlmodel.tiangolo.com/) (Pydantic + SQLAlchemy)
- **Migrations**: [Alembic](https://alembic.sqlalchemy.org/)
- **Containerization**: Docker & Docker Compose
- **Deployment**: Configured for [Railway](https://railway.com/)
- **AI Integration**: [OpenRouter](https://openrouter.ai/) for LLM access

---

## 📂 Project Structure

```text
.
├── alembic/                # Database migrations (Alembic)
├── app/                    # Main application source code
│   ├── api/                # API layer
│   │   ├── routes/         # Endpoint definitions (Auth, Articles, Users)
│   │   └── deps.py         # FastAPI dependencies (Auth, DB)
│   ├── core/               # Application configuration and settings
│   ├── services/           # Business logic and external integrations
│   │   ├── article_repository.py # Article database operations
│   │   ├── auth.py         # Authentication service logic
│   │   ├── extractor.py    # News content extraction
│   │   ├── firebase.py     # FCM integration
│   │   ├── jobs.py         # Job definitions
│   │   ├── notifications.py# Notification dispatch logic
│   │   ├── pipeline.py     # Scraping & summarization pipeline
│   │   ├── scraping_config.py # configuration for news sources
│   │   └── summarization.py# LLM summarization logic
│   ├── db.py               # Database engine and session setup
│   ├── main.py             # FastAPI app initialization
│   ├── models.py           # SQLModel database schemas
│   └── schemas.py          # Pydantic response/request models
├── API_DOCUMENTATION.md    # Detailed API endpoint references
├── CONFIGURATION.md        # Environment variable and config guide
├── tests/                  # Pytest suite
├── cron_runner.py          # Standalone entry point for background tasks
├── main.py                 # Root entry point for the API server
├── compose.yml             # Local infrastructure (PostgreSQL)
├── railway.json            # Railway deployment configuration
└── requirements.txt        # Python dependencies
```

---

## 🛠️ Local Setup

### 1. Environment Configuration
Clone the repository and create a `.env` file from the example:
```bash
cp .env.example .env
```
Fill in the following mandatory fields:
- `DATABASE_URL`: PostgreSQL connection string.
- `OPENROUTER_API_KEY`: For LLM summarization.
- `JWT_SECRET_KEY`: For token generation.
- `FIREBASE_CREDENTIALS_JSON`: For FCM notifications.

Most application defaults are now code-owned rather than environment-driven, including token TTLs, the OpenRouter model slug, API pagination defaults, scrape batching, and retention settings.

### 2. Infrastructure
Start the local PostgreSQL database:
```bash
docker compose up -d
```

### 3. Database Migrations
Apply the latest migrations to your local database:
```bash
alembic upgrade head
```

### 4. Run the API
```bash
# Using uvicorn directly
uvicorn main:app --reload

# Or via the virtual environment
source .venv/bin/activate
python main.py
```

---

## 🔄 Background Jobs

The project includes a `cron_runner.py` for executing maintenance and automation tasks independently of the web server.

- **Scrape, Summarize & Notify**: `python cron_runner.py --job scrape_and_notify`
- **Cleanup**: `python cron_runner.py --job cleanup`

---

## 🔗 API Overview

The API is structured around several key domains:

- **Auth**: `/auth/guest`, `/auth/refresh`, `/auth/logout`
- **Articles**: `/articles/unseen`, `/articles/by-category`, `/articles/search`, `/articles/bundled`
- **Users**: `/users/me/fcm-token`, `/users/me/notification-preference`
- **Health**: `/health`

Full interactive documentation is available at `/docs` when running locally.

---

## 🧪 Testing

Run the test suite using `pytest`:
```bash
pytest
```

If you are using the project virtual environment, activate it first:
```bash
source .venv/bin/activate
pytest
```
