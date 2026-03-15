#!/usr/bin/env python3
"""
Test JWT token timing issues
"""
import jwt
from datetime import datetime, timedelta

def test_token_timing():
    """Test JWT token creation and validation timing"""
    print("⏰ Testing JWT Token Timing")
    print("=" * 30)
    
    # Simulate token creation like the backend does
    print("\n1. Creating token...")
    
    current_utc = datetime.utcnow()
    expiration_utc = current_utc + timedelta(minutes=15)
    
    print(f"   Current UTC time: {current_utc}")
    print(f"   Expiration UTC time: {expiration_utc}")
    print(f"   Current timestamp: {int(current_utc.timestamp())}")
    print(f"   Expiration timestamp: {int(expiration_utc.timestamp())}")
    
    # Create payload like the backend
    payload = {
        "sub": "test-user-id",
        "email": "test@example.com",
        "exp": int(expiration_utc.timestamp()),
        "iat": int(current_utc.timestamp()),
        "type": "access"
    }
    
    # Create token
    secret_key = "test-secret-key-for-testing"
    token = jwt.encode(payload, secret_key, algorithm="HS256")
    print(f"   Token created: {token[:50]}...")
    
    # Immediately decode and check
    print("\n2. Immediate validation...")
    try:
        decoded = jwt.decode(token, secret_key, algorithms=["HS256"])
        print("✅ Token validation successful")
        print(f"   Decoded payload: {decoded}")
        
        # Check timing
        exp_timestamp = decoded.get('exp')
        current_timestamp = int(datetime.utcnow().timestamp())
        
        print(f"   Token exp timestamp: {exp_timestamp}")
        print(f"   Current timestamp: {current_timestamp}")
        print(f"   Difference: {exp_timestamp - current_timestamp} seconds")
        
        if exp_timestamp > current_timestamp:
            print("✅ Token is valid (not expired)")
        else:
            print("❌ Token is expired")
            
    except jwt.ExpiredSignatureError:
        print("❌ Token expired immediately!")
    except Exception as e:
        print(f"❌ Token validation error: {e}")
    
    # Test with different timezone approaches
    print("\n3. Testing timezone handling...")
    
    # Test with local time
    current_local = datetime.now()
    exp_local = current_local + timedelta(minutes=15)
    
    print(f"   Local time: {current_local}")
    print(f"   UTC time: {current_utc}")
    print(f"   Time difference: {current_local - current_utc}")
    
    # Create token with local time
    payload_local = {
        "sub": "test-user-id",
        "email": "test@example.com", 
        "exp": int(exp_local.timestamp()),
        "iat": int(current_local.timestamp()),
        "type": "access"
    }
    
    token_local = jwt.encode(payload_local, secret_key, algorithm="HS256")
    
    try:
        decoded_local = jwt.decode(token_local, secret_key, algorithms=["HS256"])
        print("✅ Local time token validation successful")
    except jwt.ExpiredSignatureError:
        print("❌ Local time token expired immediately!")
    except Exception as e:
        print(f"❌ Local time token error: {e}")

if __name__ == "__main__":
    test_token_timing()