#!/usr/bin/env python3
"""
Debug login issues
"""
import requests
import json

# Test login with known user
def test_login():
    url = "http://localhost:8000/api/auth/login"
    
    # Test with the test user
    data = {
        "username": "test@hederaflow.com",  # OAuth2 uses 'username' field
        "password": "test123"  # Assuming this is the password
    }
    
    print("Testing login with test@hederaflow.com...")
    
    try:
        response = requests.post(url, data=data)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ Login successful!")
            result = response.json()
            print(f"Token: {result.get('token', 'N/A')[:50]}...")
            print(f"User: {result.get('user', {}).get('email', 'N/A')}")
        else:
            print("❌ Login failed!")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_login()