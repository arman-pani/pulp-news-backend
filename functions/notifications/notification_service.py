import firebase_admin
from firebase_admin import credentials, messaging
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime, timedelta
from sqlalchemy import desc
from database.postsql_db_connection import Article, User, get_db_session

logger = logging.getLogger(__name__)

class ArticleFCMNotificationService:
    def __init__(self):
        try:
            if not firebase_admin._apps:
                cred = credentials.ApplicationDefault()
                firebase_admin.initialize_app(cred)
            self.messaging = messaging
        except Exception as e:
            logger.error(f"Failed to initialize FCM: {e}")
            raise

    def get_active_subscribers(self) -> List[str]:
        """Get all FCM tokens for users with notifications enabled"""
        with get_db_session() as db:
            try:
                users = db.query(User).filter(
                    User.is_notification_enabled == True,  # Fixed field name
                    User.fcm_token.isnot(None)
                ).all()
                
                tokens = [user.fcm_token for user in users if user.fcm_token]
                logger.info(f"Found {len(tokens)} active subscribers")
                return tokens
                
            except Exception as e:
                logger.error(f"Error fetching active subscribers: {e}")
                return []


    def send_single_article_notification(self, article: Article) -> Dict[str, Any]:
        """Send notification for a single article"""
        try:
            # Get active subscribers
            tokens = self.get_active_subscribers()
            
            if not tokens:
                logger.info("No active subscribers found")
                return {"status": "no_subscribers", "sent_count": 0}

            # Prepare notification content from article
            title = f"📰 {article.source_name}"
            body = article.title
            image_url = article.image_url or "https://via.placeholder.com/400x200/4CAF50/FFFFFF?text=News"
            
            # Truncate body if too long (FCM has limits)
            if len(body) > 150:
                body = body[:147] + "..."
            
            # Prepare article data for the notification payload
            data = {
                "type": "new_article",
                "article_id": str(article.id),
                "source_name": article.source_name,
                "title": article.title,
                "author": article.author or "",
                "image_url": image_url,
                "category": article.category or "General",
                "published_at": article.published_at.isoformat() if article.published_at else "",
                "click_action": "FLUTTER_NOTIFICATION_CLICK",
                "route": f"/article/{article.id}"
            }
            
            # Send notification
            result = self.send_to_tokens_with_image(
                tokens=tokens,
                title=title,
                body=body,
                image_url=image_url,
                data=data
            )
            
            logger.info(f"Article notification sent for: {article.title}")
            
            return {
                "status": "success",
                "article_id": str(article.id),
                "article_title": article.title,
                "image_used": image_url,
                **result
            }
            
        except Exception as e:
            logger.error(f"Error sending single article notification: {e}")
            return {"status": "error", "sent_count": 0}

    def send_to_tokens_with_image(
        self, 
        tokens: List[str], 
        title: str, 
        body: str, 
        image_url: str,
        data: Dict[str, str] = None
    ) -> Dict[str, Any]:
        """Send notification with image to multiple FCM tokens"""
        try:
            message = messaging.MulticastMessage(
                notification=messaging.Notification(
                    title=title,
                    body=body,
                    image=image_url
                ),
                data=data or {},
                tokens=tokens,
                apns=messaging.APNSConfig(
                    payload=messaging.APNSPayload(
                        aps=messaging.Aps(
                            mutable_content=1,  # Required for iOS to display custom images
                            category="NEWS_ARTICLE"  # Custom category for iOS
                        )
                    )
                ),
                android=messaging.AndroidConfig(
                    notification=messaging.AndroidNotification(
                        image=image_url,  # For Android
                        channel_id="news_articles",  # Android notification channel
                        priority="high",
                        visibility="public"
                    ),
                    priority="high"
                )
            )
            
            response = messaging.send_multicast(message)
            
            # Log results
            logger.info(f"Notification with image sent: {response.success_count} successful, {response.failure_count} failed")
            
            # Handle failed tokens
            if response.failure_count > 0:
                self._handle_failed_tokens(tokens, response.responses)
            
            return {
                "success_count": response.success_count,
                "failure_count": response.failure_count,
                "total": len(tokens)
            }
            
        except Exception as e:
            logger.error(f"Error sending notification with image: {e}")
            return {"success_count": 0, "failure_count": len(tokens), "total": len(tokens)}

    def _handle_failed_tokens(self, tokens: List[str], responses: List[messaging.SendResponse]):
        """Handle failed FCM tokens by removing invalid ones from database"""
        with get_db_session() as db:
            try:
                for i, response in enumerate(responses):
                    if not response.success:
                        token = tokens[i]
                        # Remove invalid FCM token from database
                        user = db.query(User).filter(User.fcm_token == token).first()
                        if user:
                            user.fcm_token = None
                            user.is_notification_enabled = False  # Fixed field name
                            logger.info(f"Removed invalid FCM token for user: {user.auth_id}")
                
                db.commit()
            except Exception as e:
                db.rollback()
                logger.error(f"Error handling failed tokens: {e}")

    def send_test_notification(self, test_token: str) -> Dict[str, Any]:
        """Send a test notification to verify FCM setup"""
        try:
            message = messaging.Message(
                notification=messaging.Notification(
                    title="🧪 Test Notification",
                    body="This is a test notification from Odiya GenAI Backend"
                ),
                data={
                    "type": "test",
                    "timestamp": datetime.utcnow().isoformat()
                },
                token=test_token
            )
            
            response = messaging.send(message)
            logger.info(f"Test notification sent successfully: {response}")
            
            return {
                "success": True,
                "message": "Test notification sent successfully",
                "message_id": response
            }
            
        except Exception as e:
            logger.error(f"Error sending test notification: {e}")
            return {
                "success": False,
                "error": str(e)
            }