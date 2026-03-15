#!/usr/bin/env python3
"""
Test wallet connection flow
"""
import requests

def test_wallet_connection():
    """Test wallet connection endpoint"""
    print("🔗 Testing Wallet Connection Flow")
    print("=" * 40)
    
    session = requests.Session()
    
    # Test wallet connect endpoint with mock data
    print("\n1. Testing wallet connect endpoint...")
    
    # Mock wallet connection data (this would normally come from wallet signature)
    wallet_data = {
        "hedera_account_id": "0.0.123456",  # Mock Hedera account
        "signature": "mock_signature_base64_encoded_string",
        "message": f"Hedera Flow Authentication\nAccount: 0.0.123456\nTimestamp: {1773590000000}"
    }
    
    try:
        response = session.post("http://localhost:8000/api/auth/wallet-connect", json=wallet_data)
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text[:200]}...")
        
        if response.status_code == 200:
            print("✅ Wallet connect endpoint working")
            print(f"   Cookies: {list(response.cookies.keys())}")
            
            # Test accessing protected endpoint
            print("\n2. Testing protected access after wallet connect...")
            me_response = session.get("http://localhost:8000/api/auth/me")
            print(f"   /auth/me Status: {me_response.status_code}")
            
            if me_response.status_code == 200:
                print("✅ Protected endpoint accessible after wallet connect")
                user_data = me_response.json()
                print(f"   User: {user_data.get('email')}")
                print(f"   Hedera Account: {user_data.get('hedera_account_id')}")
            else:
                print(f"❌ Protected endpoint failed: {me_response.text}")
                
        elif response.status_code == 401:
            print("ℹ️  Wallet connect failed (expected - mock signature)")
            print("   This is normal since we're using a mock signature")
        else:
            print(f"❌ Unexpected response: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Wallet connect test error: {e}")
    
    # Test with real account format but still mock signature
    print("\n3. Testing with real Hedera account format...")
    
    real_wallet_data = {
        "hedera_account_id": "0.0.4692077",  # Real testnet account format
        "signature": "real_looking_signature_but_still_mock_for_testing_purposes_base64",
        "message": f"Hedera Flow Authentication\nAccount: 0.0.4692077\nTimestamp: {1773590000000}"
    }
    
    try:
        response = session.post("http://localhost:8000/api/auth/wallet-connect", json=real_wallet_data)
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text[:200]}...")
        
        if response.status_code == 401:
            print("ℹ️  Expected 401 - signature verification failed (mock signature)")
        elif response.status_code == 400:
            print("ℹ️  Expected 400 - account validation failed")
        else:
            print(f"   Unexpected status: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Real account test error: {e}")

if __name__ == "__main__":
    test_wallet_connection()