#!/usr/bin/env python3
"""Test meter registration to debug the 400 error"""
import requests
import json

# Test credentials - use the one you registered with
email = "emmanuel@email.com"
password = "Test123!@#"  # Replace with your actual password

# Backend URL
BASE_URL = "http://localhost:8000"

print("="*60)
print("METER REGISTRATION DEBUG TEST")
print("="*60)

# Step 1: Login
print("\n1. Logging in...")
login_data = {
    "username": email,
    "password": password
}
response = requests.post(f"{BASE_URL}/api/auth/login", data=login_data)
print(f"   Status: {response.status_code}")

if response.status_code != 200:
    print(f"   Error: {response.text}")
    print("\n❌ Login failed. Please check your credentials.")
    print("   Try registering first if you haven't:")
    print(f"   POST {BASE_URL}/api/auth/register")
    exit(1)

token = response.json()["token"]
user = response.json()["user"]
print(f"   ✅ Logged in as: {user['email']}")
print(f"   Country: {user['country_code']}")

# Step 2: Get utility providers
print("\n2. Getting utility providers...")
headers = {"Authorization": f"Bearer {token}"}
country = user['country_code']
response = requests.get(f"{BASE_URL}/api/utility-providers?country_code={country}", headers=headers)
print(f"   Status: {response.status_code}")

if response.status_code != 200:
    print(f"   Error: {response.text}")
    exit(1)

providers = response.json()
print(f"   Found {len(providers)} providers for {country}")

if not providers:
    print("\n❌ No utility providers found!")
    print("   You need to seed the database first:")
    print("   cd backend && python scripts/seed_utility_providers.py")
    exit(1)

# Group by state
states = {}
for p in providers:
    state = p['state_province']
    if state not in states:
        states[state] = []
    states[state].append(p)

print(f"\n   Available states:")
for state in sorted(states.keys()):
    print(f"     - {state} ({len(states[state])} providers)")

# Use first state and provider
first_state = sorted(states.keys())[0]
first_provider = states[first_state][0]

print(f"\n   Using:")
print(f"     State: {first_state}")
print(f"     Provider: {first_provider['provider_name']}")
print(f"     Provider ID: {first_provider['id']}")

# Step 3: Register meter
print("\n3. Registering meter...")
meter_data = {
    "meter_id": f"{country}12345678",
    "utility_provider_id": first_provider['id'],
    "state_province": first_state,
    "utility_provider": first_provider['provider_name'],
    "meter_type": "postpaid",
    "is_primary": True
}

print(f"\n   Request data:")
print(json.dumps(meter_data, indent=2))

response = requests.post(
    f"{BASE_URL}/api/meters",
    headers={
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    },
    json=meter_data
)

print(f"\n   Response status: {response.status_code}")
print(f"   Response body:")
print(json.dumps(response.json(), indent=2))

if response.status_code == 201:
    print("\n✅ Meter registered successfully!")
    meter = response.json()
    print(f"   Meter ID: {meter['meter_id']}")
    print(f"   UUID: {meter['id']}")
else:
    print("\n❌ Meter registration failed!")
    print("\n   Common issues:")
    print("   1. Meter ID format invalid for your country")
    print("   2. State/province mismatch")
    print("   3. Utility provider ID not found")
    print("   4. Meter already registered")

print("\n" + "="*60)
