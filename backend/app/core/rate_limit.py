"""
Rate Limiting Middleware
Implements request rate limiting using SlowAPI
"""
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request, Response
from typing import Callable

from config import settings


def get_client_identifier(request: Request) -> str:
    """
    Get client identifier for rate limiting
    
    Priority:
    1. User ID from JWT token (if authenticated)
    2. IP address (for unauthenticated requests)
    
    This allows per-user rate limiting for authenticated users
    and per-IP rate limiting for anonymous users.
    """
    # Try to get user ID from request state (set by auth middleware)
    if hasattr(request.state, "user") and request.state.user:
        user_id = request.state.user.get("id")
        if user_id:
            return f"user:{user_id}"
    
    # Fallback to IP address
    return get_remote_address(request)


def get_storage_uri() -> str:
    """
    Get storage URI for rate limiting
    
    Returns:
        Storage URI string (Redis or in-memory)
    """
    # For MVP, use in-memory storage
    # In production with Redis configured, this can be updated
    # to use Redis for distributed rate limiting
    
    # Use memory storage for now (simpler for MVP)
    # TODO: Integrate with Redis when Redis client is set up (Task 5.5)
    return "memory://"


# Create limiter instance
limiter = Limiter(
    key_func=get_client_identifier,
    default_limits=[f"{settings.rate_limit_per_minute}/minute"],
    storage_uri=get_storage_uri(),
    strategy="fixed-window",
    headers_enabled=True,  # Add rate limit headers to responses
)


def setup_rate_limiting(app) -> None:
    """
    Configure rate limiting for the FastAPI application
    
    Args:
        app: FastAPI application instance
    """
    # Add rate limit exceeded handler
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    
    # Log configuration
    if settings.debug:
        print(f"⏱️  Rate limiting configured:")
        print(f"   - Limit: {settings.rate_limit_per_minute} requests/minute")
        print(f"   - Strategy: fixed-window")
        print(f"   - Storage: Memory (in-process)")
        print(f"   - Note: Redis integration pending (Task 5.5)")

