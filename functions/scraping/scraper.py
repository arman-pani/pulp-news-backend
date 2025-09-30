"""
Main scraping orchestration functionality
"""

from datetime import datetime, timezone, timedelta
import logging

from database.postsql_db_connection import test_database_connection
from scraping.config import NEWS_WEBSITES, SCRAPING_SCHEDULES
from scraping.rss_parser import extract_articles_from_rss
from scraping.article_processor import process_articles

logger = logging.getLogger(__name__)

def get_current_schedule() -> str:
    """Determine which scraping schedule to use based on current IST time"""
    # Get current time in UTC and convert to IST (UTC+5:30)
    utc_now = datetime.now(timezone.utc)
    ist_time = utc_now + timedelta(hours=5, minutes=30)
    current_hour = ist_time.hour
    
    # Map specific hours to schedules
    hour_to_schedule = {
        8: "morning",    # 8 AM IST
        12: "afternoon", # 12 PM IST
        16: "evening",   # 4 PM IST
        20: "night"      # 8 PM IST
    }
    
    schedule = hour_to_schedule.get(current_hour)
    if schedule:
        return schedule
    
    # Default to morning if no match (shouldn't happen with proper cron schedule)
    logger.warning(f"No schedule found for hour {current_hour}, defaulting to morning")
    return "morning"

def scrape_time_based_sources() -> int:
    """Scrape articles based on current time schedule"""
    schedule_name = get_current_schedule()
    schedule_config = SCRAPING_SCHEDULES[schedule_name]
    sources = schedule_config["sources"]
    max_articles = schedule_config["max_articles_per_source"]
    
    logger.info(f"Current time-based schedule: {schedule_name}")
    logger.info(f"Description: {schedule_config['description']}")
    logger.info(f"Targeting sources: {sources}")
    logger.info(f"Max articles per source: {max_articles}")
    
    if not test_database_connection():
        logger.error("Cannot proceed without database connection")
        return 0
    
    try:
        all_articles = []
        
        # Extract articles from specified sources only
        for source_key in sources:
            if source_key not in NEWS_WEBSITES:
                logger.warning(f"Source {source_key} not found in NEWS_WEBSITES")
                continue
                
            website_config = NEWS_WEBSITES[source_key]
            logger.info(f"Scraping from {website_config['source_name']}...")
            
            articles = extract_articles_from_rss(website_config, max_articles)
            all_articles.extend(articles)
            logger.info(f"Got {len(articles)} articles from {website_config['source_name']}")
        
        logger.info(f"Total articles scraped: {len(all_articles)}")
        
        if not all_articles:
            logger.warning("No articles found to process")
            return 0
        
        # Process articles through the complete pipeline
        saved_count = process_articles(all_articles)
        
        logger.info(f"{schedule_config['description']} scraping completed")
        return saved_count
        
    except Exception as e:
        logger.error(f"Error in {schedule_name} scraping: {e}")
        return 0
