from __future__ import annotations

import gc
import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlmodel import Session

from app.core.config import get_settings
from app.services.article_repository import (
    batch_check_duplicates,
    filter_articles_by_date,
    save_articles_bulk_insert,
    summarize_articles_in_small_batches,
)
from app.services.extractor import extract_articles_from_rss
from app.services.scraping_config import NEWS_WEBSITES, SCRAPING_SCHEDULES
from app.services.summarization import summarize_articles_batch

logger = logging.getLogger(__name__)
settings = get_settings()


def get_current_schedule(now: datetime | None = None) -> str:
    current = now or datetime.now(timezone.utc)
    ist_time = current + timedelta(hours=5, minutes=30)
    hour = ist_time.hour
    if hour == 8:
        return "8am"
    if hour == 10:
        return "10am"
    if hour == 12:
        return "12pm"
    if hour == 14:
        return "2pm"
    if hour == 18:
        return "6pm"
    if hour == 22:
        return "10pm"
    logger.warning("No schedule match for hour %s, defaulting to 8am", hour)
    return "8am"


def process_articles(session: Session, articles: list[dict[str, Any]]) -> list[Article]:
    """Deduplicate, summarise and persist articles. Returns the saved Article objects."""
    if not articles:
        return []

    recent_articles = filter_articles_by_date(articles, settings.max_article_age_days)
    if not recent_articles:
        return []

    duplicate_urls = batch_check_duplicates(session, recent_articles)
    unique_articles = [article for article in recent_articles if article["url"] not in duplicate_urls]
    if not unique_articles:
        return []

    summarized_articles = summarize_articles_in_small_batches(
        unique_articles,
        summarizer=summarize_articles_batch,
    )
    if not summarized_articles:
        return []

    saved_articles = save_articles_bulk_insert(session, summarized_articles)
    gc.collect()
    return saved_articles




def scrape_and_collect(
    session: Session, schedule_name: str | None = None
) -> tuple[dict[str, Any], list[Any]]:
    """Scrape pipeline used by the cron job. Returns (stats_dict, saved_articles).

    Having the Article objects lets the caller send notifications immediately for the
    exact articles just inserted, avoiding any time-window ambiguity.
    """
    resolved_schedule = schedule_name or get_current_schedule()
    if resolved_schedule not in SCRAPING_SCHEDULES:
        raise ValueError(f"Unknown schedule: {resolved_schedule}")

    schedule_config = SCRAPING_SCHEDULES[resolved_schedule]
    all_articles: list[dict[str, Any]] = []
    for source_key in schedule_config["sources"]:
        website_config = NEWS_WEBSITES.get(source_key)
        if website_config is None:
            logger.warning("Unknown source %s in schedule %s", source_key, resolved_schedule)
            continue
        extracted_articles = extract_articles_from_rss(
            rss_url=website_config["rss_url"],
            url_patterns=website_config["url_patterns"],
            source_name=website_config["source_name"],
            max_articles=website_config.get(
                "max_articles_per_source", schedule_config["max_articles_per_source"]
            ),
        )
        all_articles.extend(extracted_articles)

    saved_articles = process_articles(session, all_articles)
    stats = {
        "schedule": resolved_schedule,
        "description": schedule_config["description"],
        "sources": schedule_config["sources"],
        "scraped_articles": len(all_articles),
        "saved_articles": len(saved_articles),
    }
    return stats, saved_articles
