from firebase_functions import scheduler_fn

from scraping.news_scraper import scrape_and_process_articles
from config.config import config

import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@scheduler_fn.on_schedule(schedule=config.NEWS_SCRAPING_INTERVAL, region="asia-south1")  # Configurable schedule
def scheduled_news_scraping(event: scheduler_fn.ScheduledEvent) -> None:
    """
    Scheduled function to scrape Odisha news at 12 PM and 6 PM IST daily
    This function will be triggered automatically by Firebase Functions scheduler
    """
    try:
        logger.info("Starting scheduled news scraping...")
        
        # Call the scraping function
        saved_count = scrape_and_process_articles()
        
        logger.info(f"Scheduled scraping completed. Saved {saved_count} articles.")
        
    except Exception as e:
        logger.error(f"Error in scheduled news scraping: {e}")
        # Don't raise the exception to prevent Firebase from retrying immediately
        # The error will be logged and the next scheduled run will attempt again
