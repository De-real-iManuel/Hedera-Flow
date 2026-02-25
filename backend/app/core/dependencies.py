"""
Authentication Dependencies
FastAPI dependencies for JWT verification and user authentication
"""
from fastapi import Depends, HTTPException, status
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

# HTTP Bearer token security scheme
security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Verify JWT token and return current authenticated user
    
    This dependency can be used to protect routes that require authentication.
    It extracts the JWT token from the Authorization header, verifies it,
    and returns the authenticated user from the database.
    
    Requirements:
        - FR-1.4: System shall use JWT tokens for session management
        - NFR-2.1: All API endpoints shall require authentication (except public pages)
        - NFR-2.3: JWT tokens shall expire after 30 days
    
    Args:
        credentials: HTTP Bearer token from Authorization header
        db: Database session
        
    Returns:
        User: Authenticated user object
        
    Raises:
        HTTPException 401: If token is missing, invalid, or expired
        HTTPException 404: If user not found in database
        
    Example usage:
        @router.get("/protected")
        async def protected_route(current_user: User = Depends(get_current_user)):
            return {"user_id": current_user.id}
    """
    # Check if credentials are provided
    if not credentials:
        logger.warning("Authentication failed: No credentials provided")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = credentials.credentials
    
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
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Optional authentication dependency
    
    Returns the current user if authenticated, or None if not authenticated.
    Useful for routes that have different behavior for authenticated vs anonymous users.
    
    Args:
        credentials: HTTP Bearer token from Authorization header
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
    if not credentials:
        return None
    
    try:
        return await get_current_user(credentials, db)
    except HTTPException:
        # If authentication fails, return None instead of raising exception
        return None
