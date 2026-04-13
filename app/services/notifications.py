from __future__ import annotations

import logging
from typing import Any

from firebase_admin import messaging
from sqlmodel import Session

from app.core.config import get_settings
from app.services.article_repository import (
    article_to_dict,
    clear_invalid_fcm_token,
    get_notification_tokens,
)
from app.services.firebase import get_messaging

logger = logging.getLogger(__name__)
settings = get_settings()

INVALID_TOKEN_CODES = {
    "registration-token-not-registered",
    "invalid-registration-token",
}


def _notification_payload(article_data: dict[str, Any]) -> dict[str, str]:
    image_url = article_data.get("image_url") or "https://placehold.co/600x400"
    return {
        "type": "new_article",
        "id": str(article_data["id"]),
        "source_name": article_data["source_name"],
        "source_url": article_data["source_url"],
        "title": article_data["title"],
        "author": article_data.get("author") or "",
        "image_url": image_url,
        "category": article_data.get("category") or "General",
        "content": article_data.get("content") or "",
        "published_at": article_data["published_at"].isoformat()
        if hasattr(article_data["published_at"], "isoformat")
        else str(article_data["published_at"]),
        "created_at": article_data["created_at"].isoformat()
        if hasattr(article_data["created_at"], "isoformat")
        else str(article_data["created_at"]),
        "click_action": "FLUTTER_NOTIFICATION_CLICK",
    }


class ArticleFCMNotificationService:
    def __init__(self):
        self.messaging = get_messaging()

    def send_article_notification_to_topic(
        self,
        topic: str,
        article_data: dict[str, Any],
    ) -> dict[str, Any]:
        """Broadcasts a notification for an article to a specific FCM topic."""
        title = article_data["source_name"]
        body = article_data["title"]
        if len(body) > 150:
            body = body[:147] + "..."
        image_url = article_data.get("image_url") or "https://placehold.co/600x400"
        payload = _notification_payload(article_data)

        try:
            message = messaging.Message(
                notification=messaging.Notification(
                    title=title,
                    body=body,
                    image=image_url,
                ),
                data=payload,
                topic=topic,
                android=messaging.AndroidConfig(
                    notification=messaging.AndroidNotification(
                        image=image_url,
                        channel_id="news_articles",
                        priority="high",
                        visibility="public",
                    ),
                    priority="high",
                ),
                apns=messaging.APNSConfig(
                    payload=messaging.APNSPayload(
                        aps=messaging.Aps(mutable_content=1, category="NEWS_ARTICLE")
                    )
                ),
            )
            message_id = self.messaging.send(message)
            return {"status": "success", "message_id": message_id}
        except Exception as exc:
            logger.error("Failed to send FCM topic notification to %s", topic, exc_info=True)
            return {"status": "error", "error": str(exc)}



def send_notifications_for_new_articles(
    session: Session,
    article: Any,
    language: str,
) -> dict[str, Any]:
    """Send an FCM notification for the provided article to its language-specific topic.

    Topic name format: news_{language} (e.g., news_odia).
    """
    if not article:
        return {
            "status": "no_article",
            "message": "No article provided for notification",
        }

    article_data = article_to_dict(article)
    service = ArticleFCMNotificationService()
    topic = f"news_{language.lower()}"
    result = service.send_article_notification_to_topic(topic, article_data)
    
    return {
        "status": "completed",
        "topic": topic,
        "article_selected": article.title,
        "notification_result": result,
    }
