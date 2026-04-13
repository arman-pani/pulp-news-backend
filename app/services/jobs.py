from __future__ import annotations

from sqlmodel import Session

from app.core.config import ARTICLE_RETENTION_DAYS
from app.services.article_repository import delete_old_articles
from app.services.notifications import send_notifications_for_new_articles
from app.services.pipeline import scrape_and_collect


def run_cleanup_job(session: Session, days_old: int | None = None) -> dict:
    return delete_old_articles(
        session,
        days_old=days_old if days_old is not None else ARTICLE_RETENTION_DAYS,
    )


def run_scrape_and_notify_job(session: Session) -> dict:
    """Cron job: rotate → scrape → summarise → persist → notify in one pipeline."""
    stats, saved_articles = scrape_and_collect(session)
    
    # Pick the latest article and the language for topic-based notification
    last_article = saved_articles[-1] if saved_articles else None
    language = stats.get("language", "english")
    
    notification_result = send_notifications_for_new_articles(
        session, 
        article=last_article, 
        language=language
    )
    return {**stats, "notification_result": notification_result}
