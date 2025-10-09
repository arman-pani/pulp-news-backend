import firebase_admin
from firebase_admin import messaging
from typing import List, Dict, Any
import logging
import gc
import psutil
import os
from database.postsql_db_connection import User, get_db_session

logger = logging.getLogger(__name__)

def log_memory_usage(stage: str):
    """Log current memory usage for monitoring"""
    try:
        process = psutil.Process(os.getpid())
        memory_info = process.memory_info()
        memory_mb = memory_info.rss / 1024 / 1024
        logger.info(f"Memory usage at {stage}: {memory_mb:.2f} MB")
        return memory_mb
    except Exception as e:
        logger.warning(f"Could not get memory usage: {e}")
        return 0

class ArticleFCMNotificationService:
    def __init__(self):
        # Ensure Firebase is initialized
        if not firebase_admin._apps:
            firebase_admin.initialize_app()
        self.messaging = messaging

    def get_active_subscribers(self) -> List[str]:
        """Get all FCM tokens for users with notifications enabled with memory management"""
        log_memory_usage("Before fetching subscribers")
        
        with get_db_session() as db:
            try:
                users = db.query(User).filter(
                    User.is_notification_enabled == True,
                    User.fcm_token.isnot(None)
                ).all()
                
                tokens = [user.fcm_token for user in users if user.fcm_token]
                
                # Clean up
                del users
                gc.collect()
                log_memory_usage("After fetching subscribers")
                
                logger.info(f"Found {len(tokens)} active subscribers")
                return tokens
                
            except Exception as e:
                logger.error(f"Error fetching active subscribers: {e}")
                return []

    def send_single_article_notification_with_data(self, article_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send notification for a single article using pre-extracted data"""
        try:
            # Get active subscribers
            tokens = self.get_active_subscribers()
            
            if not tokens:
                logger.info("No active subscribers found")
                return {"status": "no_subscribers", "sent_count": 0}

            # Prepare notification content from article data
            title = f"{article_data['source_name']}"
            body = article_data['title']
            image_url = article_data['image_url'] or "https://placehold.co/600x400"
            
            # Truncate body if too long (FCM has limits)
            if len(body) > 150:
                body = body[:147] + "..."
            
            # Prepare article data for the notification payload
            data = {
                "type": "new_article",
                "id": str(article_data['id']),
                "source_name": article_data['source_name'],
                "source_url": article_data['source_url'],
                "title": article_data['title'],
                "author": article_data['author'] or "",
                "image_url": image_url,
                "category": article_data['category'] or "General",
                "content": article_data['content'] or "",
                "published_at": article_data['published_at'],
                "created_at": article_data['created_at'],
                "click_action": "FLUTTER_NOTIFICATION_CLICK",
            }
            
            # Send notification
            result = self.send_to_tokens_with_image(
                tokens=tokens,
                title=title,
                body=body,
                image_url=image_url,
                data=data
            )
            
            logger.info(f"Article notification sent for: {article_data['title']}")
            
            return {
                "status": "success",
                "article_id": str(article_data['id']),
                "article_title": article_data['title'],
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
        """Send notification with image to multiple FCM tokens with memory management"""
        log_memory_usage("Before sending notifications")
        
        try:
            # Filter out invalid tokens before sending
            valid_tokens = []
            for token in tokens:
                if token and len(token) > 20 and not token.startswith('test_'):
                    valid_tokens.append(token)
                else:
                    logger.warning(f"Skipping invalid token: {token[:10] + '...' if token else 'None'}")
            
            if not valid_tokens:
                logger.warning("No valid FCM tokens found to send notifications to")
                return {"success_count": 0, "failure_count": len(tokens), "total": len(tokens)}
            
            # Log the valid tokens being used (first few characters only for security)
            logger.info(f"Sending notification to {len(valid_tokens)} valid tokens: {[token[:10] + '...' for token in valid_tokens[:3]]}")
            
            # Send simple notifications to each token individually
            success_count = 0
            failure_count = 0
            
            for i, token in enumerate(valid_tokens):
                try:
                    # Create message with image for each token
                    message = messaging.Message(
                        notification=messaging.Notification(
                            title=title,
                            body=body,
                            image=image_url
                        ),
                        data=data or {},
                        token=token,
                        android=messaging.AndroidConfig(
                            notification=messaging.AndroidNotification(
                                image=image_url,
                                channel_id="news_articles",
                                priority="high",
                                visibility="public"
                            ),
                            priority="high"
                        ),
                        apns=messaging.APNSConfig(
                            payload=messaging.APNSPayload(
                                aps=messaging.Aps(
                                    mutable_content=1,
                                    category="NEWS_ARTICLE"
                                )
                            )
                        )
                    )
                    
                    response = messaging.send(message)
                    success_count += 1
                    logger.info(f"Notification with image sent to token {token[:10]}...: {response}")
                    
                    # Clean up message object
                    del message
                    del response
                    
                except Exception as e:
                    failure_count += 1
                    logger.error(f"Failed to send to token {token[:10]}...: {e}")
                
                # Memory cleanup every 50 notifications
                if i % 50 == 0 and i > 0:
                    gc.collect()
                    log_memory_usage(f"After sending {i} notifications")
            
            # Final cleanup
            del valid_tokens
            del tokens
            gc.collect()
            log_memory_usage("After sending notifications")
            
            # Return results in the same format as MulticastMessage
            return {
                "success_count": success_count,
                "failure_count": failure_count,
                "total": len(valid_tokens),
                "invalid_tokens_filtered": len(tokens) - len(valid_tokens)
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
                            user.is_notification_enabled = False
                            logger.info(f"Removed invalid FCM token for user: {user.auth_id}")
                
                db.commit()
            except Exception as e:
                db.rollback()
                logger.error(f"Error handling failed tokens: {e}")