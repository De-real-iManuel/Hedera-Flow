"""
Test script to verify FastAPI application structure
Run this to ensure all modules are properly configured
"""
import sys
from pathlib import Path

def test_imports():
    """Test that all core modules can be imported"""
    print("Testing module imports...")
    
    try:
        # Test config
        from config import settings
        print("✓ Config module imported successfully")
        print(f"  Environment: {settings.environment}")
        
        # Test core modules
        from app.core.app import create_app
        print("✓ App factory imported successfully")
        
        from app.core.exceptions import (
            HederaFlowException,
            AuthenticationError,
            NotFoundError
        )
        print("✓ Exception classes imported successfully")
        
        from app.core.dependencies import get_current_user
        print("✓ Dependencies imported successfully")
        
        # Test API modules
        from app.api.routes import api_router
        print("✓ API router imported successfully")
        
        from app.api.endpoints import health
        print("✓ Health endpoints imported successfully")
        
        print("\n✅ All imports successful!")
        return True
        
    except Exception as e:
        print(f"\n❌ Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_app_creation():
    """Test that the FastAPI app can be created"""
    print("\nTesting app creation...")
    
    try:
        from app.core.app import create_app
        app = create_app()
        
        print("✓ FastAPI app created successfully")
        print(f"  Title: {app.title}")
        print(f"  Version: {app.version}")
        print(f"  Routes: {len(app.routes)}")
        
        # List all routes
        print("\n  Available routes:")
        for route in app.routes:
            if hasattr(route, 'path') and hasattr(route, 'methods'):
                methods = ', '.join(route.methods) if route.methods else 'N/A'
                print(f"    {methods:10} {route.path}")
        
        print("\n✅ App creation successful!")
        return True
        
    except Exception as e:
        print(f"\n❌ App creation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_exception_handling():
    """Test custom exception classes"""
    print("\nTesting exception handling...")
    
    try:
        from app.core.exceptions import (
            AuthenticationError,
            NotFoundError,
            ConflictError
        )
        
        # Test exception creation
        auth_error = AuthenticationError("Test auth error")
        assert auth_error.status_code == 401
        print("✓ AuthenticationError works correctly")
        
        not_found = NotFoundError("Test not found")
        assert not_found.status_code == 404
        print("✓ NotFoundError works correctly")
        
        conflict = ConflictError("Test conflict")
        assert conflict.status_code == 409
        print("✓ ConflictError works correctly")
        
        print("\n✅ Exception handling successful!")
        return True
        
    except Exception as e:
        print(f"\n❌ Exception handling failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("=" * 60)
    print("FastAPI Application Structure Test")
    print("=" * 60)
    
    results = []
    
    # Run tests
    results.append(("Module Imports", test_imports()))
    results.append(("App Creation", test_app_creation()))
    results.append(("Exception Handling", test_exception_handling()))
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name:30} {status}")
    
    all_passed = all(result[1] for result in results)
    
    if all_passed:
        print("\n🎉 All tests passed! Application structure is ready.")
        return 0
    else:
        print("\n⚠️  Some tests failed. Please check the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
