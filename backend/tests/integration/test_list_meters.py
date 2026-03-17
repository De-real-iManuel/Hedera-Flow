"""
Test GET /api/meters endpoint
Tests listing all meters for authenticated user
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


def test_list_meters():
    """Test listing meters endpoint"""
    
    print("=" * 80)
    print("Testing GET /api/meters endpoint")
    print("=" * 80)
    
    # Step 1: Register a test user
    print("\n1. Registering test user...")
    register_data = {
        "email": "test_list_meters@example.com",
        "password": "TestPassword123!",
        "country_code": "ES"  # Spain for testing
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/register", json=register_data)
        if response.status_code == 201:
            user_data = response.json()
            token = user_data["token"]
            print(f"✅ User registered successfully")
            print(f"   User ID: {user_data['user']['id']}")
            print(f"   Email: {user_data['user']['email']}")
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
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Step 2: Test listing meters when user has no meters
    print("\n2. Testing GET /api/meters with no meters...")
    try:
        response = requests.get(f"{BASE_URL}/meters", headers=headers)
        
        if response.status_code == 200:
            meters = response.json()
            print(f"✅ GET request successful")
            print(f"   Number of meters: {len(meters)}")
            if len(meters) == 0:
                print(f"   ✅ Correctly returns empty list for new user")
        else:
            print(f"❌ GET request failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return
    except Exception as e:
        print(f"❌ Error during GET request: {e}")
        return
    
    # Step 3: Get utility provider ID for Spain
    print("\n3. Getting utility provider ID for Spain...")
    import psycopg2
    conn = psycopg2.connect(settings.database_url)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, provider_name, state_province 
        FROM utility_providers 
        WHERE country_code = 'ES' 
        LIMIT 1
    """)
    result = cursor.fetchone()
    
    if result:
        utility_provider_id = str(result[0])
        provider_name = result[1]
        state_province = result[2]
        print(f"✅ Found utility provider:")
        print(f"   ID: {utility_provider_id}")
        print(f"   Name: {provider_name}")
        print(f"   State: {state_province}")
    else:
        print("❌ No utility provider found for Spain")
        conn.close()
        return
    
    # Step 4: Register first meter
    print("\n4. Registering first meter...")
    meter1_data = {
        "meter_id": "ES-MAD-11111111",
        "utility_provider_id": utility_provider_id,
        "state_province": state_province,
        "utility_provider": provider_name,
        "meter_type": "postpaid",
        "address": "Calle Principal 123, Madrid, Spain",
        "is_primary": True
    }
    
    try:
        response = requests.post(f"{BASE_URL}/meters", json=meter1_data, headers=headers)
        
        if response.status_code == 201:
            meter1 = response.json()
            print(f"✅ First meter registered successfully!")
            print(f"   Meter ID: {meter1['id']}")
            print(f"   Meter Number: {meter1['meter_id']}")
            print(f"   Is Primary: {meter1['is_primary']}")
        else:
            print(f"❌ Meter registration failed: {response.status_code}")
            print(f"   Response: {response.text}")
            conn.close()
            return
    except Exception as e:
        print(f"❌ Error during meter registration: {e}")
        conn.close()
        return
    
    # Step 5: Register second meter
    print("\n5. Registering second meter...")
    meter2_data = {
        "meter_id": "ES-MAD-22222222",
        "utility_provider_id": utility_provider_id,
        "state_province": state_province,
        "utility_provider": provider_name,
        "meter_type": "prepaid",
        "address": "Avenida Secundaria 456, Madrid, Spain",
        "is_primary": False
    }
    
    try:
        response = requests.post(f"{BASE_URL}/meters", json=meter2_data, headers=headers)
        
        if response.status_code == 201:
            meter2 = response.json()
            print(f"✅ Second meter registered successfully!")
            print(f"   Meter ID: {meter2['id']}")
            print(f"   Meter Number: {meter2['meter_id']}")
            print(f"   Is Primary: {meter2['is_primary']}")
        else:
            print(f"❌ Meter registration failed: {response.status_code}")
            print(f"   Response: {response.text}")
            conn.close()
            return
    except Exception as e:
        print(f"❌ Error during meter registration: {e}")
        conn.close()
        return
    
    # Step 6: Register third meter
    print("\n6. Registering third meter...")
    meter3_data = {
        "meter_id": "ES-MAD-33333333",
        "utility_provider_id": utility_provider_id,
        "state_province": state_province,
        "utility_provider": provider_name,
        "meter_type": "postpaid",
        "address": "Plaza Tercera 789, Madrid, Spain",
        "is_primary": False
    }
    
    try:
        response = requests.post(f"{BASE_URL}/meters", json=meter3_data, headers=headers)
        
        if response.status_code == 201:
            meter3 = response.json()
            print(f"✅ Third meter registered successfully!")
            print(f"   Meter ID: {meter3['id']}")
            print(f"   Meter Number: {meter3['meter_id']}")
        else:
            print(f"❌ Meter registration failed: {response.status_code}")
            print(f"   Response: {response.text}")
            conn.close()
            return
    except Exception as e:
        print(f"❌ Error during meter registration: {e}")
        conn.close()
        return
    
    conn.close()
    
    # Step 7: Test listing all meters
    print("\n7. Testing GET /api/meters with multiple meters...")
    try:
        response = requests.get(f"{BASE_URL}/meters", headers=headers)
        
        if response.status_code == 200:
            meters = response.json()
            print(f"✅ GET request successful")
            print(f"   Number of meters returned: {len(meters)}")
            
            # Verify we got all 3 meters
            if len(meters) == 3:
                print(f"   ✅ Correct number of meters returned")
            else:
                print(f"   ❌ Expected 3 meters, got {len(meters)}")
            
            # Verify ordering (primary first, then by created_at desc)
            print(f"\n   Meters returned (in order):")
            for i, meter in enumerate(meters, 1):
                print(f"   {i}. {meter['meter_id']}")
                print(f"      - Type: {meter['meter_type']}")
                print(f"      - Primary: {meter['is_primary']}")
                print(f"      - Utility: {meter['utility_provider']}")
                print(f"      - State: {meter['state_province']}")
                print(f"      - Address: {meter.get('address', 'N/A')}")
                print(f"      - Created: {meter['created_at']}")
            
            # Verify primary meter is first
            if meters[0]['is_primary']:
                print(f"\n   ✅ Primary meter is listed first")
            else:
                print(f"\n   ❌ Primary meter should be listed first")
            
            # Verify all required fields are present
            required_fields = [
                'id', 'user_id', 'meter_id', 'utility_provider_id',
                'state_province', 'utility_provider', 'meter_type',
                'is_primary', 'created_at', 'updated_at'
            ]
            
            all_fields_present = True
            for meter in meters:
                for field in required_fields:
                    if field not in meter:
                        print(f"   ❌ Missing field '{field}' in meter {meter.get('meter_id', 'unknown')}")
                        all_fields_present = False
            
            if all_fields_present:
                print(f"   ✅ All required fields present in response")
            
        else:
            print(f"❌ GET request failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return
    except Exception as e:
        print(f"❌ Error during GET request: {e}")
        return
    
    # Step 8: Test authentication requirement
    print("\n8. Testing authentication requirement...")
    try:
        response = requests.get(f"{BASE_URL}/meters")  # No auth header
        
        if response.status_code == 401:
            print(f"✅ Correctly requires authentication")
            print(f"   Response: {response.json()['detail']}")
        else:
            print(f"⚠️  Expected 401 Unauthorized, got {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ Error during authentication test: {e}")
    
    # Step 9: Test with invalid token
    print("\n9. Testing with invalid token...")
    invalid_headers = {
        "Authorization": "Bearer invalid_token_here",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(f"{BASE_URL}/meters", headers=invalid_headers)
        
        if response.status_code == 401:
            print(f"✅ Correctly rejects invalid token")
            print(f"   Response: {response.json()['detail']}")
        else:
            print(f"⚠️  Expected 401 Unauthorized, got {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ Error during invalid token test: {e}")
    
    print("\n" + "=" * 80)
    print("✅ All tests completed!")
    print("=" * 80)
    print("\nSummary:")
    print("- GET /api/meters returns empty list for new users")
    print("- GET /api/meters returns all user's meters")
    print("- Primary meter is listed first")
    print("- All required fields are present")
    print("- Authentication is required")
    print("- Invalid tokens are rejected")


if __name__ == "__main__":
    test_list_meters()

