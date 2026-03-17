"""
Test MetaMask authentication flow
"""
import requests
import json

# Test data
EVM_ADDRESS = "0xc077d577554cca6ce9c91ebcc7b0209f3c13aada"
TIMESTAMP = 1234567890
MESSAGE = f"Hedera Flow Authentication\nAddress: {EVM_ADDRESS}\nTimestamp: {TIMESTAMP}"
SIGNATURE = "0x1234567890abcdef"  # Dummy signature for testing

API_BASE_URL = "http://localhost:8000/api"

def test_wallet_connect():
    """Test wallet connect endpoint"""
    print("Testing MetaMask wallet connect...")
    print(f"EVM Address: {EVM_ADDRESS}")
    print(f"Message: {MESSAGE}")
    print(f"Signature: {SIGNATURE}")
    print()
    
    payload = {
        "hedera_account_id": EVM_ADDRESS,
        "signature": SIGNATURE,
        "message": MESSAGE
    }
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/auth/wallet-connect",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            print("\n✅ Authentication successful!")
            data = response.json()
            print(f"Token: {data.get('token', 'N/A')[:50]}...")
            print(f"User ID: {data.get('user', {}).get('id', 'N/A')}")
            print(f"Email: {data.get('user', {}).get('email', 'N/A')}")
        else:
            print("\n❌ Authentication failed!")
            print(f"Error: {response.json().get('detail', 'Unknown error')}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to backend. Is it running?")
        print("Run: cd backend && uvicorn app.core.app:app --reload")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_wallet_connect()
