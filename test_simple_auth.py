#!/usr/bin/env python3
"""
Simple test for authentication endpoints
"""
import requests
import json

# Configuration
BASE_URL = "http://localhost:8000/api"

def test_auth_endpoints():
    """Test authentication endpoints"""
    print("🔐 Testing Authentication Endpoints")
    print("=" * 40)
    
    session = requests.Session()
    
    # Test 1: Check if server is running
    print("\n1. Testing Server Health...")
    try:
        response = session.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            print("✅ Server is running")
            print(f"   Response: {response.json()}")
        else:
            print(f"❌ Server health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Server not reachable: {e}")
        return False
    
    # Test 2: Try to register a new user
    print("\n2. Testing Registration...")
    test_email = "testuser123@example.com"
    register_data = {
        "first_name": "Test",
        "last_name": "User",
        "email": test_email,
        "password": "TestPass123",
        "country_code": "ES"
    }
    
    try:
        response = session.post(f"{BASE_URL}/auth/register", json=register_data)
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text[:200]}...")
        print(f"   Cookies: {list(response.cookies.keys())}")
        
        if response.status_code == 201:
            print("✅ Registration successful")
            return True
        elif response.status_code == 400 and "already exists" in response.text:
            print("ℹ️  User already exists, trying login...")
            
            # Try login
            login_data = {"username": test_email, "password": "TestPass123"}
            response = session.post(f"{BASE_URL}/auth/login", data=login_data)
            print(f"   Login Status: {response.status_code}")
            print(f"   Login Response: {response.text[:200]}...")
            print(f"   Login Cookies: {list(response.cookies.keys())}")
            
            if response.status_code == 200:
                print("✅ Login successful")
                return True
            else:
                print("❌ Login failed")
                return False
        else:
            print("❌ Registration failed")
            return False
            
    except Exception as e:
        print(f"❌ Registration error: {e}")
        return False

if __name__ == "__main__":
    test_auth_endpoints()