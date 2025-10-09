"""
Scraping package for news article extraction and processing
"""

from .scraper import scrape_time_based_sources
from .article_extractor import extract_articles_from_rss
from .config import NEWS_WEBSITES, SCRAPING_SCHEDULES

__all__ = [
    'scrape_time_based_sources',
    'extract_articles_from_rss', 
    'NEWS_WEBSITES',
    'SCRAPING_SCHEDULES'
]
