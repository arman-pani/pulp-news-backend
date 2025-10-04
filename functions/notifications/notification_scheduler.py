from datetime import datetime, timedelta
from typing import Any, Dict, List
import logging
from database.postsql_db_connection import Article, get_db_session
from .notification_service import ArticleFCMNotificationService

logger = logging.getLogger(__name__)

class ArticleNotificationScheduler:
    def __init__(self):
        self.fcm_service = ArticleFCMNotificationService()

    def get_articles_for_notification(self, minutes_back: int = 30) -> List[Article]:
        """Get articles that were created 30 minutes ago (ready for notification)"""
        with get_db_session() as db:
            try:
                # Calculate the time window: 30 minutes ago ± 2 minutes for flexibility
                target_time = datetime.utcnow() - timedelta(minutes=minutes_back)
                time_window_start = target_time - timedelta(minutes=2)
                time_window_end = target_time + timedelta(minutes=2)
                
                articles = db.query(Article).filter(
                    Article.created_at >= time_window_start,
                    Article.created_at <= time_window_end
                ).order_by(Article.created_at.desc()).all()
                
                logger.info(f"Found {len(articles)} articles ready for notification (created around {target_time})")
                return articles
                
            except Exception as e:
                logger.error(f"Error getting articles for notification: {e}")
                return []

    def send_delayed_article_notifications(self) -> Dict[str, Any]:
        """Send notification for the best article that was created 30 minutes ago"""
        try:
            # Get articles ready for notification
            articles = self.get_articles_for_notification()
            
            if not articles:
                logger.info("No articles ready for notification")
                return {
                    "status": "no_articles",
                    "sent_count": 0,
                    "message": "No articles ready for notification"
                }
            
            # Use the first article from the list
            first_article = articles[0]
            
            # Send notification for the first article
            result = self.fcm_service.send_single_article_notification(first_article)
            
            logger.info(f"Delayed article notification completed: {result}")
            
            return {
                "status": "completed",
                "articles_available": len(articles),
                "article_selected": first_article.title,
                "notification_result": result
            }
            
        except Exception as e:
            logger.error(f"Error sending delayed article notifications: {e}")
            return {
                "status": "error",
                "sent_count": 0,
                "error": str(e)
            }

    def send_immediate_notification(self, article_id: str) -> Dict[str, Any]:
        """Send immediate notification for a specific article (for testing)"""
        try:
            with get_db_session() as db:
                article = db.query(Article).filter(Article.id == article_id).first()
                
                if not article:
                    return {
                        "status": "error",
                        "message": "Article not found"
                    }
                
                # Send notification for this specific article
                result = self.fcm_service.send_single_article_notification(article)
                
                logger.info(f"Immediate notification sent for article {article_id}: {result}")
                
                return {
                    "status": "success",
                    "article_id": article_id,
                    "article_title": article.title,
                    "notification_result": result
                }
                
        except Exception as e:
            logger.error(f"Error sending immediate notification: {e}")
            return {
                "status": "error",
                "message": str(e)
            }