"""
Simple test runner for authentication tests
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import requests
import time

BASE_URL = "http://localhost:8000"
TEST_EMAIL = f"test_{int(time.time())}@example.com"
TEST_PASSWORD = "TestPassword123"

def test_backend():
    print("\n" + "="*60)
    print("BACKEND AUTHENTICATION TESTS")
    print("="*60 + "\n")
    
    # Check server
    print("1. Checking if backend is running...")
    try:
        r = requests.get(f"{BASE_URL}/api/health", timeout=2)
        print(f"   [OK] Backend is running - Status: {r.status_code}")
    except:
        print("   [FAIL] Backend is NOT running!")
        print("\n   Start backend with: cd backend && python run.py")
        return
    
    # Test registration
    print("\n2. Testing user registration...")
    try:
        r = requests.post(
            f"{BASE_URL}/api/auth/register",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD, "country_code": "ES"}
        )
        if r.status_code == 201:
            print(f"   [PASS] Registration successful")
            token = r.json().get("token")
        else:
            print(f"   [FAIL] Registration failed - {r.status_code}: {r.text}")
            return
    except Exception as e:
        print(f"   [FAIL] Registration error: {e}")
        return
    
    # Test duplicate email
    print("\n3. Testing duplicate email rejection...")
    try:
        r = requests.post(
            f"{BASE_URL}/api/auth/register",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD, "country_code": "ES"}
        )
        if r.status_code == 400:
            print(f"   [PASS] Duplicate email rejected")
        else:
            print(f"   [FAIL] Expected 400, got {r.status_code}")
    except Exception as e:
        print(f"   [FAIL] Error: {e}")
    
    # Test weak password
    print("\n4. Testing weak password rejection...")
    try:
        r = requests.post(
            f"{BASE_URL}/api/auth/register",
            json={"email": f"weak_{TEST_EMAIL}", "password": "weak", "country_code": "ES"}
        )
        if r.status_code == 400:
            print(f"   [PASS] Weak password rejected")
        else:
            print(f"   [FAIL] Expected 400, got {r.status_code}")
    except Exception as e:
        print(f"   [FAIL] Error: {e}")
    
    # Test login
    print("\n5. Testing user login...")
    try:
        r = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        if r.status_code == 200:
            print(f"   [PASS] Login successful")
            token = r.json().get("token")
        else:
            print(f"   [FAIL] Login failed - {r.status_code}: {r.text}")
    except Exception as e:
        print(f"   [FAIL] Error: {e}")
    
    # Test invalid password
    print("\n6. Testing invalid password rejection...")
    try:
        r = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": "WrongPassword123"}
        )
        if r.status_code == 401:
            print(f"   [PASS] Invalid password rejected")
        else:
            print(f"   [FAIL] Expected 401, got {r.status_code}")
    except Exception as e:
        print(f"   [FAIL] Error: {e}")
    
    # Test non-existent user
    print("\n7. Testing non-existent user rejection...")
    try:
        r = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "nonexistent@example.com", "password": TEST_PASSWORD}
        )
        if r.status_code == 404:
            print(f"   [PASS] Non-existent user rejected")
        else:
            print(f"   [FAIL] Expected 404, got {r.status_code}")
    except Exception as e:
        print(f"   [FAIL] Error: {e}")
    
    # Test protected route
    print("\n8. Testing protected route with token...")
    try:
        r = requests.get(f"{BASE_URL}/api/health", headers={"Authorization": f"Bearer {token}"})
        if r.status_code == 200:
            print(f"   [PASS] Protected route accessible with token")
        else:
            print(f"   [FAIL] Expected 200, got {r.status_code}")
    except Exception as e:
        print(f"   [FAIL] Error: {e}")
    
    print("\n" + "="*60)
    print("TESTS COMPLETED")
    print("="*60 + "\n")

if __name__ == "__main__":
    test_backend()
