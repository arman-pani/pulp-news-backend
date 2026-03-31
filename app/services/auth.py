from __future__ import annotations

import hashlib
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import jwt
from fastapi import HTTPException, status
from sqlmodel import Session, select

from app.core.config import get_settings
from app.models import RefreshSession, User
from app.schemas import AuthTokenResponse


settings = get_settings()


@dataclass(frozen=True)
class AuthenticatedUser:
    uid: str
    token: dict


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _hash_refresh_token(refresh_token: str) -> str:
    return hashlib.sha256(refresh_token.encode("utf-8")).hexdigest()


def _build_access_token(user_id: str) -> tuple[str, int]:
    now = _utc_now()
    expires_at = now + timedelta(minutes=settings.access_token_ttl_minutes)
    payload = {
        "sub": user_id,
        "type": "access",
        "jti": uuid4().hex,
        "iat": int(now.timestamp()),
        "exp": int(expires_at.timestamp()),
    }
    encoded = jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )
    return encoded, int((expires_at - now).total_seconds())


def _create_refresh_session(session: Session, user_id: str) -> tuple[RefreshSession, str, int]:
    raw_refresh_token = secrets.token_urlsafe(48)
    token_hash = _hash_refresh_token(raw_refresh_token)
    now = _utc_now()
    expires_at = now + timedelta(days=settings.refresh_token_ttl_days)
    refresh_session = RefreshSession(
        user_auth_id=user_id,
        token_hash=token_hash,
        expires_at=expires_at,
        created_at=now,
    )
    session.add(refresh_session)
    session.flush()
    return refresh_session, raw_refresh_token, int((expires_at - now).total_seconds())


def _issue_token_pair(session: Session, user_id: str) -> AuthTokenResponse:
    access_token, access_ttl = _build_access_token(user_id)
    _, refresh_token, refresh_ttl = _create_refresh_session(session, user_id)
    return AuthTokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        access_token_expires_in=access_ttl,
        refresh_token_expires_in=refresh_ttl,
        user_id=user_id,
    )


def create_guest_auth_session(session: Session) -> AuthTokenResponse:
    user_id = f"guest_{uuid4().hex}"
    user = User(auth_id=user_id)
    session.add(user)
    session.flush()
    return _issue_token_pair(session, user_id)


def _get_valid_refresh_session(
    session: Session,
    refresh_token: str,
) -> RefreshSession:
    token_hash = _hash_refresh_token(refresh_token)
    refresh_session = session.exec(
        select(RefreshSession).where(RefreshSession.token_hash == token_hash)
    ).first()
    if refresh_session is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )
    if refresh_session.revoked_at is not None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has been revoked",
        )
    if _as_utc(refresh_session.expires_at) <= _utc_now():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has expired",
        )
    return refresh_session


def refresh_auth_session(session: Session, refresh_token: str) -> AuthTokenResponse:
    existing_session = _get_valid_refresh_session(session, refresh_token)
    access_token, access_ttl = _build_access_token(existing_session.user_auth_id)
    new_session, new_refresh_token, refresh_ttl = _create_refresh_session(
        session,
        existing_session.user_auth_id,
    )
    existing_session.revoked_at = _utc_now()
    existing_session.replaced_by_session_id = new_session.id
    session.add(existing_session)
    session.flush()
    return AuthTokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
        access_token_expires_in=access_ttl,
        refresh_token_expires_in=refresh_ttl,
        user_id=existing_session.user_auth_id,
    )


def revoke_refresh_session(session: Session, refresh_token: str) -> None:
    existing_session = _get_valid_refresh_session(session, refresh_token)
    existing_session.revoked_at = _utc_now()
    session.add(existing_session)
    session.flush()


def authenticate_access_token(token: str) -> AuthenticatedUser:
    try:
        decoded = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
    except jwt.InvalidTokenError as exc:
        raise ValueError("Invalid or expired token") from exc

    if decoded.get("type") != "access":
        raise ValueError("Invalid token type")
    uid = decoded.get("sub")
    if not uid:
        raise ValueError("Access token does not contain a subject")
    return AuthenticatedUser(uid=uid, token=decoded)
