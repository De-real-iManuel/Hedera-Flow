"""
Custom Middleware for Error Handling and Request Processing
"""
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import time
import logging
import uuid
from typing import Callable

logger = logging.getLogger(__name__)


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for comprehensive error handling and request tracking
    
    Features:
    - Request ID generation for tracking
    - Request/response logging
    - Execution time tracking
    - Error context enrichment
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process each request with error handling and logging
        
        Args:
            request: Incoming HTTP request
            call_next: Next middleware/endpoint in chain
        
        Returns:
            HTTP response
        """
        # Generate unique request ID
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        
        # Add request ID to request state for access in endpoints
        request.state.request_id = request_id
        
        # Start timer
        start_time = time.time()
        
        # Log incoming request
        logger.info(
            f"Incoming request: {request.method} {request.url.path}",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "query_params": str(request.query_params),
                "client_host": request.client.host if request.client else None,
                "user_agent": request.headers.get("user-agent")
            }
        )
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate execution time
            execution_time = time.time() - start_time
            
            # Add custom headers to response
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Execution-Time"] = f"{execution_time:.3f}s"
            
            # Log response
            logger.info(
                f"Request completed: {request.method} {request.url.path} - {response.status_code}",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "execution_time": execution_time
                }
            )
            
            return response
            
        except Exception as exc:
            # Calculate execution time
            execution_time = time.time() - start_time
            
            # Log error with context
            logger.error(
                f"Request failed: {request.method} {request.url.path} - {exc.__class__.__name__}",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "exception_type": exc.__class__.__name__,
                    "exception_message": str(exc),
                    "execution_time": execution_time
                },
                exc_info=True
            )
            
            # Re-raise exception to be handled by exception handlers
            raise


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add security headers to all responses
    
    Headers added:
    - X-Content-Type-Options: nosniff
    - X-Frame-Options: DENY
    - X-XSS-Protection: 1; mode=block
    - Strict-Transport-Security: max-age=31536000; includeSubDomains
    - Content-Security-Policy: default-src 'self'
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Add security headers to response"""
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # Add HSTS header only in production
        if request.url.scheme == "https":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        # Basic CSP (can be customized per route if needed)
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        
        return response


def setup_middleware(app: ASGIApp) -> None:
    """
    Setup all custom middleware
    
    Args:
        app: FastAPI application instance
    """
    # Add error handling middleware
    app.add_middleware(ErrorHandlingMiddleware)
    
    # Add security headers middleware
    app.add_middleware(SecurityHeadersMiddleware)
    
    logger.info("Custom middleware configured successfully")
