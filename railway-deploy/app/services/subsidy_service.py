"""
Subsidy Eligibility Service for Hedera Flow MVP

Manages user subsidy eligibility verification and checks.
For MVP, subsidy verification is a manual admin process (no automated income verification).

Requirements: FR-4.5 (System shall apply subsidies if user eligible)
"""
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import and_
import logging

from app.models.user import User

logger = logging.getLogger(__name__)


class SubsidyServiceError(Exception):
    """Raised when subsidy service operations fail"""
    pass


def check_user_eligibility(
    db: Session,
    user_id: str
) -> Dict[str, Any]:
    """
    Check if a user is currently eligible for subsidies.
    
    Args:
        db: Database session
        user_id: User UUID
    
    Returns:
        Dictionary containing:
            - eligible: Boolean indicating if user is eligible
            - subsidy_type: Type of subsidy (if eligible)
            - verified_at: When eligibility was verified
            - expires_at: When eligibility expires
            - expired: Boolean indicating if eligibility has expired
    
    Raises:
        SubsidyServiceError: If user not found or check fails
    """
    try:
        # Fetch user from database
        user = db.query(User).filter(User.id == user_id).first()
        
        if not user:
            raise SubsidyServiceError(f"User not found: {user_id}")
        
        # Check if user has subsidy eligibility flag
        if not user.subsidy_eligible:
            return {
                'eligible': False,
                'subsidy_type': None,
                'verified_at': None,
                'expires_at': None,
                'expired': False,
                'reason': 'User not marked as subsidy eligible'
            }
        
        # Check if eligibility has expired
        now = datetime.now(timezone.utc)
        expired = False
        
        if user.subsidy_expires_at:
            expired = user.subsidy_expires_at < now
        
        if expired:
            return {
                'eligible': False,
                'subsidy_type': user.subsidy_type,
                'verified_at': user.subsidy_verified_at,
                'expires_at': user.subsidy_expires_at,
                'expired': True,
                'reason': f'Subsidy eligibility expired on {user.subsidy_expires_at.isoformat()}'
            }
        
        # User is eligible
        return {
            'eligible': True,
            'subsidy_type': user.subsidy_type,
            'verified_at': user.subsidy_verified_at,
            'expires_at': user.subsidy_expires_at,
            'expired': False,
            'reason': None
        }
        
    except SubsidyServiceError:
        raise
    except Exception as e:
        logger.error(f"Error checking user eligibility: {e}", exc_info=True)
        raise SubsidyServiceError(f"Failed to check eligibility: {str(e)}")


def set_user_eligibility(
    db: Session,
    user_id: str,
    eligible: bool,
    subsidy_type: Optional[str] = None,
    expires_at: Optional[datetime] = None
) -> Dict[str, Any]:
    """
    Set user subsidy eligibility (admin/manual process for MVP).
    
    Args:
        db: Database session
        user_id: User UUID
        eligible: Whether user is eligible for subsidies
        subsidy_type: Type of subsidy (low_income, senior_citizen, disability, energy_efficiency)
        expires_at: When eligibility expires (optional, None = no expiration)
    
    Returns:
        Dictionary containing updated eligibility status
    
    Raises:
        SubsidyServiceError: If user not found or update fails
    """
    try:
        # Fetch user from database
        user = db.query(User).filter(User.id == user_id).first()
        
        if not user:
            raise SubsidyServiceError(f"User not found: {user_id}")
        
        # Validate subsidy type if eligible
        valid_types = ['low_income', 'senior_citizen', 'disability', 'energy_efficiency']
        if eligible and subsidy_type and subsidy_type not in valid_types:
            raise SubsidyServiceError(
                f"Invalid subsidy type: {subsidy_type}. Must be one of: {', '.join(valid_types)}"
            )
        
        # Update user eligibility
        user.subsidy_eligible = eligible
        user.subsidy_type = subsidy_type if eligible else None
        user.subsidy_verified_at = datetime.now(timezone.utc) if eligible else None
        user.subsidy_expires_at = expires_at if eligible else None
        
        # Commit changes
        db.commit()
        db.refresh(user)
        
        logger.info(
            f"Updated subsidy eligibility for user {user_id}: "
            f"eligible={eligible}, type={subsidy_type}, expires={expires_at}"
        )
        
        return {
            'user_id': str(user.id),
            'eligible': user.subsidy_eligible,
            'subsidy_type': user.subsidy_type,
            'verified_at': user.subsidy_verified_at,
            'expires_at': user.subsidy_expires_at
        }
        
    except SubsidyServiceError:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error setting user eligibility: {e}", exc_info=True)
        raise SubsidyServiceError(f"Failed to set eligibility: {str(e)}")


def get_applicable_subsidies(
    db: Session,
    user_id: str,
    country_code: str,
    utility_provider: str
) -> List[Dict[str, Any]]:
    """
    Get applicable subsidies for a user based on their eligibility and location.
    
    This function would typically query a subsidies database table, but for MVP
    it returns subsidies from the tariff data if user is eligible.
    
    Args:
        db: Database session
        user_id: User UUID
        country_code: Country code (ES, US, IN, BR, NG)
        utility_provider: Utility provider name
    
    Returns:
        List of applicable subsidy dictionaries
    
    Raises:
        SubsidyServiceError: If check fails
    """
    try:
        # Check user eligibility
        eligibility = check_user_eligibility(db, user_id)
        
        if not eligibility['eligible']:
            return []
        
        # For MVP, subsidies are defined in tariff data
        # In production, this would query a separate subsidies table
        # filtered by country, utility provider, and subsidy type
        
        # Return empty list for now - subsidies come from tariff data
        # This function is a placeholder for future enhancement
        return []
        
    except SubsidyServiceError:
        raise
    except Exception as e:
        logger.error(f"Error getting applicable subsidies: {e}", exc_info=True)
        raise SubsidyServiceError(f"Failed to get subsidies: {str(e)}")


def revoke_user_eligibility(
    db: Session,
    user_id: str,
    reason: Optional[str] = None
) -> Dict[str, Any]:
    """
    Revoke user subsidy eligibility.
    
    Args:
        db: Database session
        user_id: User UUID
        reason: Optional reason for revocation
    
    Returns:
        Dictionary containing updated eligibility status
    
    Raises:
        SubsidyServiceError: If user not found or revocation fails
    """
    try:
        # Use set_user_eligibility to revoke
        result = set_user_eligibility(
            db=db,
            user_id=user_id,
            eligible=False,
            subsidy_type=None,
            expires_at=None
        )
        
        logger.info(f"Revoked subsidy eligibility for user {user_id}. Reason: {reason}")
        
        return result
        
    except SubsidyServiceError:
        raise
    except Exception as e:
        logger.error(f"Error revoking user eligibility: {e}", exc_info=True)
        raise SubsidyServiceError(f"Failed to revoke eligibility: {str(e)}")
