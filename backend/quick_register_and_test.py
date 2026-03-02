#!/usr/bin/env python3
"""Quick registration and meter test"""
import requests
import json

BASE_URL = "http://localhost:8000"

# Step 1: Register
print("1. Registering new user...")
register_data = {
    "email": "test@example.com",
    "password": "Test123!@#",
    "country_code": "ES"
}

response = requests.post(
    f"{BASE_URL}/api/auth/register",
    json=register_data
)

print(f"   Status: {response.status_code}")
if response.status_code == 201:
    print("   ✅ Registration successful!")
    token = response.json()["token"]
    user = response.json()["user"]
    print(f"   Email: {user['email']}")
    print(f"   Country: {user['country_code']}")
else:
    print(f"   Response: {response.text}")
    # Try to login instead
    print("\n   Trying to login...")
    login_data = {
        "username": register_data["email"],
        "password": register_data["password"]
    }
    response = requests.post(f"{BASE_URL}/api/auth/login", data=login_data)
    if response.status_code == 200:
        token = response.json()["token"]
        user = response.json()["user"]
        print("   ✅ Login successful!")
    else:
        print(f"   ❌ Login failed: {response.text}")
        exit(1)

# Step 2: Get providers
print("\n2. Getting utility providers...")
headers = {"Authorization": f"Bearer {token}"}
response = requests.get(
    f"{BASE_URL}/api/utility-providers?country_code={user['country_code']}",
    headers=headers
)

if response.status_code == 200:
    providers = response.json()
    print(f"   Found {len(providers)} providers")
    if providers:
        provider = providers[0]
        print(f"   Using: {provider['provider_name']} in {provider['state_province']}")
    else:
        print("   ❌ No providers found!")
        exit(1)
else:
    print(f"   ❌ Failed: {response.text}")
    exit(1)

# Step 3: Register meter
print("\n3. Registering meter...")
meter_data = {
    "meter_id": "ES12345678",
    "utility_provider_id": provider['id'],
    "state_province": provider['state_province'],
    "utility_provider": provider['provider_name'],
    "meter_type": "postpaid",
    "is_primary": True
}

response = requests.post(
    f"{BASE_URL}/api/meters",
    headers={
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    },
    json=meter_data
)

print(f"   Status: {response.status_code}")
if response.status_code == 201:
    meter = response.json()
    print(f"   ✅ Meter registered!")
    print(f"   Meter ID: {meter['meter_id']}")
    print(f"   UUID: {meter['id']}")
else:
    print(f"   ❌ Failed:")
    print(json.dumps(response.json(), indent=2))
