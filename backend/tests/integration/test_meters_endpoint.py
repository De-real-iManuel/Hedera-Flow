"""
Test POST /api/meters endpoint
Manual test script for meter registration
"""
import requests
import json
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from config import settings

# API base URL
BASE_URL = "http://localhost:8000/api"


def test_meter_registration():
    """Test meter registration endpoint"""
    
    print("=" * 80)
    print("Testing POST /api/meters endpoint")
    print("=" * 80)
    
    # Step 1: Register a test user
    print("\n1. Registering test user...")
    register_data = {
        "email": "test_meter_user@example.com",
        "password": "TestPassword123!",
        "country_code": "NG"  # Nigeria for testing
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/register", json=register_data)
        if response.status_code == 201:
            user_data = response.json()
            token = user_data["token"]
            print(f"✅ User registered successfully")
            print(f"   User ID: {user_data['user']['id']}")
            print(f"   Email: {user_data['user']['email']}")
            print(f"   Country: {user_data['user']['country_code']}")
        elif response.status_code == 400 and "already exists" in response.text:
            # User already exists, try to login
            print("   User already exists, logging in...")
            login_data = {
                "email": register_data["email"],
                "password": register_data["password"]
            }
            response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
            if response.status_code == 200:
                user_data = response.json()
                token = user_data["token"]
                print(f"✅ User logged in successfully")
            else:
                print(f"❌ Login failed: {response.status_code}")
                print(f"   Response: {response.text}")
                return
        else:
            print(f"❌ Registration failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return
    except Exception as e:
        print(f"❌ Error during registration: {e}")
        return
    
    # Step 2: Get utility provider ID for Lagos, Nigeria (IKEDP)
    print("\n2. Getting utility provider ID...")
    # We need to query the database to get a valid utility provider ID
    # For now, we'll use a placeholder and expect the endpoint to validate
    
    # Let's try to get utility providers from the database
    import psycopg2
    conn = psycopg2.connect(settings.database_url)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, provider_name, state_province 
        FROM utility_providers 
        WHERE country_code = 'NG' AND state_province = 'Lagos'
        LIMIT 1
    """)
    result = cursor.fetchone()
    conn.close()
    
    if result:
        utility_provider_id = str(result[0])
        provider_name = result[1]
        state_province = result[2]
        print(f"✅ Found utility provider:")
        print(f"   ID: {utility_provider_id}")
        print(f"   Name: {provider_name}")
        print(f"   State: {state_province}")
    else:
        print("❌ No utility provider found for Lagos, Nigeria")
        return
    
    # Step 3: Register a meter
    print("\n3. Registering meter...")
    meter_data = {
        "meter_id": "NG-LAGOS-12345678",
        "utility_provider_id": utility_provider_id,
        "state_province": state_province,
        "utility_provider": provider_name,
        "meter_type": "postpaid",
        "band_classification": "C",  # Required for Nigeria
        "address": "123 Test Street, Lagos, Nigeria",
        "is_primary": True
    }
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/meters", json=meter_data, headers=headers)
        
        if response.status_code == 201:
            meter = response.json()
            print(f"✅ Meter registered successfully!")
            print(f"   Meter ID: {meter['id']}")
            print(f"   Meter Number: {meter['meter_id']}")
            print(f"   Utility Provider: {meter['utility_provider']}")
            print(f"   State: {meter['state_province']}")
            print(f"   Type: {meter['meter_type']}")
            print(f"   Band: {meter['band_classification']}")
            print(f"   Is Primary: {meter['is_primary']}")
            print(f"   Created At: {meter['created_at']}")
        else:
            print(f"❌ Meter registration failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return
    except Exception as e:
        print(f"❌ Error during meter registration: {e}")
        return
    
    # Step 4: Test validation - try to register same meter again
    print("\n4. Testing duplicate meter validation...")
    try:
        response = requests.post(f"{BASE_URL}/meters", json=meter_data, headers=headers)
        
        if response.status_code == 409:
            print(f"✅ Duplicate meter validation working correctly")
            print(f"   Response: {response.json()['detail']}")
        else:
            print(f"⚠️  Expected 409 Conflict, got {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ Error during duplicate test: {e}")
    
    # Step 5: Test validation - try to register meter without band classification
    print("\n5. Testing band classification validation...")
    invalid_meter_data = meter_data.copy()
    invalid_meter_data["meter_id"] = "NG-LAGOS-87654321"
    invalid_meter_data["band_classification"] = None
    
    try:
        response = requests.post(f"{BASE_URL}/meters", json=invalid_meter_data, headers=headers)
        
        if response.status_code == 400:
            print(f"✅ Band classification validation working correctly")
            print(f"   Response: {response.json()['detail']}")
        else:
            print(f"⚠️  Expected 400 Bad Request, got {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ Error during validation test: {e}")
    
    print("\n" + "=" * 80)
    print("✅ All tests completed!")
    print("=" * 80)


if __name__ == "__main__":
    test_meter_registration()
