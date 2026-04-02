from datetime import datetime

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
    user_id: str


class BundledCategoryPayload(BaseModel):
    articles: list[ArticleRead]
    total: int
    limit: int


class BundledArticlesResponse(BaseModel):
    categories: dict[str, BundledCategoryPayload]
    total_categories: int
    limit_per_category: int
    success: bool = True



class MessageResponse(BaseModel):
    success: bool = True
    message: str


class AuthTokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    access_token_expires_in: int
    refresh_token_expires_in: int
    user_id: str


class AuthRefreshRequest(BaseModel):
    refresh_token: str


class AuthLogoutRequest(BaseModel):
    refresh_token: str


class FCMTokenUpdateRequest(BaseModel):
    fcm_token: str


class NotificationPreferenceRequest(BaseModel):
    is_enabled: bool
    fcm_token: str | None = None


class NotificationPreferenceResponse(MessageResponse):
    is_notification_enabled: bool
