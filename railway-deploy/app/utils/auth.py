"""
Authentication Utilities
Password hashing and JWT token management
"""
import bcrypt
import jwt
from datetime import datetime, timedelta
from typing import Dict, Optional
from config import settings


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt with cost factor 12
    
    Args:
        password: Plain text password
        
    Returns:
        Hashed password string
        
    Requirements:
        - NFR-2.2: Passwords shall be hashed with bcrypt (cost factor 12)
    """
    # Generate salt and hash password
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash
    
    Args:
        plain_password: Plain text password to verify
        hashed_password: Hashed password from database
        
    Returns:
        True if password matches, False otherwise
    """
    return bcrypt.checkpw(
        plain_password.encode('utf-8'),
        hashed_password.encode('utf-8')
    )


def create_access_token(
    user_id: str,
    email: str,
    country_code: str,
    hedera_account_id: Optional[str] = None
) -> str:
    """
    Create JWT access token for authenticated user
    
    Args:
        user_id: User's unique identifier
        email: User's email address
        country_code: User's country code
        hedera_account_id: User's Hedera account ID (optional)
        
    Returns:
        JWT token string
        
    Requirements:
        - FR-1.4: System shall use JWT tokens for session management
        - NFR-2.3: JWT tokens shall expire after 30 days
    """
    # Calculate expiration time
    expiration = datetime.utcnow() + timedelta(days=settings.jwt_expiration_days)
    
    # Create token payload
    payload = {
        "sub": user_id,  # Subject (user ID)
        "email": email,
        "country_code": country_code,
        "hedera_account_id": hedera_account_id,
        "exp": int(expiration.timestamp()),  # Expiration time
        "iat": int(datetime.utcnow().timestamp()),  # Issued at
        "type": "access"
    }
    
    # Encode JWT token
    token = jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm
    )
    
    return token


def decode_access_token(token: str) -> Dict:
    """
    Decode and verify JWT access token
    
    Args:
        token: JWT token string
        
    Returns:
        Decoded token payload
        
    Raises:
        jwt.ExpiredSignatureError: If token has expired
        jwt.InvalidTokenError: If token is invalid
    """
    payload = jwt.decode(
        token,
        settings.jwt_secret_key,
        algorithms=[settings.jwt_algorithm]
    )
    return payload


def validate_password_strength(password: str) -> tuple[bool, Optional[str]]:
    """
    Validate password meets security requirements
    
    Args:
        password: Password to validate
        
    Returns:
        Tuple of (is_valid, error_message)
        
    Requirements:
        - FR-1.5: System shall enforce password requirements 
                  (min 8 chars, 1 uppercase, 1 number)
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    if not any(c.isupper() for c in password):
        return False, "Password must contain at least one uppercase letter"
    
    if not any(c.isdigit() for c in password):
        return False, "Password must contain at least one number"
    
    return True, None


def extract_token_from_header(authorization: str) -> Optional[str]:
    """
    Extract JWT token from Authorization header
    
    Args:
        authorization: Authorization header value (e.g., "Bearer <token>")
        
    Returns:
        JWT token string or None if invalid format
    """
    if not authorization:
        return None
    
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None
    
    return parts[1]
