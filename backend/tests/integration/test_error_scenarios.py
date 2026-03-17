"""
Comprehensive error handling test scenarios
Demonstrates all error types and response formats
"""
from fastapi import FastAPI, Request, APIRouter
from fastapi.testclient import TestClient
import sys

sys.path.insert(0, '.')

from app.core.exceptions import (
    NotFoundError,
    ValidationError,
    AuthenticationError,
    AuthorizationError,
    ConflictError,
    DatabaseError,
    HederaNetworkError,
    RateLimitError,
    ExternalServiceError
)
from app.core.middleware import ErrorHandlingMiddleware, SecurityHeadersMiddleware

# Create test app with error handling
app = FastAPI()
app.add_middleware(ErrorHandlingMiddleware)
app.add_middleware(SecurityHeadersMiddleware)

# Import exception handlers
from app.core.exceptions import setup_exception_handlers
setup_exception_handlers(app)

# Create test router
router = APIRouter()


@router.get("/test/not-found")
async def test_not_found():
    """Test NotFoundError"""
    raise NotFoundError("User not found")


@router.get("/test/validation")
async def test_validation():
    """Test ValidationError"""
    raise ValidationError(
        message="Invalid meter ID format",
        details={
            "field": "meter_id",
            "expected": "XXX-12345678",
            "received": "invalid"
        }
    )


@router.get("/test/authentication")
async def test_authentication():
    """Test AuthenticationError"""
    raise AuthenticationError("Invalid credentials")


@router.get("/test/authorization")
async def test_authorization():
    """Test AuthorizationError"""
    raise AuthorizationError("Insufficient permissions")


@router.get("/test/conflict")
async def test_conflict():
    """Test ConflictError"""
    raise ConflictError("Meter already registered")


@router.get("/test/database")
async def test_database():
    """Test DatabaseError"""
    raise DatabaseError(
        message="Failed to connect to database",
        details={"host": "localhost", "port": 5432}
    )


@router.get("/test/hedera")
async def test_hedera():
    """Test HederaNetworkError"""
    raise HederaNetworkError("Failed to submit transaction")


@router.get("/test/rate-limit")
async def test_rate_limit():
    """Test RateLimitError"""
    raise RateLimitError("Too many requests")


@router.get("/test/external-service")
async def test_external_service():
    """Test ExternalServiceError"""
    raise ExternalServiceError(
        message="OCR service unavailable",
        details={"service": "Google Vision API", "status": 503}
    )


@router.get("/test/unexpected")
async def test_unexpected():
    """Test unexpected exception"""
    raise ValueError("Something went wrong")


# Include router
app.include_router(router)

# Create test client
client = TestClient(app)


def print_error_response(name: str, response):
    """Pretty print error response"""
    print(f"\n{name}")
    print("=" * 60)
    print(f"Status Code: {response.status_code}")
    print(f"Response:")
    import json
    print(json.dumps(response.json(), indent=2))
    print(f"Headers:")
    print(f"  - Request ID: {response.headers.get('x-request-id', 'N/A')}")
    print(f"  - Execution Time: {response.headers.get('x-execution-time', 'N/A')}")
    print(f"  - Security Headers: {response.headers.get('x-content-type-options', 'N/A')}")


def run_tests():
    """Run all error scenario tests"""
    print("\n" + "=" * 60)
    print("ERROR HANDLING TEST SCENARIOS")
    print("=" * 60)
    
    # Test all error types
    tests = [
        ("1. NotFoundError (404)", "/test/not-found", 404),
        ("2. ValidationError (400)", "/test/validation", 400),
        ("3. AuthenticationError (401)", "/test/authentication", 401),
        ("4. AuthorizationError (403)", "/test/authorization", 403),
        ("5. ConflictError (409)", "/test/conflict", 409),
        ("6. DatabaseError (500)", "/test/database", 500),
        ("7. HederaNetworkError (503)", "/test/hedera", 503),
        ("8. RateLimitError (429)", "/test/rate-limit", 429),
        ("9. ExternalServiceError (503)", "/test/external-service", 503),
        ("10. Unexpected Exception (500)", "/test/unexpected", 500),
    ]
    
    for name, endpoint, expected_status in tests:
        response = client.get(endpoint)
        print_error_response(name, response)
        
        # Verify response format
        assert response.status_code == expected_status, f"Expected {expected_status}, got {response.status_code}"
        data = response.json()
        assert "error" in data, "Missing 'error' field"
        assert "code" in data["error"], "Missing 'code' field"
        assert "message" in data["error"], "Missing 'message' field"
        assert "status" in data["error"], "Missing 'status' field"
        assert "timestamp" in data["error"], "Missing 'timestamp' field"
        assert "path" in data["error"], "Missing 'path' field"
        
        # Verify headers
        assert "x-request-id" in response.headers, "Missing X-Request-ID header"
        assert "x-execution-time" in response.headers, "Missing X-Execution-Time header"
        assert "x-content-type-options" in response.headers, "Missing security headers"
    
    print("\n" + "=" * 60)
    print("✅ ALL ERROR SCENARIOS TESTED SUCCESSFULLY")
    print("=" * 60)
    print("\nKey Features Verified:")
    print("  ✅ Standardized error response format")
    print("  ✅ Proper HTTP status codes")
    print("  ✅ Request ID tracking")
    print("  ✅ Execution time tracking")
    print("  ✅ Security headers")
    print("  ✅ Error details and context")
    print("  ✅ Timestamp tracking")
    print("  ✅ Path information")


if __name__ == "__main__":
    try:
        run_tests()
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
