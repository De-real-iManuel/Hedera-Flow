"""
Custom Exception Classes and Handlers
Comprehensive error handling middleware for Hedera Flow API
"""
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError, HTTPException
from starlette.exceptions import HTTPException as StarletteHTTPException
from pydantic import ValidationError as PydanticValidationError
import logging
import traceback
import sys
from datetime import datetime
from typing import Optional, Dict, Any

from config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO if not settings.debug else logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class HederaFlowException(Exception):
    """Base exception for Hedera Flow application"""
    def __init__(
        self, 
        message: str, 
        status_code: int = 500,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}
        super().__init__(self.message)


class AuthenticationError(HederaFlowException):
    """Authentication failed"""
    def __init__(self, message: str = "Authentication failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=401, error_code="AUTH_FAILED", details=details)


class AuthorizationError(HederaFlowException):
    """User not authorized"""
    def __init__(self, message: str = "Not authorized", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=403, error_code="FORBIDDEN", details=details)


class NotFoundError(HederaFlowException):
    """Resource not found"""
    def __init__(self, message: str = "Resource not found", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=404, error_code="NOT_FOUND", details=details)


class ConflictError(HederaFlowException):
    """Resource conflict"""
    def __init__(self, message: str = "Resource conflict", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=409, error_code="CONFLICT", details=details)


class ValidationError(HederaFlowException):
    """Validation error"""
    def __init__(self, message: str = "Validation failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=400, error_code="VALIDATION_ERROR", details=details)


class HederaNetworkError(HederaFlowException):
    """Hedera network error"""
    def __init__(self, message: str = "Hedera network error", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=503, error_code="HEDERA_ERROR", details=details)


class DatabaseError(HederaFlowException):
    """Database error"""
    def __init__(self, message: str = "Database error", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=500, error_code="DATABASE_ERROR", details=details)


class RateLimitError(HederaFlowException):
    """Rate limit exceeded"""
    def __init__(self, message: str = "Rate limit exceeded", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=429, error_code="RATE_LIMIT_EXCEEDED", details=details)


class ExternalServiceError(HederaFlowException):
    """External service error (OCR, IPFS, etc.)"""
    def __init__(self, message: str = "External service error", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=503, error_code="EXTERNAL_SERVICE_ERROR", details=details)


def create_error_response(
    error_code: str,
    message: str,
    status_code: int,
    path: str,
    details: Optional[Dict[str, Any]] = None,
    request_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create standardized error response
    
    Args:
        error_code: Machine-readable error code
        message: Human-readable error message
        status_code: HTTP status code
        path: Request path
        details: Additional error details
        request_id: Request tracking ID
    
    Returns:
        Standardized error response dictionary
    """
    response = {
        "error": {
            "code": error_code,
            "message": message,
            "status": status_code,
            "timestamp": datetime.utcnow().isoformat(),
            "path": path
        }
    }
    
    if details:
        response["error"]["details"] = details
    
    if request_id:
        response["error"]["request_id"] = request_id
    
    # Include stack trace in debug mode
    if settings.debug and "traceback" in (details or {}):
        response["error"]["traceback"] = details["traceback"]
    
    return response


def setup_exception_handlers(app: FastAPI) -> None:
    """
    Setup comprehensive global exception handlers
    Handles all types of errors with proper logging and user-friendly responses
    """
    
    @app.exception_handler(HederaFlowException)
    async def hedera_flow_exception_handler(
        request: Request,
        exc: HederaFlowException
    ):
        """Handle custom application exceptions"""
        # Log the error
        logger.warning(
            f"Application error: {exc.error_code} - {exc.message}",
            extra={
                "error_code": exc.error_code,
                "status_code": exc.status_code,
                "path": str(request.url),
                "method": request.method,
                "details": exc.details
            }
        )
        
        # Create error response
        response = create_error_response(
            error_code=exc.error_code,
            message=exc.message,
            status_code=exc.status_code,
            path=str(request.url.path),
            details=exc.details if exc.details else None,
            request_id=request.headers.get("X-Request-ID")
        )
        
        return JSONResponse(
            status_code=exc.status_code,
            content=response
        )
    
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request,
        exc: RequestValidationError
    ):
        """Handle request validation errors (Pydantic)"""
        # Extract validation errors
        errors = []
        for error in exc.errors():
            errors.append({
                "field": ".".join(str(loc) for loc in error["loc"]),
                "message": error["msg"],
                "type": error["type"]
            })
        
        # Log validation error
        logger.info(
            f"Validation error on {request.method} {request.url.path}",
            extra={
                "errors": errors,
                "method": request.method,
                "path": str(request.url)
            }
        )
        
        # Create error response
        response = create_error_response(
            error_code="VALIDATION_ERROR",
            message="Request validation failed",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            path=str(request.url.path),
            details={"validation_errors": errors},
            request_id=request.headers.get("X-Request-ID")
        )
        
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=response
        )
    
    @app.exception_handler(HTTPException)
    async def http_exception_handler(
        request: Request,
        exc: HTTPException
    ):
        """Handle FastAPI HTTPException"""
        # Log HTTP exception
        logger.info(
            f"HTTP exception: {exc.status_code} - {exc.detail}",
            extra={
                "status_code": exc.status_code,
                "detail": exc.detail,
                "path": str(request.url),
                "method": request.method
            }
        )
        
        # Create error response
        response = create_error_response(
            error_code=f"HTTP_{exc.status_code}",
            message=str(exc.detail),
            status_code=exc.status_code,
            path=str(request.url.path),
            request_id=request.headers.get("X-Request-ID")
        )
        
        return JSONResponse(
            status_code=exc.status_code,
            content=response
        )
    
    @app.exception_handler(StarletteHTTPException)
    async def starlette_http_exception_handler(
        request: Request,
        exc: StarletteHTTPException
    ):
        """Handle Starlette HTTPException (e.g., 404 for unknown routes)"""
        # Log HTTP exception
        logger.info(
            f"Starlette HTTP exception: {exc.status_code} - {exc.detail}",
            extra={
                "status_code": exc.status_code,
                "detail": exc.detail,
                "path": str(request.url),
                "method": request.method
            }
        )
        
        # Create error response
        response = create_error_response(
            error_code=f"HTTP_{exc.status_code}",
            message=str(exc.detail),
            status_code=exc.status_code,
            path=str(request.url.path),
            request_id=request.headers.get("X-Request-ID")
        )
        
        return JSONResponse(
            status_code=exc.status_code,
            content=response
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(
        request: Request,
        exc: Exception
    ):
        """Handle unexpected exceptions"""
        # Get traceback
        tb = traceback.format_exc()
        
        # Log the exception with full traceback
        logger.error(
            f"Unexpected error: {exc.__class__.__name__} - {str(exc)}",
            extra={
                "exception_type": exc.__class__.__name__,
                "exception_message": str(exc),
                "path": str(request.url),
                "method": request.method,
                "traceback": tb
            },
            exc_info=True
        )
        
        # Create error response
        details = None
        if settings.debug:
            details = {
                "exception_type": exc.__class__.__name__,
                "exception_message": str(exc),
                "traceback": tb.split("\n")
            }
        
        response = create_error_response(
            error_code="INTERNAL_SERVER_ERROR",
            message="An unexpected error occurred. Please try again later.",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            path=str(request.url.path),
            details=details,
            request_id=request.headers.get("X-Request-ID")
        )
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=response
        )
