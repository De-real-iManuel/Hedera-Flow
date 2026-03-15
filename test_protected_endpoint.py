#!/usr/bin/env python3
"""
Test protected endpoint with cookies
"""
import requests

def test_protected_access():
    """Test accessing protected endpoint after login"""
    print("🔒 Testing Protected Endpoint Access")
    print("=" * 40)
    
    session = requests.Session()
    
    # Step 1: Login to get cookies
    print("\n1. Logging in...")
    login_data = {"username": "testuser123@example.com", "password": "TestPass123"}
    
    try:
        response = session.post("http://localhost:8000/api/auth/login", data=login_data)
        print(f"   Login Status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Login successful")
            print(f"   Cookies received: {list(response.cookies.keys())}")
        else:
            print(f"❌ Login failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Login error: {e}")
        return False
    
    # Step 2: Access protected endpoint
    print("\n2. Accessing protected endpoint...")
    try:
        response = session.get("http://localhost:8000/api/auth/me")
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Protected endpoint accessible")
            user_data = response.json()
            print(f"   User: {user_data.get('email')}")
        else:
            print(f"❌ Protected endpoint failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Protected endpoint error: {e}")
        return False
    
    # Step 3: Test token refresh
    print("\n3. Testing token refresh...")
    try:
        response = session.post("http://localhost:8000/api/auth/refresh-token")
        print(f"   Refresh Status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Token refresh successful")
            print(f"   New cookies: {list(response.cookies.keys())}")
        else:
            print(f"❌ Token refresh failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Token refresh error: {e}")
        return False
    
    # Step 4: Test logout
    print("\n4. Testing logout...")
    try:
        response = session.post("http://localhost:8000/api/auth/logout")
        print(f"   Logout Status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Logout successful")
        else:
            print(f"❌ Logout failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Logout error: {e}")
        return False
    
    # Step 5: Verify access is denied after logout
    print("\n5. Verifying access denied after logout...")
    try:
        response = session.get("http://localhost:8000/api/auth/me")
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 401:
            print("✅ Access properly denied after logout")
        else:
            print(f"❌ Still have access after logout: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Post-logout test error: {e}")
        return False
    
    print("\n🎉 All tests passed!")
    return True

if __name__ == "__main__":
    test_protected_access()