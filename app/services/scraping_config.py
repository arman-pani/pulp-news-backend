"""News source configuration.

Sources are grouped by language.  The cron pipeline picks one source per tick
using the Redis-backed rotation state in ``app.services.rotation``.
"""

from __future__ import annotations

# Languages processed in this order during each full rotation cycle.
LANGUAGE_CYCLE: list[str] = ["english", "odia", "bengali"]

# Maximum articles fetched from a single source per cron run.
MAX_ARTICLES_PER_SOURCE: int = 10

# ---------------------------------------------------------------------------
# All news sources, keyed by language then by a short string identifier.
# Each entry must have: base_url, rss_url, source_name, url_patterns.
# ---------------------------------------------------------------------------
LANGUAGE_SOURCES: dict[str, dict[str, dict]] = {

    # -----------------------------------------------------------------------
    # National-Wide English News Websites
    # -----------------------------------------------------------------------
    "english": {
        "timesofindia": {
            "base_url": "https://timesofindia.indiatimes.com",
            "rss_url": "https://timesofindia.indiatimes.com/rssfeedstopstories.cms",
            "source_name": "Times of India",
            "url_patterns": [
                "https://timesofindia.indiatimes.com/india/",
                "https://timesofindia.indiatimes.com/world/",
                "https://timesofindia.indiatimes.com/business/",
            ],
        },
        "thehindu": {
            "base_url": "https://www.thehindu.com",
            "rss_url": "https://www.thehindu.com/feeder/default.rss",
            "source_name": "The Hindu",
            "url_patterns": [
                "https://www.thehindu.com/news/national/",
                "https://www.thehindu.com/news/international/",
            ],
        },
        "hindustantimes": {
            "base_url": "https://www.hindustantimes.com",
            "rss_url": "https://www.hindustantimes.com/feeds/rss/latest/rssfeed.xml",
            "source_name": "Hindustan Times",
            "url_patterns": [
                "https://www.hindustantimes.com/india-news/",
                "https://www.hindustantimes.com/world-news/",
            ],
        },
        "ndtv_english": {
            "base_url": "https://www.ndtv.com",
            "rss_url": "https://feeds.feedburner.com/ndtvnews-top-stories",
            "source_name": "NDTV",
            "url_patterns": [
                "https://www.ndtv.com/india-news/",
            ],
        },
        "news18_english": {
            "base_url": "https://www.news18.com",
            "rss_url": "https://www.news18.com/commonfeeds/v1/eng/rss/india.xml",
            "source_name": "News18 English",
            "url_patterns": [
                "https://www.news18.com/india/",
            ],
        },
        "deccanherald": {
            "base_url": "https://www.deccanherald.com",
            "rss_url": "https://www.deccanherald.com/stories.rss",
            "source_name": "Deccan Herald",
            "url_patterns": [
                "https://www.deccanherald.com/india/",
            ],
        },
        "indianexpress": {
            "base_url": "https://indianexpress.com",
            "rss_url": "https://indianexpress.com/section/trending/feed/",
            "source_name": "Indian Express",
            "url_patterns": [
                "https://indianexpress.com/article/trending/",
            ],
        },
        "indiatoday": {
            "base_url": "https://www.indiatoday.in",
            "rss_url": "https://www.indiatoday.in/rss/1206578",
            "source_name": "India Today",
            "url_patterns": [
                "https://www.indiatoday.in/india/story",
            ],
        },
    },

    # -----------------------------------------------------------------------
    # Odia Based News Websites (Native Text Content)
    # -----------------------------------------------------------------------
    "odia": {
        "sambad_odia": {
            "base_url": "https://sambad.in",
            "rss_url": "https://sambad.in/rss",
            "source_name": "Sambad",
            "url_patterns": [
                "https://sambad.in/",
            ],
        },
        "prameya_odia": {
            "base_url": "https://www.prameya.com",
            "rss_url": "https://www.prameya.com/feed",
            "source_name": "Prameya",
            "url_patterns": [
                "https://www.prameya.com/",
            ],
        },
        "khabarodisha": {
            "base_url": "https://khabarodisha.com",
            "rss_url": "https://khabarodisha.com/RSS/Feed/Khabar-Odisha-Special-and-Odisha-News-Detail",
            "source_name": "Khabar Odisha",
            "url_patterns": [
                "https://khabarodisha.com/",
            ],
        },
        "odia_oneindia": {
            "base_url": "https://odia.oneindia.com",
            "rss_url": "https://odia.oneindia.com/rss/feeds/oneindia-odia-fb.xml",
            "source_name": "Oneindia Odia",
            "url_patterns": [
                "https://odia.oneindia.com/",
            ],
        },
        "kanaknews": {
            "base_url": "https://kanaknews.com",
            "rss_url": "https://kanaknews.com/rss",
            "source_name": "Kanak News",
            "url_patterns": [
                "https://kanaknews.com/",
            ],
        },
        "dharitri": {
            "base_url": "https://www.dharitri.com",
            "rss_url": "https://www.dharitri.com/rss",
            "source_name": "Dharitri",
            "url_patterns": [
                "https://www.dharitri.com/",
            ],
        },
        "thesamaja": {
            "base_url": "https://thesamaja.in",
            "rss_url": "https://samajalive.in/feed",  # navigable via DOM parsing only
            "source_name": "The Samaja",
            "url_patterns": [
                "https://thesamaja.in/",
            ],
        },
    },

    # -----------------------------------------------------------------------
    # Bengali Based News Websites (Native Text Content)
    # -----------------------------------------------------------------------
    "bengali": {
        "zee_bengali": {
            "base_url": "https://zeenews.india.com/bengali",
            "rss_url": "http://zeenews.india.com/bengali/rssfeed/nation.xml",
            "source_name": "Zee 24 Ghanta",
            "url_patterns": [
                "/bengali/nation/",
                "/bengali/state/",
            ],
        },
        "abp_ananda": {
            "base_url": "https://bengali.abplive.com",
            "rss_url": "https://bengali.abplive.com/home/feed",
            "source_name": "ABP Ananda",
            "url_patterns": [
                "https://bengali.abplive.com/news/",
            ],
        },
        "sangbadpratidin": {
            "base_url": "https://www.sangbadpratidin.in",
            "rss_url": "https://www.sangbadpratidin.in/feed/",
            "source_name": "Sangbad Pratidin",
            "url_patterns": [
                "https://www.sangbadpratidin.in/",
            ],
        },
        "news18_bengali": {
            "base_url": "https://bengali.news18.com",
            "rss_url": "https://bengali.news18.com/commonfeeds/v1/ben/rss/trending.xml",
            "source_name": "News18 Bengali",
            "url_patterns": [
                "https://bengali.news18.com/news/",
            ],
        },
        "eisamay": {
            "base_url": "https://eisamay.com",
            "rss_url": "https://eisamay.com/stories.rss",
            "source_name": "Eisamay",
            "url_patterns": [
                "https://eisamay.com/",
            ],
        },
        "tv9bangla": {
            "base_url": "https://tv9bangla.com",
            "rss_url": "https://tv9bangla.com/feed",
            "source_name": "TV9 Bangla",
            "url_patterns": [
                "https://tv9bangla.com/",
            ],
        },
        "uttarbangasambad": {
            "base_url": "https://uttarbangasambad.com",
            "rss_url": "https://uttarbangasambad.com/feed/",
            "source_name": "Uttar Bangla Sambad",
            "url_patterns": [
                "https://uttarbangasambad.com/",
            ],
        },
    },
}
