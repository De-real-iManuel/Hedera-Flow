#!/usr/bin/env python3
"""
Test script to verify CORS configuration with credentials
"""
import requests

def test_cors_with_credentials():
    """Test CORS configuration with credentials"""
    print("🌐 Testing CORS Configuration with Credentials")
    print("=" * 50)
    
    # Test preflight request
    print("\n1. Testing CORS Preflight Request...")
    try:
        response = requests.options(
            "http://localhost:8000/api/auth/me",
            headers={
                "Origin": "http://localhost:8081",
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "Content-Type"
            }
        )
        
        print(f"   Status: {response.status_code}")
        print(f"   Headers: {dict(response.headers)}")
        
        # Check CORS headers
        cors_headers = {
            "Access-Control-Allow-Origin": response.headers.get("Access-Control-Allow-Origin"),
            "Access-Control-Allow-Credentials": response.headers.get("Access-Control-Allow-Credentials"),
            "Access-Control-Allow-Methods": response.headers.get("Access-Control-Allow-Methods"),
            "Access-Control-Allow-Headers": response.headers.get("Access-Control-Allow-Headers"),
        }
        
        print(f"   CORS Headers: {cors_headers}")
        
        if cors_headers["Access-Control-Allow-Origin"] == "http://localhost:8081":
            print("✅ CORS origin correctly set to specific origin")
        else:
            print(f"❌ CORS origin issue: {cors_headers['Access-Control-Allow-Origin']}")
            
        if cors_headers["Access-Control-Allow-Credentials"] == "true":
            print("✅ CORS credentials enabled")
        else:
            print(f"❌ CORS credentials issue: {cors_headers['Access-Control-Allow-Credentials']}")
            
    except Exception as e:
        print(f"❌ Preflight test error: {e}")
    
    # Test actual request with credentials
    print("\n2. Testing Actual Request with Credentials...")
    try:
        session = requests.Session()
        response = session.get(
            "http://localhost:8000/api/auth/me",
            headers={"Origin": "http://localhost:8081"}
        )
        
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text[:200]}...")
        
        if response.status_code == 401:
            print("✅ Unauthenticated request properly rejected (expected)")
        else:
            print(f"❌ Unexpected response: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Request test error: {e}")
    
    print("\n" + "=" * 50)
    print("🎯 CORS test completed!")

if __name__ == "__main__":
    test_cors_with_credentials()