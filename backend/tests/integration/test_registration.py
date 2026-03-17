"""
Test script for user registration endpoint
"""
import requests
import json

# API endpoint
BASE_URL = "http://localhost:8000"
REGISTER_URL = f"{BASE_URL}/api/auth/register"

def test_registration():
    """Test user registration with email and password"""
    
    # Test data
    test_user = {
        "email": "test@example.com",
        "password": "TestPass123",
        "country_code": "ES"
    }
    
    print("Testing user registration endpoint...")
    print(f"POST {REGISTER_URL}")
    print(f"Request body: {json.dumps(test_user, indent=2)}")
    print()
    
    try:
        # Make registration request
        response = requests.post(REGISTER_URL, json=test_user)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 201:
            print("\n✅ Registration successful!")
            data = response.json()
            print(f"User ID: {data['user']['id']}")
            print(f"Email: {data['user']['email']}")
            print(f"Country: {data['user']['country_code']}")
            print(f"Hedera Account: {data['user']['hedera_account_id']}")
            print(f"Token: {data['token'][:50]}...")
        else:
            print("\n❌ Registration failed!")
            
    except requests.exceptions.ConnectionError:
        print("❌ Error: Could not connect to API server")
        print("Make sure the server is running: python backend/main.py")
    except Exception as e:
        print(f"❌ Error: {e}")


def test_password_validation():
    """Test password validation"""
    
    print("\n" + "="*60)
    print("Testing password validation...")
    print("="*60 + "\n")
    
    test_cases = [
        {
            "email": "test1@example.com",
            "password": "short",  # Too short
            "country_code": "ES"
        },
        {
            "email": "test2@example.com",
            "password": "nouppercase123",  # No uppercase
            "country_code": "ES"
        },
        {
            "email": "test3@example.com",
            "password": "NoNumbers",  # No numbers
            "country_code": "ES"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"Test case {i}: {test_case['password']}")
        try:
            response = requests.post(REGISTER_URL, json=test_case)
            print(f"Status: {response.status_code}")
            if response.status_code == 400:
                print(f"✅ Validation working: {response.json()['detail']}")
            else:
                print(f"❌ Expected 400, got {response.status_code}")
        except Exception as e:
            print(f"❌ Error: {e}")
        print()


if __name__ == "__main__":
    test_registration()
    test_password_validation()
