from firebase_functions import https_fn
from typing import Dict, Any
import logging
from database.postsql_db_connection import User, get_db_session

logger = logging.getLogger(__name__)

def update_fcm_token(req: https_fn.CallableRequest) -> Dict[str, Any]:
    """
    Update FCM token for a user
    Expected payload: {"fcm_token": "string"}
    """
    try:
        # Get user from Firebase auth
        user_id = req.auth.uid if req.auth else None
        if not user_id:
            return {"success": False, "error": "Authentication required"}
        
        # Get FCM token from request
        fcm_token = req.data.get("fcm_token")
        if not fcm_token:
            return {"success": False, "error": "FCM token is required"}
        
        # Update user's FCM token in database
        with get_db_session() as db:
            user = db.query(User).filter(User.auth_id == user_id).first()
            
            if not user:
                # Create new user if doesn't exist
                user = User(auth_id=user_id, fcm_token=fcm_token)
                db.add(user)
            else:
                # Update existing user's FCM token
                user.fcm_token = fcm_token
                        
        logger.info(f"Updated FCM token for user: {user_id}")
        return {"success": True, "message": "FCM token updated successfully"}
        
    except Exception as e:
        logger.error(f"Error updating FCM token: {e}")
        return {"success": False, "error": "Failed to update FCM token"}

def set_notification_preference(req: https_fn.CallableRequest) -> Dict[str, Any]:
    """
    Set notification preference for a user
    Expected payload: {"isEnabled": boolean, "fcm_token": "string"} (fcm_token optional)
    """
    try:
        # Get user from Firebase auth
        user_id = req.auth.uid if req.auth else None
        if not user_id:
            return {"success": False, "error": "Authentication required"}
        
        # Get isEnabled parameter
        is_enabled = req.data.get("isEnabled")
        if is_enabled is None:
            return {"success": False, "error": "isEnabled parameter is required"}
        
        with get_db_session() as db:
            user = db.query(User).filter(User.auth_id == user_id).first()
            
            if not user:
                # Create new user if doesn't exist
                fcm_token = req.data.get("fcm_token", "")
                user = User(
                    auth_id=user_id, 
                    fcm_token=fcm_token,
                    is_notification_enabled=bool(is_enabled)
                )
                db.add(user)
            else:
                # Update existing user
                user.is_notification_enabled = bool(is_enabled)
                if req.data.get("fcm_token"):
                    user.fcm_token = req.data.get("fcm_token")
                        
        action = "enabled" if is_enabled else "disabled"
        logger.info(f"{action.capitalize()} notifications for user: {user_id}")
        return {
            "success": True, 
            "message": f"Notifications {action} successfully",
            "is_notification_enabled": bool(is_enabled)
        }
        
    except Exception as e:
        logger.error(f"Error setting notification preference: {e}")
        return {"success": False, "error": "Failed to update notification preference"}


