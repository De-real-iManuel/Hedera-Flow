"""
Quick test script to verify new endpoints are working
Run this after the server starts successfully
"""
import requests
import json

BASE_URL = "http://localhost:8000/api"

# You'll need to replace this with a real token after logging in
TOKEN = "your_jwt_token_here"

def test_endpoints():
    """Test all new endpoints"""
    
    print("=" * 60)
    print("Testing New Hedera Flow Endpoints")
    print("=" * 60)
    
    # Test 1: Profile Completion
    print("\n1. Testing Profile Completion Endpoint")
    print("-" * 60)
    try:
        response = requests.put(
            f"{BASE_URL}/auth/complete-profile",
            headers={"Authorization": f"Bearer {TOKEN}"},
            data={
                "first_name": "Test",
                "last_name": "User",
                "country_code": "US"
            }
        )
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print("✅ Profile completion endpoint working!")
            print(f"Response: {json.dumps(response.json(), indent=2)}")
        elif response.status_code == 401:
            print("⚠️  Endpoint exists but needs valid token")
        else:
            print(f"❌ Error: {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 2: Prepaid Payment Confirmation
    print("\n2. Testing Prepaid Payment Confirmation Endpoint")
    print("-" * 60)
    try:
        response = requests.post(
            f"{BASE_URL}/prepaid/confirm-payment",
            headers={"Authorization": f"Bearer {TOKEN}"},
            data={
                "token_id": "TOKEN-US-2026-001",
                "hedera_tx_id": "0.0.12345@1710241234.123456789"
            }
        )
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print("✅ Payment confirmation endpoint working!")
            print(f"Response: {json.dumps(response.json(), indent=2)}")
        elif response.status_code == 401:
            print("⚠️  Endpoint exists but needs valid token")
        elif response.status_code == 404:
            print("⚠️  Endpoint exists but token not found (expected)")
        else:
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 3: Smart Meter Consumption History
    print("\n3. Testing Smart Meter Consumption History Endpoint")
    print("-" * 60)
    try:
        # Use a dummy UUID for testing
        meter_id = "550e8400-e29b-41d4-a716-446655440000"
        response = requests.get(
            f"{BASE_URL}/smart-meter/consumption-history/{meter_id}?limit=10",
            headers={"Authorization": f"Bearer {TOKEN}"}
        )
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print("✅ Consumption history endpoint working!")
            data = response.json()
            print(f"Found {len(data)} consumption logs")
            if data:
                print(f"Sample: {json.dumps(data[0], indent=2)}")
        elif response.status_code == 401:
            print("⚠️  Endpoint exists but needs valid token")
        elif response.status_code == 404:
            print("⚠️  Endpoint exists but meter not found (expected)")
        else:
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 4: Health Check
    print("\n4. Testing Health Check (for reference)")
    print("-" * 60)
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print("✅ Server is running!")
            health = response.json()
            print(f"Database: {health.get('database', 'unknown')}")
            print(f"OCR Available: {health.get('ocr_available', 'unknown')}")
        else:
            print(f"❌ Error: {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n" + "=" * 60)
    print("Test Complete!")
    print("=" * 60)
    print("\nNOTE: To fully test endpoints, you need:")
    print("1. A valid JWT token (login first)")
    print("2. Real meter IDs and token IDs from your database")
    print("3. Valid Hedera transaction IDs for payment confirmation")
    print("\nSee QUICK_START.md for detailed testing instructions")


if __name__ == "__main__":
    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Server is running, starting tests...\n")
            test_endpoints()
        else:
            print("❌ Server returned unexpected status")
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server at http://localhost:8000")
        print("Please start the server first:")
        print("  cd backend")
        print("  python -m uvicorn app.core.app:app --reload")
    except Exception as e:
        print(f"❌ Error: {e}")
