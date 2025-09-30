# Odia GenAI Backend

A news aggregation and AI summarization service for Odia news content.

## Project Structure

```
functions/
├── __init__.py                 # Package initialization
├── main.py                    # Main entry point for Firebase Functions
├── requirements.txt           # Python dependencies
├── README.md                 # This file
│
├── api/                      # API endpoints and HTTP handlers
│   ├── __init__.py
│   ├── main.py              # HTTP endpoints (articles, search, etc.)
│   └── cron_scraper.py      # Scheduled scraping job
│
├── config/                   # Configuration management
│   ├── __init__.py
│   ├── config.py            # Main configuration class
│   └── config_template.py   # Configuration template
│
├── database/                 # Database models and operations
│   ├── __init__.py
│   ├── postsql_db_connection.py  # Database models and connection
│   ├── crud_operations.py       # Basic CRUD operations
│   ├── db_utility_functions.py  # Database utility functions
│   └── user_article_operations.py # User and article operations
│
├── scraping/                 # News scraping and AI processing
│   ├── __init__.py
│   ├── config.py            # Configuration and constants
│   ├── rss_parser.py        # RSS/Atom feed parsing
│   ├── article_processor.py # Article processing and filtering
│   ├── scraper.py           # Main scraping orchestration
│   └── summarize_article.py # AI summarization using Gemini
│
└── utils/                    # Utility functions (future use)
    └── __init__.py
```

## Key Features

- **News Scraping**: Automated scraping of Odisha TV news articles
- **AI Summarization**: Uses Google Gemini AI to summarize and categorize articles
- **User Management**: Firebase authentication integration
- **Article Tracking**: Tracks which articles users have seen
- **RESTful API**: Clean API endpoints for frontend consumption
- **Database**: PostgreSQL with SQLAlchemy ORM

## API Endpoints

- `GET /get_unseen_articles` - Get articles user hasn't seen
- `GET /get_articles_by_category` - Get articles by category
- `GET /search_articles` - Search articles by query
- `GET /get_bundled_articles` - Get articles bundled by category

## Database Schema

### Users Table
- `auth_id` (String, Primary Key) - Firebase authentication ID
- `created_at` (DateTime) - User creation timestamp

### Articles Table  
- `id` (UUID, Primary Key) - Unique article identifier
- `source_id` (String, Unique) - Source-specific article ID
- `source_name` (String) - News source name
- `source_url` (Text) - Original article URL
- `title` (Text) - Article title
- `author` (Text) - Article author
- `published_at` (DateTime) - Publication date
- `image_url` (Text) - Article image URL
- `content` (Text) - Article content
- `category` (String) - Article category
- `created_at` (DateTime) - Record creation timestamp

### Seen Articles Table
- `id` (Integer, Primary Key) - Auto-increment ID
- `user_auth_id` (String, Foreign Key) - References users.auth_id
- `article_id` (UUID, Foreign Key) - References articles.id
- `seen_at` (DateTime) - When article was marked as seen

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Configure environment variables in `config/config.py`

3. Deploy to Firebase Functions:
   ```bash
   firebase deploy --only functions
   ```

## Development

The project follows a modular structure with clear separation of concerns:

- **API Layer**: Handles HTTP requests and responses
- **Database Layer**: Manages data persistence and queries  
- **Scraping Layer**: Handles web scraping and AI processing
- **Config Layer**: Manages configuration and environment variables

Each module is self-contained with its own `__init__.py` file for clean imports.
