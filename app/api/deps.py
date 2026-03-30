from fastapi import Depends, Header, HTTPException, status
from sqlmodel import Session

from app.core.config import Settings, get_settings
from app.db import get_session


def get_db_session(session: Session = Depends(get_session)) -> Session:
    return session


def require_internal_token(
    settings: Settings = Depends(get_settings),
    x_internal_api_token: str | None = Header(default=None),
) -> None:
    if not settings.internal_api_token:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="INTERNAL_API_TOKEN is not configured",
        )
    if x_internal_api_token != settings.internal_api_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid internal API token",
        )
