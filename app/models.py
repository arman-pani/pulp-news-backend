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
    fcm_token: Optional[str] = Field(default=None, index=True)
    is_notification_enabled: bool = Field(default=False, index=True)


class Article(SQLModel, table=True):
    __tablename__ = "articles"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    source_name: str = Field(max_length=100)
    source_url: str = Field(nullable=False, unique=True, index=True)
    title: str = Field(nullable=False)
    author: Optional[str] = Field(default=None)
    published_at: datetime = Field(default_factory=utc_now, nullable=False, index=True)
    image_url: Optional[str] = Field(default=None)
    content: str = Field(nullable=False)
    category: str = Field(default="General", max_length=50, index=True)
    language: str = Field(default="english", max_length=20, index=True)
    created_at: datetime = Field(default_factory=utc_now, nullable=False, index=True)


class SeenArticle(SQLModel, table=True):
    __tablename__ = "seen_articles"

    user_auth_id: str = Field(
        foreign_key="users.auth_id",
        max_length=255,
        nullable=False,
        primary_key=True,
    )
    article_id: UUID = Field(
        foreign_key="articles.id",
        nullable=False,
        primary_key=True,
    )
    seen_at: datetime = Field(default_factory=utc_now, nullable=False, index=True)


class RefreshSession(SQLModel, table=True):
    __tablename__ = "refresh_sessions"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_auth_id: str = Field(
        foreign_key="users.auth_id",
        max_length=255,
        nullable=False,
        index=True,
    )
    token_hash: str = Field(nullable=False, unique=True, index=True)
    expires_at: datetime = Field(nullable=False, index=True)
    created_at: datetime = Field(default_factory=utc_now, nullable=False)
    revoked_at: Optional[datetime] = Field(default=None, index=True)
    replaced_by_session_id: Optional[UUID] = Field(default=None, nullable=True)
