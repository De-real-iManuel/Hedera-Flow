#!/usr/bin/env python3
import requests
import json

BASE_URL = "http://localhost:8000"

# Login
token = requests.post(
    f"{BASE_URL}/api/auth/login",
    data={'username': 'test@example.com', 'password': 'Test123!@#'}
).json()['token']

headers = {'Authorization': f'Bearer {token}'}

# List existing meters
meters = requests.get(f"{BASE_URL}/api/meters", headers=headers).json()
print(f"Existing meters: {len(meters)}")
for m in meters:
    print(f"  - {m['meter_id']} ({m['utility_provider']})")

# Get providers
providers = requests.get(
    f"{BASE_URL}/api/utility-providers?country_code=NG",
    headers=headers
).json()

if providers:
    p = providers[0]
    print(f"\nUsing provider: {p['provider_name']} in {p['state_province']}")
    
    # Try new meter
    new_meter = {
        'meter_id': '98765432109',  # Different meter ID
        'utility_provider_id': p['id'],
        'state_province': p['state_province'],
        'utility_provider': p['provider_name'],
        'meter_type': 'prepaid',
        'band_classification': 'C',
        'is_primary': False
    }
    
    print("\nRegistering new meter...")
    r = requests.post(
        f"{BASE_URL}/api/meters",
        headers={**headers, 'Content-Type': 'application/json'},
        json=new_meter
    )
    
    print(f"Status: {r.status_code}")
    print(json.dumps(r.json(), indent=2))
