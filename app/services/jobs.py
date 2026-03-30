from __future__ import annotations

from sqlmodel import Session

from app.core.config import get_settings
from app.services.article_repository import delete_old_articles
from app.services.pipeline import scrape_time_based_sources

settings = get_settings()


def run_scrape_job(session: Session, schedule_name: str | None = None) -> dict:
    return scrape_time_based_sources(session, schedule_name=schedule_name)


def run_cleanup_job(session: Session, days_old: int | None = None) -> dict:
    return delete_old_articles(
        session,
        days_old=days_old if days_old is not None else settings.article_retention_days,
    )
