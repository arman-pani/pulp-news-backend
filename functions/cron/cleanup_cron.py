"""
Scheduled cleanup of old articles from the database
"""

from firebase_functions import options, scheduler_fn
from datetime import datetime, timezone
import logging

from database.cleanup_operations import delete_old_articles, get_old_articles_count

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@scheduler_fn.on_schedule(
    schedule="0 0 * * 0",  # Every Sunday at midnight
    timezone="Asia/Kolkata",
    region="asia-south1",
    memory=options.MemoryOption.MB_256,
    timeout_sec=120
)
def scheduled_article_cleanup(event: scheduler_fn.ScheduledEvent) -> None:
    """
    Scheduled function to delete old articles (older than 1 week)
    Runs every Sunday at midnight IST
    
    This function:
    1. Deletes seen_articles records for old articles
    2. Deletes articles older than 7 days
    3. Logs the cleanup results
    """
    try:
        logger.info("Starting scheduled article cleanup...")
        
        # Get current IST time for logging
        ist_now = datetime.now(timezone.utc)
        logger.info(f"Current UTC time: {ist_now.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        
        # Check how many articles will be deleted (for logging)
        old_count = get_old_articles_count(days_old=7)
        logger.info(f"Found {old_count} articles older than 7 days")
        
        if old_count == 0:
            logger.info("No old articles to clean up")
            return
        
        # Perform the cleanup
        result = delete_old_articles(days_old=7)
        
        logger.info(f"Article cleanup completed successfully:")
        logger.info(f"  - Articles deleted: {result['articles_deleted']}")
        logger.info(f"  - Seen articles deleted: {result['seen_articles_deleted']}")
        
    except Exception as e:
        logger.error(f"Error in scheduled article cleanup: {e}")
        # Don't raise the exception to prevent Firebase from retrying immediately
        # The error will be logged and the next scheduled run will attempt again
