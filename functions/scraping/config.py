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
        "source_name": "Orissa Post",
        "url_patterns": ["https://www.orissapost.com"]
    },
    "orissapost_metro": {
        "base_url": "https://www.orissapost.com",
        "rss_url": "https://www.orissapost.com/metro-news/rss",
        "source_name": "Orissa Post",
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
    },
    "ommcomnews": {
        "base_url": "https://ommcomnews.com",
        "rss_url": "https://ommcomnews.com/rss",
        "source_name": "Ommcom News",
        "url_patterns": ["https://ommcomnews.com/odisha-news/"]
    },
    "dinalipi": {
        "base_url": "https://www.dinalipi.com",
        "rss_url": "https://www.dinalipi.com/category/odisha/rss",
        "source_name": "Dinalipi",
        "url_patterns": ["https://www.dinalipi.com/"]
    },
    "thehindu": {
        "base_url": "https://www.thehindu.com",
        "rss_url": "https://www.thehindu.com/news/states/feeder/default.rss",
        "source_name": "The Hindu",
        "url_patterns": ["https://www.thehindu.com/news/national/odisha/"]
    },
    "prameyanews": {
        "base_url": "https://www.prameyanews.com",
        "rss_url": "https://www.prameyanews.com/feed",
        "source_name": "Prameya News",
        "url_patterns": ["https://www.prameyanews.com/"]
    },
    "odishabarta" : {
        "base_url": "https://www.odishabarta.com",
        "rss_url": "https://www.odishabarta.com/feed",
        "source_name": "Odisha Barta",
        "url_patterns": ["https://www.odishabarta.com/"]
    },
    "odisha24x7" : {
        "base_url": "https://www.odisha24x7.com",
        "rss_url": "https://www.odisha24x7.com/rss",
        "source_name": "Odisha 24x7",
        "url_patterns": ["https://www.odisha24x7.com/"]
    },
   
   
}

# Time-based scraping schedule configuration for specific IST times
SCRAPING_SCHEDULES = {
    "8am": {
        "sources": ["odishatv", "sambadenglish"],
        "max_articles_per_source": 10,
        "description": "8 AM IST",
    },
    "10am": {
        "sources": ["odishabytes", "orissapost_state"],
        "max_articles_per_source": 10,
        "description": "10 AM IST",
    },
    "12pm": {
        "sources": ["orissapost_metro", "pragativadi"],
        "max_articles_per_source": 10,
        "description": "12 PM IST",
    },
    "2pm": {
        "sources": ["ommcomnews", "dinalipi"],
        "max_articles_per_source": 10,
        "description": "2 PM IST",
    },
    "6pm": {
        "sources": ["thehindu", "prameyanews"],
        "max_articles_per_source": 10,
        "description": "6 PM IST",
    },
    "10pm": {
        "sources": ["odishabarta", "odisha24x7"],
        "max_articles_per_source": 10,
        "description": "10 PM IST",
    }
}

# Scraping configuration constants
BATCH_SIZE = 10  # Articles per summarization batch
RATE_LIMIT_DELAY = 2  # Seconds between batches
MAX_ARTICLE_AGE_DAYS = 2  # Maximum age of articles to process
