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
    get_recent_article_for_notification,
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

    def send_single_article_notification_with_data(
        self,
        session: Session,
        article_data: dict[str, Any],
    ) -> dict[str, Any]:
        tokens = get_notification_tokens(session)
        if not tokens:
            return {"status": "no_subscribers", "sent_count": 0}

        title = article_data["source_name"]
        body = article_data["title"]
        if len(body) > 150:
            body = body[:147] + "..."
        image_url = article_data.get("image_url") or "https://placehold.co/600x400"
        payload = _notification_payload(article_data)

        success_count = 0
        failure_count = 0
        invalid_tokens: list[str] = []

        for token in tokens:
            try:
                message = messaging.Message(
                    notification=messaging.Notification(
                        title=title,
                        body=body,
                        image=image_url,
                    ),
                    data=payload,
                    token=token,
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
                self.messaging.send(message)
                success_count += 1
            except Exception as exc:
                failure_count += 1
                code = getattr(exc, "code", "")
                if code in INVALID_TOKEN_CODES:
                    invalid_tokens.append(token)
                logger.warning("Failed to send FCM notification to token: %s", token[:10], exc_info=True)

        for invalid_token in invalid_tokens:
            clear_invalid_fcm_token(session, invalid_token)

        return {
            "status": "success" if success_count else "error",
            "sent_count": success_count,
            "failure_count": failure_count,
            "invalid_tokens_filtered": len(invalid_tokens),
        }


def send_delayed_article_notifications(
    session: Session,
    minutes_back: int | None = None,
) -> dict[str, Any]:
    lookback = minutes_back if minutes_back is not None else settings.notification_delay_minutes
    article = get_recent_article_for_notification(session, lookback)
    if article is None:
        return {
            "status": "no_articles",
            "sent_count": 0,
            "message": "No articles ready for notification",
        }

    article_data = article_to_dict(article)
    service = ArticleFCMNotificationService()
    result = service.send_single_article_notification_with_data(session, article_data)
    return {
        "status": "completed",
        "article_selected": article.title,
        "notification_result": result,
    }
