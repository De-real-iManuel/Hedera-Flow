"""
Authentication Dependencies
FastAPI dependencies for JWT verification and user authentication
"""
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional
import jwt
import logging

from app.core.database import get_db
from app.models.user import User
from app.utils.auth import decode_access_token
from config import settings

logger = logging.getLogger(__name__)

# HTTP Bearer token security scheme (kept for backward compatibility)
security = HTTPBearer(auto_error=False)


async def get_current_user(
    request: Request,
    db: Session = Depends(get_db)
) -> User:
    """
    Verify JWT token from httpOnly cookie (or Authorization header fallback)
    and return current authenticated user.
    """
    # Try cookie first
    token = request.cookies.get("access_token")
    
    # Fallback: Authorization: Bearer <token> header (for cross-origin cookie issues)
    if not token:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
    
    if not token:
        logger.warning("Authentication failed: No access token provided")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        # Decode and verify JWT token
        payload = decode_access_token(token)
        
        # Extract user ID from token payload
        user_id: str = payload.get("sub")
        if user_id is None:
            logger.warning("Authentication failed: Token missing 'sub' claim")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Verify token type
        token_type: str = payload.get("type")
        if token_type != "access":
            logger.warning(f"Authentication failed: Invalid token type '{token_type}'")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
    except HTTPException:
        # Re-raise HTTP exceptions from validation checks
        raise
    except jwt.ExpiredSignatureError:
        logger.warning("Authentication failed: Token has expired")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError as e:
        logger.warning(f"Authentication failed: Invalid token - {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        logger.error(f"Authentication failed: Unexpected error - {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Fetch user from database
    try:
        # Convert user_id string to UUID
        from uuid import UUID
        try:
            user_uuid = UUID(user_id)
        except ValueError:
            logger.warning(f"Authentication failed: Invalid user ID format '{user_id}'")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid user ID in token"
            )
        
        user = db.query(User).filter(User.id == user_uuid).first()
        
        if user is None:
            logger.warning(f"Authentication failed: User {user_id} not found in database")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Check if user account is active
        if not user.is_active:
            logger.warning(f"Authentication failed: User {user_id} account is inactive")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Account is inactive"
            )
        
        logger.info(f"User authenticated successfully: {user.email} (ID: {user.id})")
        return user
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Database error during authentication: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication failed"
        )


async def get_current_user_optional(
    request: Request,
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Optional authentication dependency
    
    Returns the current user if authenticated, or None if not authenticated.
    Useful for routes that have different behavior for authenticated vs anonymous users.
    
    Args:
        request: FastAPI request object to access cookies
        db: Database session
        
    Returns:
        User object if authenticated, None otherwise
        
    Example usage:
        @router.get("/optional-auth")
        async def optional_route(current_user: Optional[User] = Depends(get_current_user_optional)):
            if current_user:
                return {"message": f"Hello {current_user.email}"}
            return {"message": "Hello anonymous user"}
    """
    token = request.cookies.get("access_token")
    if not token:
        return None
    
    try:
        return await get_current_user(request, db)
    except HTTPException:
        # If authentication fails, return None instead of raising exception
        return None


async def get_current_admin_user(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> User:
    """
    Verify that the current user has admin privileges
    
    This dependency can be used to protect admin-only routes.
    For MVP, we check if the user's email is in the admin list.
    In production, this would check a proper role/permission system.
    
    Args:
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        User: Authenticated admin user object
        
    Raises:
        HTTPException 403: If user is not an admin
        
    Example usage:
        @router.post("/admin/action")
        async def admin_action(current_admin: User = Depends(get_current_admin_user)):
            return {"message": "Admin action performed"}
    """
    # For MVP, check if user email is in admin list
    # In production, this would check a proper role/permission system
    admin_emails = settings.ADMIN_EMAILS.split(',') if hasattr(settings, 'ADMIN_EMAILS') else []
    
    if current_user.email not in admin_emails:
        logger.warning(f"Authorization failed: User {current_user.email} is not an admin")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    
    logger.info(f"Admin user authenticated: {current_user.email}")
    return current_user
