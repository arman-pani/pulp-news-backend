from datetime import datetime, timedelta
from typing import Any, Dict, List
import logging
from database.postsql_db_connection import Article, get_db_session
from .notification_service import ArticleFCMNotificationService

logger = logging.getLogger(__name__)

class ArticleNotificationScheduler:
    def __init__(self):
        self.fcm_service = ArticleFCMNotificationService()

    def get_articles_for_notification(self, minutes_back: int = 30) -> Dict[str, Any]:
        """Get the first article from database for testing purposes and return as dict"""
        with get_db_session() as db:
            try:
                time_window_start = datetime.utcnow() - timedelta(minutes=minutes_back)
                time_window_end = datetime.utcnow()

                article = db.query(Article).filter(                    
                    Article.created_at >= time_window_start,                    
                    Article.created_at <= time_window_end
                ).order_by(Article.created_at.desc()).first()

                if not article:
                    logger.info("No articles found in database")
                    return {}
                
                # Extract article data while session is still open
                article_data = {
                    "id": article.id,
                    "title": article.title,
                    "source_name": article.source_name,
                    "author": article.author,
                    "source_url": article.source_url,
                    "content": article.content,
                    "image_url": article.image_url,
                    "category": article.category,
                    "published_at": article.published_at.isoformat() if article.published_at else "",
                    "created_at": article.created_at.isoformat() if article.created_at else ""
                }
                
                logger.info(f"Found article for testing: {article.title}")
                return article_data
                
            except Exception as e:
                logger.error(f"Error getting articles for notification: {e}")
                return {}

    def send_delayed_article_notifications(self) -> Dict[str, Any]:
        """Send notification for the best article that was created 30 minutes ago"""
        try:
            # Get article ready for notification
            article_data = self.get_articles_for_notification()
            
            if not article_data:
                logger.info("No articles ready for notification")
                return {
                    "status": "no_articles",
                    "sent_count": 0,
                    "message": "No articles ready for notification"
                }
            
            # Send notification for the article
            result = self.fcm_service.send_single_article_notification_with_data(article_data)
        
            logger.info(f"Delayed article notification completed: {result}")
            
            return {
                "status": "completed",
                "article_selected": article_data["title"],
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