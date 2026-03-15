"""
User Profile Endpoints
API endpoints for user profile management, preferences, and settings
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any
import logging

from app.core.dependencies import get_db, get_current_user
from app.models.user import User
from app.schemas.user_preferences import (
    UserPreferences,
    NotificationPreferences,
    SecuritySettings,
    UpdateProfileRequest,
    UserProfileResponse
)

logger = logging.getLogger(__name__)
router = APIRouter()


def get_default_preferences() -> Dict[str, Any]:
    """Get default user preferences"""
    return {
        "theme": "light",
        "language": "en",
        "currency_display": "local",
        "notifications": {
            "bill_reminders": True,
            "payment_confirmations": True,
            "subsidy_updates": True,
            "email_notifications": True,
            "push_notifications": False
        }
    }


def get_default_security() -> Dict[str, Any]:
    """Get default security settings"""
    return {
        "biometric_enabled": False,
        "pin_enabled": False,
        "two_factor_enabled": False
    }


@router.get("/profile", response_model=UserProfileResponse)
async def get_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get current user's full profile including preferences and security settings
    
    Returns:
        UserProfileResponse with complete profile data
    """
    try:
        # Ensure preferences and security settings exist
        preferences = current_user.preferences or get_default_preferences()
        security = current_user.security_settings or get_default_security()
        
        return UserProfileResponse(
            id=str(current_user.id),
            email=current_user.email,
            first_name=current_user.first_name,
            last_name=current_user.last_name,
            country_code=current_user.country_code.value if hasattr(current_user.country_code, 'value') else current_user.country_code,
            hedera_account_id=current_user.hedera_account_id,
            wallet_type=current_user.wallet_type.value if current_user.wallet_type and hasattr(current_user.wallet_type, 'value') else current_user.wallet_type,
            created_at=current_user.created_at,
            last_login=current_user.last_login,
            is_active=current_user.is_active,
            preferences=UserPreferences(**preferences),
            security=SecuritySettings(**security)
        )
    except Exception as e:
        logger.error(f"Failed to get user profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve profile"
        )


@router.put("/profile", response_model=UserProfileResponse)
async def update_profile(
    request: UpdateProfileRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update user profile information
    
    Args:
        request: Profile update data
        
    Returns:
        Updated user profile
    """
    try:
        # Update fields if provided
        if request.first_name is not None:
            current_user.first_name = request.first_name
        if request.last_name is not None:
            current_user.last_name = request.last_name
        if request.email is not None:
            # Check if email is already taken
            existing = db.query(User).filter(
                User.email == request.email,
                User.id != current_user.id
            ).first()
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already in use"
                )
            current_user.email = request.email
            current_user.is_email_verified = False  # Require re-verification
        
        db.commit()
        db.refresh(current_user)
        
        logger.info(f"Profile updated for user: {current_user.id}")
        
        # Return updated profile
        preferences = current_user.preferences or get_default_preferences()
        security = current_user.security_settings or get_default_security()
        
        return UserProfileResponse(
            id=str(current_user.id),
            email=current_user.email,
            first_name=current_user.first_name,
            last_name=current_user.last_name,
            country_code=current_user.country_code.value if hasattr(current_user.country_code, 'value') else current_user.country_code,
            hedera_account_id=current_user.hedera_account_id,
            wallet_type=current_user.wallet_type.value if current_user.wallet_type and hasattr(current_user.wallet_type, 'value') else current_user.wallet_type,
            created_at=current_user.created_at,
            last_login=current_user.last_login,
            is_active=current_user.is_active,
            preferences=UserPreferences(**preferences),
            security=SecuritySettings(**security)
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to update profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update profile"
        )


@router.get("/preferences", response_model=UserPreferences)
async def get_preferences(
    current_user: User = Depends(get_current_user)
):
    """
    Get user preferences (theme, language, notifications)
    
    Returns:
        User preferences
    """
    preferences = current_user.preferences or get_default_preferences()
    return UserPreferences(**preferences)


@router.put("/preferences", response_model=UserPreferences)
async def update_preferences(
    preferences: UserPreferences,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update user preferences
    
    Args:
        preferences: New preference values
        
    Returns:
        Updated preferences
    """
    try:
        current_user.preferences = preferences.model_dump()
        db.commit()
        
        logger.info(f"Preferences updated for user: {current_user.id}")
        return preferences
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to update preferences: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update preferences"
        )


@router.get("/notifications", response_model=NotificationPreferences)
async def get_notification_preferences(
    current_user: User = Depends(get_current_user)
):
    """
    Get notification preferences
    
    Returns:
        Notification preferences
    """
    preferences = current_user.preferences or get_default_preferences()
    notifications = preferences.get("notifications", get_default_preferences()["notifications"])
    return NotificationPreferences(**notifications)


@router.put("/notifications", response_model=NotificationPreferences)
async def update_notification_preferences(
    notifications: NotificationPreferences,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update notification preferences
    
    Args:
        notifications: New notification settings
        
    Returns:
        Updated notification preferences
    """
    try:
        preferences = current_user.preferences or get_default_preferences()
        preferences["notifications"] = notifications.model_dump()
        current_user.preferences = preferences
        db.commit()
        
        logger.info(f"Notification preferences updated for user: {current_user.id}")
        return notifications
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to update notification preferences: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update notification preferences"
        )


@router.get("/security", response_model=SecuritySettings)
async def get_security_settings(
    current_user: User = Depends(get_current_user)
):
    """
    Get security settings
    
    Returns:
        Security settings
    """
    security = current_user.security_settings or get_default_security()
    return SecuritySettings(**security)


@router.put("/security", response_model=SecuritySettings)
async def update_security_settings(
    security: SecuritySettings,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update security settings
    
    Args:
        security: New security settings
        
    Returns:
        Updated security settings
    """
    try:
        current_user.security_settings = security.model_dump()
        db.commit()
        
        logger.info(f"Security settings updated for user: {current_user.id}")
        return security
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to update security settings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update security settings"
        )
