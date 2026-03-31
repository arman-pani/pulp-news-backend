from fastapi import APIRouter, Depends, Query
from sqlmodel import Session

from app.api.deps import get_current_user, get_db_session
from app.core.config import get_settings
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
    get_unseen_articles_for_user,
    search_articles,
)

router = APIRouter(prefix="/articles", tags=["articles"])
settings = get_settings()


@router.get("/unseen", response_model=UnseenArticlesResponse)
def read_unseen_articles(
    limit: int = Query(default=settings.default_article_limit, ge=1, le=100),
    category: str | None = Query(default=None),
    current_user: AuthenticatedUser = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> UnseenArticlesResponse:
    articles = get_unseen_articles_for_user(
        session,
        auth_id=current_user.uid,
        limit=limit,
        category=category,
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
    limit: int = Query(default=settings.default_article_limit, ge=1, le=100),
    offset: int = Query(default=settings.default_article_offset, ge=0),
    session: Session = Depends(get_db_session),
) -> ArticlesByCategoryResponse:
    articles = get_articles_by_category(session, category=category, limit=limit, offset=offset)
    return ArticlesByCategoryResponse(
        articles=[article_to_dict(article) for article in articles],
        category=category,
        limit=limit,
        offset=offset,
    )


@router.get("/search", response_model=SearchArticlesResponse)
def search_articles_route(
    q: str = Query(..., min_length=1),
    limit: int = Query(default=settings.default_article_limit, ge=1, le=100),
    offset: int = Query(default=settings.default_article_offset, ge=0),
    category: str | None = Query(default=None),
    session: Session = Depends(get_db_session),
) -> SearchArticlesResponse:
    articles = search_articles(
        session,
        search_query=q,
        limit=limit,
        offset=offset,
        category=category,
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
    session: Session = Depends(get_db_session),
) -> BundledArticlesResponse:
    bundled = get_bundled_articles_by_category(session, limit_per_category=limit_per_category)
    payload = {
        category: BundledCategoryPayload(
            articles=data["articles"],
            total=data["total"],
            limit=data["limit"],
        )
        for category, data in bundled["categories"].items()
    }
    return BundledArticlesResponse(
        categories=payload,
        total_categories=bundled["total_categories"],
        limit_per_category=limit_per_category,
    )
