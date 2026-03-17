#!/usr/bin/env python3
"""Test user profile with names"""
import requests
import json

BASE_URL = "http://localhost:8080/api"

# Test login
print("Testing login...")
login_data = {
    "username": "emmanuel@email.com",  # OAuth2 uses 'username' field
    "password": "your_password_here"
}

response = requests.post(f"{BASE_URL}/auth/login", data=login_data)
print(f"Login status: {response.status_code}")

if response.status_code == 200:
    data = response.json()
    print(f"Token: {data['token'][:20]}...")
    print(f"User: {json.dumps(data['user'], indent=2)}")
    
    # Test /me endpoint
    print("\nTesting /me endpoint...")
    headers = {"Authorization": f"Bearer {data['token']}"}
    me_response = requests.get(f"{BASE_URL}/auth/me", headers=headers)
    print(f"/me status: {me_response.status_code}")
    if me_response.status_code == 200:
        print(f"Current user: {json.dumps(me_response.json(), indent=2)}")
else:
    print(f"Error: {response.text}")
