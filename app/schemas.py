from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ArticleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    source_name: str
    source_url: str
    title: str
    author: str | None = None
    image_url: str | None = None
    content: str
    category: str
    published_at: datetime
    created_at: datetime


class ArticlesResponse(BaseModel):
    articles: list[ArticleRead]
    success: bool = True


class ArticlesByCategoryResponse(ArticlesResponse):
    category: str
    limit: int
    offset: int


class SearchArticlesResponse(ArticlesResponse):
    query: str
    category: str | None = None
    limit: int
    offset: int


class UnseenArticlesResponse(ArticlesResponse):
    limit: int
    category: str | None = None
    tracking_enabled: bool


class BundledCategoryPayload(BaseModel):
    articles: list[ArticleRead]
    total: int
    limit: int


class BundledArticlesResponse(BaseModel):
    categories: dict[str, BundledCategoryPayload]
    total_categories: int
    limit_per_category: int
    success: bool = True


class JobResponse(BaseModel):
    status: str
    detail: str
    data: dict[str, Any] | None = None
