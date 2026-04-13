from __future__ import annotations

import gc
import logging
import time
from datetime import datetime, timedelta, timezone
from typing import Any

from dateutil import parser as date_parser
from rapidfuzz import fuzz, process
from sqlmodel import Session, delete, desc, func, or_, select

from app.core.config import (
    ARTICLE_RETENTION_DAYS,
    BATCH_SIZE,
    MAX_ARTICLE_AGE_DAYS,
    RATE_LIMIT_DELAY,
    get_settings,
)
from app.models import Article, RefreshSession, SeenArticle, User

logger = logging.getLogger(__name__)
settings = get_settings()


def normalize_title(title: str) -> str:
    return " ".join(title.lower().split()) if title else ""


def get_or_create_user(session: Session, auth_id: str) -> User:
    user = session.get(User, auth_id)
    if user is None:
        user = User(auth_id=auth_id)
        session.add(user)
        session.flush()
    return user


def get_refresh_sessions_for_user(session: Session, auth_id: str) -> list[RefreshSession]:
    statement = select(RefreshSession).where(RefreshSession.user_auth_id == auth_id)
    return list(session.exec(statement))


def article_to_dict(article: Article) -> dict[str, Any]:
    return {
        "id": article.id,
        "source_name": article.source_name,
        "source_url": article.source_url,
        "title": article.title,
        "author": article.author,
        "image_url": article.image_url,
        "content": article.content,
        "category": article.category,
        "language": article.language,
        "published_at": article.published_at,
        "created_at": article.created_at,
    }


def get_latest_articles(
    session: Session,
    limit: int = 10,
    category: str | None = None,
    language: str | None = None,
) -> list[Article]:
    statement = select(Article)
    if category:
        statement = statement.where(Article.category == category)
    if language:
        statement = statement.where(Article.language == language)
    statement = statement.order_by(desc(Article.created_at)).limit(limit)
    return list(session.exec(statement))


def get_unseen_articles_for_user(
    session: Session,
    auth_id: str,
    limit: int = 10,
    category: str | None = None,
    language: str | None = None,
) -> list[Article]:
    get_or_create_user(session, auth_id)

    statement = (
        select(Article)
        .outerjoin(
            SeenArticle,
            (Article.id == SeenArticle.article_id)
            & (SeenArticle.user_auth_id == auth_id),
        )
        .where(SeenArticle.article_id.is_(None))
    )
    if category:
        statement = statement.where(Article.category == category)
    if language:
        statement = statement.where(Article.language == language)

    articles = list(session.exec(statement.order_by(desc(Article.created_at)).limit(limit)))
    if articles:
        session.add_all(
            [SeenArticle(user_auth_id=auth_id, article_id=article.id) for article in articles]
        )
        session.flush()
    return articles


def update_user_fcm_token(session: Session, auth_id: str, fcm_token: str) -> User:
    user = get_or_create_user(session, auth_id)
    user.fcm_token = fcm_token
    session.add(user)
    session.flush()
    return user


def set_user_notification_preference(
    session: Session,
    auth_id: str,
    is_enabled: bool,
    fcm_token: str | None = None,
) -> User:
    user = get_or_create_user(session, auth_id)
    user.is_notification_enabled = is_enabled
    if fcm_token:
        user.fcm_token = fcm_token
    session.add(user)
    session.flush()
    return user


def get_notification_tokens(session: Session) -> list[str]:
    statement = select(User.fcm_token).where(
        User.is_notification_enabled.is_(True),
        User.fcm_token.is_not(None),
    )
    tokens = session.exec(statement).all()
    return [token for token in tokens if token]


def clear_invalid_fcm_token(session: Session, fcm_token: str) -> None:
    user = session.exec(select(User).where(User.fcm_token == fcm_token)).first()
    if user is None:
        return
    user.fcm_token = None
    user.is_notification_enabled = False
    session.add(user)
    session.flush()


def get_recent_article_for_notification(
    session: Session,
    minutes_back: int,
) -> Article | None:
    window_start = datetime.now(timezone.utc) - timedelta(minutes=minutes_back)
    statement = (
        select(Article)
        .where(Article.created_at >= window_start)
        .where(Article.created_at <= datetime.now(timezone.utc))
        .order_by(desc(Article.created_at))
    )
    return session.exec(statement).first()




def get_articles_by_category(
    session: Session,
    category: str,
    limit: int = 10,
    offset: int = 0,
    language: str | None = None,
) -> list[Article]:
    statement = select(Article).where(Article.category == category)
    if language:
        statement = statement.where(Article.language == language)
    statement = statement.order_by(desc(Article.created_at)).offset(offset).limit(limit)
    return list(session.exec(statement))


def search_articles(
    session: Session,
    search_query: str,
    limit: int = 10,
    offset: int = 0,
    category: str | None = None,
    language: str | None = None,
) -> list[Article]:
    statement = select(Article).where(
        or_(
            Article.title.ilike(f"%{search_query}%"),
            Article.content.ilike(f"%{search_query}%"),
        )
    )
    if category:
        statement = statement.where(Article.category == category)
    if language:
        statement = statement.where(Article.language == language)
    statement = statement.order_by(desc(Article.created_at)).offset(offset).limit(limit)
    return list(session.exec(statement))


def get_bundled_articles_by_category(
    session: Session,
    limit_per_category: int = 5,
    language: str | None = None,
) -> dict[str, Any]:
    categories = settings.permanent_categories
    if not categories:
        return {"categories": {}, "total_categories": 0, "success": True}

    bundled: dict[str, dict[str, Any]] = {
        category: {"articles": [], "total": 0, "limit": limit_per_category}
        for category in categories
    }
    for category in categories:
        count_stmt = select(func.count()).select_from(Article).where(Article.category == category)
        if language:
            count_stmt = count_stmt.where(Article.language == language)
        total = session.exec(count_stmt).one()
        articles = get_articles_by_category(
            session,
            category=category,
            limit=limit_per_category,
            offset=0,
            language=language,
        )
        bundled[category]["articles"] = [article_to_dict(article) for article in articles]
        bundled[category]["total"] = total

    return {"categories": bundled, "total_categories": len(categories), "success": True}


def get_trending_articles(session: Session, language: str | None = None) -> list[Article]:
    """Retrieve the single most recent article for each permanent category."""
    categories = settings.permanent_categories
    trending: list[Article] = []

    for category in categories:
        statement = select(Article).where(Article.category == category)
        if language:
            statement = statement.where(Article.language == language)

        # Order by created_at to get the very latest we've saved
        statement = statement.order_by(desc(Article.created_at)).limit(1)
        article = session.exec(statement).first()
        if article:
            trending.append(article)

    return trending


def batch_check_duplicates(
    session: Session, scraped_articles: list[dict[str, Any]], title_threshold: int = 85
) -> set[str]:
    if not scraped_articles:
        return set()

    duplicate_urls: set[str] = set()
    source_urls = [article["url"] for article in scraped_articles if "url" in article]
    if source_urls:
        existing_urls = session.exec(
            select(Article.source_url).where(Article.source_url.in_(source_urls))
        ).all()
        duplicate_urls.update(existing_urls)

    cutoff_time = datetime.now(timezone.utc) - timedelta(hours=24)
    recent_titles = session.exec(
        select(Article.title).where(Article.created_at >= cutoff_time)
    ).all()
    seen_titles = {normalize_title(title) for title in recent_titles if title}

    for index, article in enumerate(scraped_articles):
        url = article.get("url")
        title = normalize_title(article.get("original_title", ""))
        if not url or url in duplicate_urls or not title:
            continue

        match = process.extractOne(title, seen_titles, scorer=fuzz.token_set_ratio)
        if match and match[1] >= title_threshold:
            duplicate_urls.add(url)
            continue

        seen_titles.add(title)
        if index % 50 == 0 and index > 0:
            gc.collect()

    return duplicate_urls


def save_articles_bulk_insert(session: Session, articles: list[Article]) -> list[Article]:
    """Bulk-insert new articles, skipping duplicates. Returns the inserted Article objects."""
    if not articles:
        return []

    source_urls = [article.source_url for article in articles]
    existing_urls = set(
        session.exec(select(Article.source_url).where(Article.source_url.in_(source_urls))).all()
    )

    articles_to_insert = [article for article in articles if article.source_url not in existing_urls]
    if not articles_to_insert:
        return []

    session.add_all(articles_to_insert)
    session.flush()
    return articles_to_insert


def filter_articles_by_date(
    articles: list[dict[str, Any]], max_age_days: int | None = None
) -> list[dict[str, Any]]:
    if not articles:
        return articles

    max_days = max_age_days if max_age_days is not None else MAX_ARTICLE_AGE_DAYS
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=max_days)
    filtered: list[dict[str, Any]] = []

    for article in articles:
        publish_date = article.get("publish_date")
        if not publish_date:
            filtered.append(article)
            continue
        try:
            if isinstance(publish_date, str):
                parsed_date = date_parser.parse(publish_date)
            else:
                parsed_date = publish_date
            if parsed_date.tzinfo is None:
                parsed_date = parsed_date.replace(tzinfo=timezone.utc)
            if parsed_date >= cutoff_date:
                filtered.append(article)
        except Exception:
            filtered.append(article)

    return filtered


def summarize_articles_in_small_batches(
    articles: list[dict[str, Any]], summarizer
) -> list[Article]:
    if not articles:
        return []

    processed: list[Article] = []
    for start in range(0, len(articles), BATCH_SIZE):
        batch = articles[start : start + BATCH_SIZE]
        try:
            processed.extend(summarizer(batch))
        except Exception:
            logger.exception("Error summarizing batch %s", start // BATCH_SIZE + 1)
        if start + BATCH_SIZE < len(articles):
            time.sleep(RATE_LIMIT_DELAY)
    return processed


def delete_old_articles(session: Session, days_old: int | None = None) -> dict[str, int]:
    retention_days = days_old if days_old is not None else ARTICLE_RETENTION_DAYS
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=retention_days)
    old_articles = session.exec(select(Article.id).where(Article.published_at < cutoff_date)).all()
    if not old_articles:
        return {"articles_deleted": 0, "seen_articles_deleted": 0}

    seen_deleted = session.exec(
        delete(SeenArticle).where(SeenArticle.article_id.in_(old_articles))
    )
    article_deleted = session.exec(delete(Article).where(Article.id.in_(old_articles)))
    session.flush()
    return {
        "articles_deleted": article_deleted.rowcount or 0,
        "seen_articles_deleted": seen_deleted.rowcount or 0,
    }
