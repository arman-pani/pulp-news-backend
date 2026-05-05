from functools import lru_cache
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

APP_NAME = "Odia News Backend"
APP_ENV = "development"
DEBUG = False
AUTO_CREATE_TABLES = False
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_TTL_MINUTES = 15
REFRESH_TOKEN_TTL_DAYS = 30
OPENROUTER_MODEL = "openrouter/free"
SARVAM_AI_MODEL = "sarvam-30b"
SARVAM_AI_BASE_URL = "https://api.sarvam.ai/v1"
BATCH_SIZE = 5
RATE_LIMIT_DELAY = 2
MAX_ARTICLE_AGE_DAYS = 2
ARTICLE_RETENTION_DAYS = 7
SCRAPER_TIMEOUT_SECONDS = 30
SUMMARIZATION_TIMEOUT_SECONDS = 300
DEFAULT_ARTICLE_LIMIT = 10
DEFAULT_ARTICLE_OFFSET = 0


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    database_url: str
    jwt_secret_key: str
    redis_url: str | None = None
    openrouter_api_key: str | None = None
    sarvam_ai_api_key: str | None = None
    firebase_credentials_json: str | None = None

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

    def validate_runtime_configuration(self) -> None:
        """Validate the required runtime secrets."""
        missing: list[str] = []
        if not self.database_url:
            missing.append("DATABASE_URL")
        if not self.jwt_secret_key:
            missing.append("JWT_SECRET_KEY")
        if not self.redis_url:
            missing.append("REDIS_URL")
        if not self.openrouter_api_key:
            missing.append("OPENROUTER_API_KEY")
        if not self.sarvam_ai_api_key:
            missing.append("SARVAM_AI_API_KEY")
        if not self.firebase_credentials_json:
            missing.append("FIREBASE_CREDENTIALS_JSON")
        if missing:
            raise ValueError("Missing required configuration: " + ", ".join(missing))


@lru_cache
def get_settings() -> Settings:
    return Settings()
