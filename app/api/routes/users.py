from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.api.deps import get_current_user, get_db_session
from app.schemas import (
    FCMTokenUpdateRequest,
    MessageResponse,
    NotificationPreferenceRequest,
    NotificationPreferenceResponse,
)
from app.services.auth import AuthenticatedUser
from app.services.article_repository import (
    set_user_notification_preference,
    update_user_fcm_token,
)

router = APIRouter(prefix="/users/me", tags=["users"])


@router.post("/fcm-token", response_model=MessageResponse)
def update_fcm_token(
    payload: FCMTokenUpdateRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> MessageResponse:
    update_user_fcm_token(session, current_user.uid, payload.fcm_token)
    return MessageResponse(message="FCM token updated successfully")


@router.post("/notification-preference", response_model=NotificationPreferenceResponse)
def set_notification_preference(
    payload: NotificationPreferenceRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> NotificationPreferenceResponse:
    user = set_user_notification_preference(
        session,
        auth_id=current_user.uid,
        is_enabled=payload.is_enabled,
        fcm_token=payload.fcm_token,
    )
    action = "enabled" if user.is_notification_enabled else "disabled"
    return NotificationPreferenceResponse(
        message=f"Notifications {action} successfully",
        is_notification_enabled=user.is_notification_enabled,
    )
