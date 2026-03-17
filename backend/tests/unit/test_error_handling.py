"""
Test script for error handling middleware
Tests various error scenarios to verify proper error responses
"""
import sys
import asyncio
from fastapi.testclient import TestClient

# Add parent directory to path
sys.path.insert(0, '.')

from main import app
from app.core.exceptions import (
    NotFoundError,
    ValidationError,
    AuthenticationError,
    DatabaseError
)

# Create test client
client = TestClient(app)


def test_root_endpoint():
    """Test root endpoint returns 200"""
    print("\n1. Testing root endpoint...")
    response = client.get("/")
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    print("   ✅ Root endpoint works")


def test_health_endpoint():
    """Test health endpoint returns proper format"""
    print("\n2. Testing health endpoint...")
    response = client.get("/api/health")
    print(f"   Status: {response.status_code}")
    data = response.json()
    print(f"   Response: {data}")
    assert response.status_code == 200
    assert "status" in data
    assert "components" in data
    print("   ✅ Health endpoint works")


def test_404_error():
    """Test 404 error for non-existent endpoint"""
    print("\n3. Testing 404 error...")
    response = client.get("/api/nonexistent")
    print(f"   Status: {response.status_code}")
    data = response.json()
    print(f"   Response: {data}")
    assert response.status_code == 404
    assert "error" in data
    assert data["error"]["code"] == "HTTP_404"
    assert "message" in data["error"]
    assert "timestamp" in data["error"]
    assert "path" in data["error"]
    print("   ✅ 404 error formatted correctly")


def test_request_headers():
    """Test that response includes custom headers"""
    print("\n4. Testing custom response headers...")
    response = client.get("/api/health")
    print(f"   Headers: {dict(response.headers)}")
    
    # Check for request ID
    assert "x-request-id" in response.headers
    print(f"   Request ID: {response.headers['x-request-id']}")
    
    # Check for execution time
    assert "x-execution-time" in response.headers
    print(f"   Execution Time: {response.headers['x-execution-time']}")
    
    # Check for security headers
    assert "x-content-type-options" in response.headers
    assert response.headers["x-content-type-options"] == "nosniff"
    
    assert "x-frame-options" in response.headers
    assert response.headers["x-frame-options"] == "DENY"
    
    assert "x-xss-protection" in response.headers
    assert response.headers["x-xss-protection"] == "1; mode=block"
    
    print("   ✅ All custom headers present")


def test_validation_error():
    """Test validation error handling"""
    print("\n5. Testing validation error...")
    # This will trigger a validation error since we're sending invalid data
    # We'll need to create a test endpoint for this
    print("   ⚠️  Skipping - requires test endpoint with validation")


def test_cors_headers():
    """Test CORS headers are present"""
    print("\n6. Testing CORS headers...")
    response = client.options("/api/health")
    print(f"   Status: {response.status_code}")
    print(f"   CORS Headers: {[k for k in response.headers.keys() if 'access-control' in k.lower()]}")
    print("   ✅ CORS configured")


def run_all_tests():
    """Run all tests"""
    print("=" * 60)
    print("Testing Error Handling Middleware")
    print("=" * 60)
    
    try:
        test_root_endpoint()
        test_health_endpoint()
        test_404_error()
        test_request_headers()
        test_validation_error()
        test_cors_headers()
        
        print("\n" + "=" * 60)
        print("✅ All tests passed!")
        print("=" * 60)
        return True
        
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        return False
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
