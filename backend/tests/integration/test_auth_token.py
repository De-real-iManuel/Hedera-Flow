#!/usr/bin/env python3
"""
Test script to create a valid auth token for testing
"""
import requests
import json

API_BASE = "http://localhost:8000/api"

def test_login_and_verify():
    """Test login and then verify endpoint"""
    
    # First, try to login with test credentials
    login_data = {
        "username": "testuser@hederaflow.com",  # New test user
        "password": "TestPassword123!"  # Known password
    }
    
    print("Testing login...")
    try:
        # Try to login
        response = requests.post(f"{API_BASE}/auth/login", data=login_data)
        print(f"Login Status Code: {response.status_code}")
        print(f"Login Response: {response.text}")
        
        if response.status_code == 200:
            auth_data = response.json()
            token = auth_data.get("token")
            print(f"Got token: {token[:50]}..." if token else "No token in response")
            
            if token:
                # Now test the verify endpoint with the token
                print("\nTesting verify endpoint with token...")
                
                # Create a small test image
                test_image_content = b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xff\xd9'
                
                headers = {"Authorization": f"Bearer {token}"}
                files = {"image": ("test.jpg", test_image_content, "image/jpeg")}
                data = {"meter_id": "79c3c974-f1e3-432e-8e6e-0fefa91f1835"}  # Use test user's meter UUID
                
                verify_response = requests.post(
                    f"{API_BASE}/verify/scan", 
                    files=files, 
                    data=data, 
                    headers=headers
                )
                
                print(f"Verify Status Code: {verify_response.status_code}")
                print(f"Verify Response: {verify_response.text}")
        
        else:
            print("Login failed - cannot test verify endpoint")
            
    except Exception as e:
        print(f"Test failed: {e}")

if __name__ == "__main__":
    test_login_and_verify()