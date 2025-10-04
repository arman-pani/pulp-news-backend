from firebase_functions import scheduler_fn
from datetime import datetime, timezone

from scraping import scrape_time_based_sources
from config.config import config

import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@scheduler_fn.on_schedule(schedule="30 2,6,10,14 * * *", region="asia-south1")  # 8am, 12pm, 4pm, 8pm IST
def scheduled_news_scraping(event: scheduler_fn.ScheduledEvent) -> None:
    """
    Scheduled function to scrape Odisha news based on current time
    Runs at 8am, 12pm, 4pm, 8pm IST (2:30, 6:30, 10:30, 14:30 UTC)
    
    Schedule:
    - 8 AM IST: Morning news (OdishaTV + Sambad English)
    - 12 PM IST: Afternoon news (OdishaBytes + Orissa Post State)
    - 4 PM IST: Evening news (OdishaTV + Pragativadi)
    - 8 PM IST: Night news (Sambad English + Orissa Post Metro)
    """
    try:
        logger.info("Starting time-based scheduled news scraping...")
        
        # Get current IST time for logging
        ist_now = datetime.now(timezone.utc)
        logger.info(f"Current UTC time: {ist_now.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        
        # Call the time-based scraping function
        saved_count = scrape_time_based_sources()
        
        logger.info(f"Time-based scraping completed. Saved {saved_count} articles.")
        
    except Exception as e:
        logger.error(f"Error in scheduled news scraping: {e}")
        # Don't raise the exception to prevent Firebase from retrying immediately
        # The error will be logged and the next scheduled run will attempt again