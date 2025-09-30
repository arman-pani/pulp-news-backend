"""
Configuration for news scraping
"""

# Configuration for multiple Odisha news websites with RSS feeds
NEWS_WEBSITES = {
    "odishatv": {
        "base_url": "https://odishatv.in",
        "rss_url": "https://odishatv.in/rss",
        "source_name": "OdishaTV",
        "url_patterns": ["https://odishatv.in/odisha/"]
    },
    "odishabytes": {
        "base_url": "https://odishabytes.com",
        "rss_url": "https://odishabytes.com/category/odisha/rss",
        "source_name": "OdishaBytes",
        "url_patterns": ["https://odishabytes.com/"]
    },
    "sambadenglish": {
        "base_url": "https://sambadenglish.com",
        "rss_url": "https://sambadenglish.com/rss",
        "source_name": "Sambad English",
        "url_patterns": ["/latest-news/", "/news-from-around-the-state/"]
    },
    "orissapost_state": {
        "base_url": "https://www.orissapost.com",
        "rss_url": "https://www.orissapost.com/state-news/rss",
        "source_name": "Orissa Post State",
        "url_patterns": ["https://www.orissapost.com"]
    },
    "orissapost_metro": {
        "base_url": "https://www.orissapost.com",
        "rss_url": "https://www.orissapost.com/metro-news/rss",
        "source_name": "Orissa Post Metro",
        "url_patterns": ["https://www.orissapost.com"]
    },
    "orissadiary": {
        "base_url": "https://orissadiary.com",
        "rss_url": "https://orissadiary.com/category/odisha/rss",
        "source_name": "Orissa Diary",
        "url_patterns": ["https://orissadiary.com/"]
    },
    "pragativadi": {
        "base_url": "https://pragativadi.com",
        "rss_url": "https://pragativadi.com/category/odisha/rss",
        "source_name": "Pragativadi",
        "url_patterns": ["https://pragativadi.com/"]
    }
}

# Time-based scraping schedule configuration for specific IST times
SCRAPING_SCHEDULES = {
    "morning": {
        "sources": ["odishatv", "sambadenglish"],
        "max_articles_per_source": 10,
        "description": "Morning news (8 AM IST)",
    },
    "afternoon": {
        "sources": ["odishabytes", "orissapost_state"],
        "max_articles_per_source": 10,
        "description": "Afternoon news (12 PM IST)",
    },
    "evening": {
        "sources": ["odishatv", "pragativadi"],
        "max_articles_per_source": 10,
        "description": "Evening news (4 PM IST)",
    },
    "night": {
        "sources": ["sambadenglish", "orissapost_metro"],
        "max_articles_per_source": 10,
        "description": "Night news (8 PM IST)",
    }
}

# Scraping configuration constants
BATCH_SIZE = 10  # Articles per summarization batch
RATE_LIMIT_DELAY = 1  # Seconds between batches
MAX_ARTICLE_AGE_DAYS = 2  # Maximum age of articles to process
