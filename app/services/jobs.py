from __future__ import annotations

from sqlmodel import Session

from app.core.config import get_settings
from app.services.article_repository import delete_old_articles
from app.services.notifications import send_notifications_for_new_articles
from app.services.pipeline import scrape_and_collect

settings = get_settings()


def run_cleanup_job(session: Session, days_old: int | None = None) -> dict:
    return delete_old_articles(
        session,
        days_old=days_old if days_old is not None else settings.article_retention_days,
    )


def run_scrape_and_notify_job(
    session: Session,
    schedule_name: str | None = None,
) -> dict:
    """Cron job: scrape → summarise → persist → notify in one pipeline."""
    stats, saved_articles = scrape_and_collect(session, schedule_name=schedule_name)
    notification_result = send_notifications_for_new_articles(session, saved_articles)
    return {**stats, "notification_result": notification_result}
