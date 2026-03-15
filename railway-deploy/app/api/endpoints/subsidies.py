"""
Subsidy Eligibility API Endpoints

Provides endpoints for checking and managing user subsidy eligibility.
For MVP, subsidy verification is a manual admin process.

Requirements: FR-4.5 (System shall apply subsidies if user eligible)
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
import logging

from app.core.database import get_db
from app.core.dependencies import get_current_user, get_current_admin_user
from app.models.user import User
from app.services.subsidy_service import (
    check_user_eligibility,
    set_user_eligibility,
    revoke_user_eligibility,
    SubsidyServiceError
)
from app.schemas.subsidies import (
    SubsidyEligibilityResponse,
    SetSubsidyEligibilityRequest,
    SetSubsidyEligibilityResponse
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["subsidies"])


@router.get(
    "/users/me/subsidy-eligibility",
    response_model=SubsidyEligibilityResponse,
    summary="Check current user's subsidy eligibility"
)
async def get_my_subsidy_eligibility(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Check the current user's subsidy eligibility status.
    
    Returns:
        - eligible: Boolean indicating if user is eligible
        - subsidy_type: Type of subsidy (if eligible)
        - verified_at: When eligibility was verified
        - expires_at: When eligibility expires
        - expired: Boolean indicating if eligibility has expired
    
    Requirements: FR-4.5
    """
    try:
        eligibility = check_user_eligibility(db, str(current_user.id))
        
        return SubsidyEligibilityResponse(
            user_id=str(current_user.id),
            eligible=eligibility['eligible'],
            subsidy_type=eligibility.get('subsidy_type'),
            verified_at=eligibility.get('verified_at'),
            expires_at=eligibility.get('expires_at'),
            expired=eligibility.get('expired', False),
            reason=eligibility.get('reason')
        )
        
    except SubsidyServiceError as e:
        logger.error(f"Error checking subsidy eligibility: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check eligibility: {str(e)}"
        )


@router.post(
    "/users/{user_id}/subsidy-eligibility",
    response_model=SetSubsidyEligibilityResponse,
    summary="Set user subsidy eligibility (admin only)"
)
async def set_user_subsidy_eligibility(
    user_id: str,
    request: SetSubsidyEligibilityRequest,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Set user subsidy eligibility (admin only).
    
    For MVP, this is a manual admin process. In production, this would be
    integrated with automated income verification systems.
    
    Args:
        user_id: UUID of user to update
        request: Eligibility details (eligible, subsidy_type, expires_at)
    
    Returns:
        Updated eligibility status
    
    Requirements: FR-4.5
    """
    try:
        result = set_user_eligibility(
            db=db,
            user_id=user_id,
            eligible=request.eligible,
            subsidy_type=request.subsidy_type,
            expires_at=request.expires_at
        )
        
        return SetSubsidyEligibilityResponse(
            user_id=result['user_id'],
            eligible=result['eligible'],
            subsidy_type=result.get('subsidy_type'),
            verified_at=result.get('verified_at'),
            expires_at=result.get('expires_at'),
            message="Subsidy eligibility updated successfully"
        )
        
    except SubsidyServiceError as e:
        logger.error(f"Error setting subsidy eligibility: {e}")
        
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        elif "invalid" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to set eligibility: {str(e)}"
            )


@router.delete(
    "/users/{user_id}/subsidy-eligibility",
    response_model=SetSubsidyEligibilityResponse,
    summary="Revoke user subsidy eligibility (admin only)"
)
async def revoke_user_subsidy_eligibility(
    user_id: str,
    reason: Optional[str] = None,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Revoke user subsidy eligibility (admin only).
    
    Args:
        user_id: UUID of user to revoke eligibility
        reason: Optional reason for revocation
    
    Returns:
        Updated eligibility status
    
    Requirements: FR-4.5
    """
    try:
        result = revoke_user_eligibility(
            db=db,
            user_id=user_id,
            reason=reason
        )
        
        return SetSubsidyEligibilityResponse(
            user_id=result['user_id'],
            eligible=result['eligible'],
            subsidy_type=result.get('subsidy_type'),
            verified_at=result.get('verified_at'),
            expires_at=result.get('expires_at'),
            message=f"Subsidy eligibility revoked. Reason: {reason}" if reason else "Subsidy eligibility revoked"
        )
        
    except SubsidyServiceError as e:
        logger.error(f"Error revoking subsidy eligibility: {e}")
        
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to revoke eligibility: {str(e)}"
            )
