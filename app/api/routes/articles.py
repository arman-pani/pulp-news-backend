import json
import logging
from fastapi import APIRouter, Depends, Query
from sqlmodel import Session

from app.api.deps import get_current_user, get_db_session
from app.core.config import DEFAULT_ARTICLE_LIMIT, DEFAULT_ARTICLE_OFFSET
from app.schemas import (
    ArticlesByCategoryResponse,
    BundledArticlesResponse,
    BundledCategoryPayload,
    SearchArticlesResponse,
    UnseenArticlesResponse,
)
from app.services.auth import AuthenticatedUser
from app.services.article_repository import (
    article_to_dict,
    get_articles_by_category,
    get_bundled_articles_by_category,
    get_trending_articles,
    get_unseen_articles_for_user,
    search_articles,
)
from app.core.redis_client import get_redis

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/articles", tags=["articles"])

_LANGUAGE_QUERY = Query(
    default=None,
    description="Filter by language: english | odia | bengali. Omit for all languages.",
)


@router.get("/unseen", response_model=UnseenArticlesResponse)
def read_unseen_articles(
    limit: int = Query(default=DEFAULT_ARTICLE_LIMIT, ge=1, le=100),
    category: str | None = Query(default=None),
    language: str | None = _LANGUAGE_QUERY,
    current_user: AuthenticatedUser = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> UnseenArticlesResponse:
    articles = get_unseen_articles_for_user(
        session,
        auth_id=current_user.uid,
        limit=limit,
        category=category,
        language=language,
    )
    return UnseenArticlesResponse(
        articles=[article_to_dict(article) for article in articles],
        limit=limit,
        category=category,
        user_id=current_user.uid,
    )


@router.get("/by-category", response_model=ArticlesByCategoryResponse)
def read_articles_by_category(
    category: str = Query(...),
    limit: int = Query(default=DEFAULT_ARTICLE_LIMIT, ge=1, le=100),
    offset: int = Query(default=DEFAULT_ARTICLE_OFFSET, ge=0),
    language: str | None = _LANGUAGE_QUERY,
    session: Session = Depends(get_db_session),
) -> ArticlesByCategoryResponse:
    articles = get_articles_by_category(
        session,
        category=category,
        limit=limit,
        offset=offset,
        language=language,
    )
    return ArticlesByCategoryResponse(
        articles=[article_to_dict(article) for article in articles],
        category=category,
        limit=limit,
        offset=offset,
    )


@router.get("/search", response_model=SearchArticlesResponse)
def search_articles_route(
    q: str = Query(..., min_length=1),
    limit: int = Query(default=DEFAULT_ARTICLE_LIMIT, ge=1, le=100),
    offset: int = Query(default=DEFAULT_ARTICLE_OFFSET, ge=0),
    category: str | None = Query(default=None),
    language: str | None = _LANGUAGE_QUERY,
    session: Session = Depends(get_db_session),
) -> SearchArticlesResponse:
    articles = search_articles(
        session,
        search_query=q,
        limit=limit,
        offset=offset,
        category=category,
        language=language,
    )
    return SearchArticlesResponse(
        articles=[article_to_dict(article) for article in articles],
        query=q,
        category=category,
        limit=limit,
        offset=offset,
    )


@router.get("/bundled", response_model=BundledArticlesResponse)
def read_bundled_articles(
    limit_per_category: int = Query(default=5, ge=1, le=50),
    language: str | None = _LANGUAGE_QUERY,
    session: Session = Depends(get_db_session),
) -> BundledArticlesResponse:
    # 1. Cache Key Generation
    cache_key = f"cache:bundled:{language or 'english'}:{limit_per_category}"
    redis_client = get_redis()

    # 2. Cache Hit Attempt
    try:
        cached_data = redis_client.get(cache_key)
        if cached_data:
            logger.info("Cache Hit: %s", cache_key)
            return BundledArticlesResponse.model_validate_json(cached_data)
    except Exception:
        logger.exception("Redis error during cache lookup for %s", cache_key)

    # 3. Cache Miss - Compute Response
    logger.info("Cache Miss: %s", cache_key)
    bundled = get_bundled_articles_by_category(
        session,
        limit_per_category=limit_per_category,
        language=language,
    )

    trending_articles = get_trending_articles(session, language=language)

    payload = {
        category: BundledCategoryPayload(
            articles=data["articles"],
            total=data["total"],
            limit=data["limit"],
        )
        for category, data in bundled["categories"].items()
    }

    response_data = BundledArticlesResponse(
        categories=payload,
        trending=[article_to_dict(article) for article in trending_articles],
        total_categories=bundled["total_categories"],
        limit_per_category=limit_per_category,
    )

    # 4. Save to Cache with 5-hour TTL
    try:
        redis_client.setex(
            cache_key,
            18000,  # 5 hours
            response_data.model_dump_json(),
        )
    except Exception:
        logger.exception("Failed to save response to cache for %s", cache_key)

    return response_data
