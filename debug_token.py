#!/usr/bin/env python3
"""
Debug JWT token creation and validation
"""
import requests
import jwt
from datetime import datetime

def debug_token():
    """Debug JWT token issues"""
    print("🔍 Debugging JWT Token Issues")
    print("=" * 40)
    
    session = requests.Session()
    
    # Step 1: Login and capture response
    print("\n1. Logging in and capturing token...")
    login_data = {"username": "testuser123@example.com", "password": "TestPass123"}
    
    try:
        response = session.post("http://localhost:8000/api/auth/login", data=login_data)
        print(f"   Login Status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Login successful")
            
            # Get the access token cookie
            access_token = session.cookies.get('access_token')
            refresh_token = session.cookies.get('refresh_token')
            
            if access_token:
                print(f"   Access token length: {len(access_token)}")
                print(f"   Access token (first 50 chars): {access_token[:50]}...")
                
                # Try to decode without verification to see the payload
                try:
                    # Decode without verification to inspect payload
                    payload = jwt.decode(access_token, options={"verify_signature": False})
                    print(f"   Token payload: {payload}")
                    
                    # Check expiration
                    exp_timestamp = payload.get('exp')
                    if exp_timestamp:
                        exp_datetime = datetime.fromtimestamp(exp_timestamp)
                        current_datetime = datetime.now()
                        print(f"   Token expires at: {exp_datetime}")
                        print(f"   Current time: {current_datetime}")
                        print(f"   Time until expiry: {exp_datetime - current_datetime}")
                        
                        if exp_datetime < current_datetime:
                            print("❌ Token is already expired!")
                        else:
                            print("✅ Token is still valid")
                    
                except Exception as e:
                    print(f"❌ Error decoding token: {e}")
            
            if refresh_token:
                print(f"   Refresh token length: {len(refresh_token)}")
                
                # Decode refresh token too
                try:
                    refresh_payload = jwt.decode(refresh_token, options={"verify_signature": False})
                    print(f"   Refresh token payload: {refresh_payload}")
                    
                    exp_timestamp = refresh_payload.get('exp')
                    if exp_timestamp:
                        exp_datetime = datetime.fromtimestamp(exp_timestamp)
                        current_datetime = datetime.now()
                        print(f"   Refresh token expires at: {exp_datetime}")
                        print(f"   Time until refresh expiry: {exp_datetime - current_datetime}")
                        
                except Exception as e:
                    print(f"❌ Error decoding refresh token: {e}")
        else:
            print(f"❌ Login failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Login error: {e}")
        return False
    
    # Step 2: Try immediate access
    print("\n2. Immediate access test...")
    try:
        response = session.get("http://localhost:8000/api/auth/me")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text}")
        
    except Exception as e:
        print(f"❌ Access error: {e}")

if __name__ == "__main__":
    debug_token()