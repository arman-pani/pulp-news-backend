from firebase_functions import scheduler_fn
import logging
from notifications.notification_scheduler import ArticleNotificationScheduler

logger = logging.getLogger(__name__)

@scheduler_fn.on_schedule(
    schedule="30 3,7,11,15 * * *",  # 8:30am, 12:30pm, 4:30pm, 8:30pm IST (3:00, 7:00, 11:00, 15:00 UTC)
    timezone="Asia/Kolkata"
)
def scheduled_article_notifications(event):
    """
    Scheduled function to send notifications for articles created 30 minutes ago.
    Runs at 8:30am, 12:30pm, 4:30pm, 8:30pm IST (30 minutes after web scraping).
    """
    try:
        logger.info("Starting scheduled article notifications check")
        
        scheduler = ArticleNotificationScheduler()
        result = scheduler.send_delayed_article_notifications()
        
        logger.info(f"Scheduled notification result: {result}")
        
        return {
            "status": "completed",
            "result": result
        }
        
    except Exception as e:
        logger.error(f"Error in scheduled article notifications: {e}")
        return {
            "status": "error",
            "error": str(e)
        }

