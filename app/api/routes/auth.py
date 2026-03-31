from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.api.deps import get_db_session
from app.schemas import (
    AuthLogoutRequest,
    AuthRefreshRequest,
    AuthTokenResponse,
    MessageResponse,
)
from app.services.auth import (
    create_guest_auth_session,
    refresh_auth_session,
    revoke_refresh_session,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/guest", response_model=AuthTokenResponse)
def create_guest_session(
    session: Session = Depends(get_db_session),
) -> AuthTokenResponse:
    return create_guest_auth_session(session)


@router.post("/refresh", response_model=AuthTokenResponse)
def refresh_session(
    payload: AuthRefreshRequest,
    session: Session = Depends(get_db_session),
) -> AuthTokenResponse:
    return refresh_auth_session(session, payload.refresh_token)


@router.post("/logout", response_model=MessageResponse)
def logout_session(
    payload: AuthLogoutRequest,
    session: Session = Depends(get_db_session),
) -> MessageResponse:
    revoke_refresh_session(session, payload.refresh_token)
    return MessageResponse(message="Refresh token revoked successfully")
