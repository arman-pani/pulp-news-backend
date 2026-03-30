from functools import lru_cache
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "Odia News Backend"
    app_env: str = "development"
    debug: bool = False
    database_url: str = "sqlite:///./odiya_news.db"
    openrouter_api_key: str | None = None
    openrouter_model: str = "meta-llama/llama-3.3-70b-instruct:free"
    internal_api_token: str | None = None
    auto_create_tables: bool = True

    permanent_categories: List[str] = Field(
        default_factory=lambda: [
            "Politics",
            "Crime",
            "Technology",
            "Sports",
            "Entertainment",
            "Business",
            "General",
        ]
    )

    batch_size: int = 10
    rate_limit_delay: int = 2
    max_article_age_days: int = 2
    article_retention_days: int = 7
    scraper_timeout_seconds: int = 30
    max_articles_per_source: int = 10
    default_article_limit: int = 10
    default_article_offset: int = 0


@lru_cache
def get_settings() -> Settings:
    return Settings()
