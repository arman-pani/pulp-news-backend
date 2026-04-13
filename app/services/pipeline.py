from __future__ import annotations

import gc
import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlmodel import Session

from app.core.config import MAX_ARTICLE_AGE_DAYS
from app.models import Article
from app.services.article_repository import (
    batch_check_duplicates,
    filter_articles_by_date,
    save_articles_bulk_insert,
    summarize_articles_in_small_batches,
)
from app.services.extractor import extract_articles_from_rss
from app.services.rotation import advance_turn, get_and_advance_sources, get_current_turn
from app.services.scraping_config import MAX_ARTICLES_PER_SOURCE
from app.services.summarization import summarize_articles_batch

logger = logging.getLogger(__name__)


def process_articles(
    session: Session,
    articles: list[dict[str, Any]],
    language: str = "english",
) -> list[Article]:
    """Deduplicate, summarise and persist articles. Returns the saved Article objects."""
    if not articles:
        return []

    recent_articles = filter_articles_by_date(articles, MAX_ARTICLE_AGE_DAYS)
    if not recent_articles:
        return []

    duplicate_urls = batch_check_duplicates(session, recent_articles)
    unique_articles = [a for a in recent_articles if a["url"] not in duplicate_urls]
    if not unique_articles:
        return []

    summarized_articles = summarize_articles_in_small_batches(
        unique_articles,
        summarizer=lambda batch: summarize_articles_batch(batch, language=language),
    )
    if not summarized_articles:
        return []

    saved_articles = save_articles_bulk_insert(session, summarized_articles)
    gc.collect()
    return saved_articles


def scrape_and_collect(session: Session) -> tuple[dict[str, Any], list[Any]]:
    """Cron pipeline entry point.

    Reads the current language turn and source index from Redis, scrapes multiple
    sources (default 2), summarises and persists the articles, then advances 
    the rotation state for the next run.

    Returns ``(stats_dict, saved_articles)``.
    """
    language = get_current_turn()
    sources = get_and_advance_sources(language, count=2)
    advance_turn(language)

    all_articles: list[dict[str, Any]] = []
    source_names = []

    for source in sources:
        logger.info(
            "Scraping — language=%s source=%s rss=%s",
            language,
            source["source_name"],
            source["rss_url"],
        )
        source_articles = extract_articles_from_rss(
            rss_url=source["rss_url"],
            url_patterns=source["url_patterns"],
            source_name=source["source_name"],
            max_articles=MAX_ARTICLES_PER_SOURCE,
        )
        all_articles.extend(source_articles)
        source_names.append(source["source_name"])

    saved_articles = process_articles(session, all_articles, language=language)

    stats = {
        "language": language,
        "sources": ", ".join(source_names),
        "scraped_articles": len(all_articles),
        "saved_articles": len(saved_articles),
    }
    return stats, saved_articles
