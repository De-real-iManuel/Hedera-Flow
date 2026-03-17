"""
Test prepaid preview endpoint
"""
import requests
import json

API_BASE_URL = "http://localhost:8000/api"

# Get auth token from the test we ran earlier
# You'll need to replace this with a real token
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIzZDY2ZjA1Yy0zYmZmLTQwOWEtYTI1Zi0wYjQ0NDEyMDIzYmIiLCJlbWFpbCI6IjB4YzA3N2Q1Nzc1NTRjY2E2Y2U5YzkxZWJjYzdiMDIwOWYzYzEzYWFkYUBtZXRhbWFzay5oZWRlcmFmbG93LmxvY2FsIiwiY291bnRyeV9jb2RlIjoiRVMiLCJoZWRlcmFfYWNjb3VudF9pZCI6IjB4YzA3N2Q1Nzc1NTRjY2E2Y2U5YzkxZWJjYzdiMDIwOWYzYzEzYWFkYSIsImV4cCI6MTc3NTgwMDgyOCwiaWF0IjoxNzczMjA4ODI4LCJ0eXBlIjoiYWNjZXNzIn0.3ABPBcp3NRRTW7P4b9ZTLU-V4gh2gqv1FfLcU-aKW88"

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

try:
    # First, check if user already has meters
    print("1. Checking existing meters...")
    response = requests.get(f"{API_BASE_URL}/meters", headers=headers)
    
    if response.status_code == 200:
        meters = response.json()
        if meters:
            meter_id = meters[0]['id']
            print(f"✅ Using existing meter: {meter_id}")
        else:
            # Get utility providers for Spain (ES)
            print("\n2. Fetching utility providers for Spain...")
            response = requests.get(
                f"{API_BASE_URL}/utility-providers",
                params={"country_code": "ES"},
                headers=headers
            )
            
            if response.status_code != 200:
                print(f"❌ Failed to fetch utility providers: {response.status_code}")
                print(response.json())
                exit(1)
            
            providers = response.json()
            if not providers:
                print("❌ No utility providers found for Spain")
                exit(1)
            
            provider = providers[0]
            print(f"✅ Using provider: {provider['name']} (ID: {provider['id']})")
            
            # Create meter
            print("\n3. Creating a test meter...")
            meter_payload = {
                "meter_id": "ES-TEST-12345678",
                "utility_provider_id": provider['id'],
                "state_province": "Madrid",
                "utility_provider": provider['name'],
                "meter_type": "prepaid"
            }
            
            response = requests.post(
                f"{API_BASE_URL}/meters",
                json=meter_payload,
                headers=headers
            )
            
            if response.status_code == 201:
                meter = response.json()
                meter_id = meter['id']
                print(f"✅ Meter created: {meter_id}")
            else:
                print(f"❌ Failed to create meter: {response.status_code}")
                print(response.json())
                exit(1)
    else:
        print(f"❌ Failed to fetch meters: {response.status_code}")
        print(response.json())
        exit(1)
    
    # Test prepaid preview
    print("\n4. Testing prepaid preview...")
    preview_payload = {
        "meter_id": meter_id,
        "amount_fiat": 50.0,
        "currency": "EUR",
        "payment_method": "HBAR"
    }
    
    response = requests.post(
        f"{API_BASE_URL}/prepaid/preview",
        json=preview_payload,
        headers=headers
    )
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    if response.status_code == 200:
        data = response.json()
        print("\n✅ Preview successful!")
        print(f"   Amount: €{data['amount_fiat']}")
        print(f"   HBAR needed: {data['amount_hbar']}")
        print(f"   kWh units: {data['units_kwh']}")
        print(f"   Exchange rate: {data['exchange_rate']}")
        print(f"   Tariff rate: {data['tariff_rate']}")
    else:
        print("\n❌ Preview failed!")
        
except requests.exceptions.ConnectionError:
    print("❌ Could not connect to backend. Is it running?")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
