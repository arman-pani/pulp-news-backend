from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class User(SQLModel, table=True):
    __tablename__ = "users"

    auth_id: str = Field(primary_key=True, max_length=255)
    created_at: datetime = Field(default_factory=utc_now, nullable=False)
    fcm_token: Optional[str] = Field(default=None)
    is_notification_enabled: bool = Field(default=False)


class Article(SQLModel, table=True):
    __tablename__ = "articles"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    source_name: str = Field(default="OdishaTV", max_length=100)
    source_url: str = Field(nullable=False, unique=True, index=True)
    title: str = Field(nullable=False)
    author: Optional[str] = Field(default=None)
    published_at: datetime = Field(default_factory=utc_now, nullable=False)
    image_url: Optional[str] = Field(default=None)
    content: str = Field(nullable=False)
    category: str = Field(default="General", max_length=50)
    created_at: datetime = Field(default_factory=utc_now, nullable=False)


class SeenArticle(SQLModel, table=True):
    __tablename__ = "seen_articles"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_auth_id: str = Field(foreign_key="users.auth_id", max_length=255, nullable=False)
    article_id: UUID = Field(foreign_key="articles.id", nullable=False)
    seen_at: datetime = Field(default_factory=utc_now, nullable=False)
