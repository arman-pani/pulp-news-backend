from firebase_functions import scheduler_fn
import logging
from notifications.notification_scheduler import ArticleNotificationScheduler
from firebase_functions import options, scheduler_fn

logger = logging.getLogger(__name__)

@scheduler_fn.on_schedule(
    schedule="15 8,10,12,14,18,22 * * *", 
    timezone="Asia/Kolkata",
    region="asia-south1",
    memory=options.MemoryOption.MB_512,
)
def scheduled_article_notifications(event):
    """
    Scheduled function to send notifications for articles created 15 minutes ago.
    Runs at 8:45am, 10:45am, 12:45pm, 2:45pm, 6:45pm, 10:45pm IST (15 minutes after web scraping).
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

