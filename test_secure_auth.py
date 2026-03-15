#!/usr/bin/env python3
"""
Test script for secure JWT authentication with httpOnly cookies
"""
import requests
import json
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000/api"
TEST_EMAIL = f"testuser{int(datetime.now().timestamp())}@example.com"  # Unique email
TEST_PASSWORD = "TestPass123"

def test_secure_auth():
    """Test the secure authentication flow"""
    session = requests.Session()
    
    print("🔐 Testing Secure JWT Authentication with httpOnly Cookies")
    print("=" * 60)
    
    # Test 1: Register a new user
    print("\n1. Testing Registration...")
    register_data = {
        "first_name": "Test",
        "last_name": "User", 
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD,
        "country_code": "ES"
    }
    
    try:
        response = session.post(f"{BASE_URL}/auth/register", json=register_data)
        if response.status_code == 201:
            print("✅ Registration successful")
            user_data = response.json()
            print(f"   User: {user_data.get('email')}")
            print(f"   Cookies: {list(response.cookies.keys())}")
        elif response.status_code == 400 and "already exists" in response.text:
            print("ℹ️  User already exists, trying login instead...")
            # Try login instead
            login_data = {"username": TEST_EMAIL, "password": TEST_PASSWORD}
            response = session.post(f"{BASE_URL}/auth/login", data=login_data)
            if response.status_code == 200:
                print("✅ Login successful")
                user_data = response.json()
                print(f"   User: {user_data.get('email')}")
                print(f"   Cookies: {list(response.cookies.keys())}")
            else:
                print(f"❌ Login failed: {response.status_code} - {response.text}")
                return False
        else:
            print(f"❌ Registration failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Registration error: {e}")
        return False
    
    # Test 2: Check if cookies are set
    print("\n2. Testing Cookie Storage...")
    cookies = session.cookies
    if 'access_token' in cookies and 'refresh_token' in cookies:
        print("✅ httpOnly cookies set successfully")
        print(f"   Access token cookie: {'Present' if cookies.get('access_token') else 'Missing'}")
        print(f"   Refresh token cookie: {'Present' if cookies.get('refresh_token') else 'Missing'}")
    else:
        print("❌ httpOnly cookies not set")
        print(f"   Available cookies: {list(cookies.keys())}")
        return False
    
    # Test 3: Access protected endpoint
    print("\n3. Testing Protected Endpoint Access...")
    try:
        response = session.get(f"{BASE_URL}/auth/me")
        if response.status_code == 200:
            print("✅ Protected endpoint accessible with cookies")
            user_data = response.json()
            print(f"   User: {user_data.get('email')}")
        else:
            print(f"❌ Protected endpoint failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Protected endpoint error: {e}")
        return False
    
    # Test 4: Test token refresh
    print("\n4. Testing Token Refresh...")
    try:
        response = session.post(f"{BASE_URL}/auth/refresh-token")
        if response.status_code == 200:
            print("✅ Token refresh successful")
            print(f"   New cookies: {list(response.cookies.keys())}")
        else:
            print(f"❌ Token refresh failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Token refresh error: {e}")
        return False
    
    # Test 5: Test logout
    print("\n5. Testing Logout...")
    try:
        response = session.post(f"{BASE_URL}/auth/logout")
        if response.status_code == 200:
            print("✅ Logout successful")
            print(f"   Response: {response.json()}")
        else:
            print(f"❌ Logout failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Logout error: {e}")
        return False
    
    # Test 6: Verify cookies are cleared
    print("\n6. Testing Cookie Clearance...")
    try:
        response = session.get(f"{BASE_URL}/auth/me")
        if response.status_code == 401:
            print("✅ Cookies cleared successfully - access denied")
        else:
            print(f"❌ Cookies not cleared - still have access: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Cookie clearance test error: {e}")
        return False
    
    print("\n" + "=" * 60)
    print("🎉 All secure authentication tests passed!")
    return True

if __name__ == "__main__":
    test_secure_auth()