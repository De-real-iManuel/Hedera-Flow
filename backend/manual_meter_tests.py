"""
Task 7.7: Manual Meter CRUD Testing for All 5 Regions
Tests meter operations via HTTP API calls (no Hedera/SQLite issues)
"""
import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000/api"

# Test results storage
results = []

def log_test(region, operation, success, details=""):
    """Log test result"""
    status = "[PASS]" if success else "[FAIL]"
    results.append({
        "region": region,
        "operation": operation,
        "success": success,
        "details": details
    })
    print(f"{status} {region} - {operation}: {details}")

def test_meter_crud_spain():
    """Test meter CRUD for Spain"""
    print("\n=== Testing Spain (ES) ===")
    
    # Register user
    user_data = {
        "email": f"test_es_{datetime.now().timestamp()}@example.com",
        "password": "TestPassword123",
        "country_code": "ES"
    }
    
    try:
        r = requests.post(f"{BASE_URL}/auth/register", json=user_data)
        if r.status_code == 201:
            token = r.json()["token"]
            user_id = r.json()["user"]["id"]
            log_test("ES", "User Registration", True, f"User ID: {user_id}")
        else:
            log_test("ES", "User Registration", False, f"Status: {r.status_code}")
            return
    except Exception as e:
        log_test("ES", "User Registration", False, str(e))
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create meter
    meter_data = {
        "meter_id": "ES-TEST-001",
        "utility_provider_id": 1,  # Assuming Iberdrola
        "meter_type": "DIGITAL",
        "is_prepaid": False
    }
    
    try:
        r = requests.post(f"{BASE_URL}/meters", json=meter_data, headers=headers)
        if r.status_code == 201:
            meter_id = r.json()["id"]
            log_test("ES", "Create Meter", True, f"Meter ID: {meter_id}")
        else:
            log_test("ES", "Create Meter", False, f"Status: {r.status_code} - {r.text}")
            return
    except Exception as e:
        log_test("ES", "Create Meter", False, str(e))
        return
    
    # Read meter
    try:
        r = requests.get(f"{BASE_URL}/meters", headers=headers)
        if r.status_code == 200:
            meters = r.json()
            log_test("ES", "Read Meters", True, f"Found {len(meters)} meter(s)")
        else:
            log_test("ES", "Read Meters", False, f"Status: {r.status_code}")
    except Exception as e:
        log_test("ES", "Read Meters", False, str(e))
    
    # Update meter
    update_data = {"meter_type": "SMART"}
    try:
        r = requests.put(f"{BASE_URL}/meters/{meter_id}", json=update_data, headers=headers)
        if r.status_code == 200:
            log_test("ES", "Update Meter", True, "Type changed to SMART")
        else:
            log_test("ES", "Update Meter", False, f"Status: {r.status_code}")
    except Exception as e:
        log_test("ES", "Update Meter", False, str(e))
    
    # Delete meter
    try:
        r = requests.delete(f"{BASE_URL}/meters/{meter_id}", headers=headers)
        if r.status_code == 200:
            log_test("ES", "Delete Meter", True, "Meter deleted")
        else:
            log_test("ES", "Delete Meter", False, f"Status: {r.status_code}")
    except Exception as e:
        log_test("ES", "Delete Meter", False, str(e))


def test_meter_crud_usa():
    """Test meter CRUD for USA"""
    print("\n=== Testing USA (US) ===")
    
    user_data = {
        "email": f"test_us_{datetime.now().timestamp()}@example.com",
        "password": "TestPassword123",
        "country_code": "US"
    }
    
    try:
        r = requests.post(f"{BASE_URL}/auth/register", json=user_data)
        if r.status_code == 201:
            token = r.json()["token"]
            log_test("US", "User Registration", True)
        else:
            log_test("US", "User Registration", False, f"Status: {r.status_code}")
            return
    except Exception as e:
        log_test("US", "User Registration", False, str(e))
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    meter_data = {
        "meter_id": "US-TEST-001",
        "utility_provider_id": 2,  # Assuming PG&E
        "meter_type": "SMART"
    }
    
    try:
        r = requests.post(f"{BASE_URL}/meters", json=meter_data, headers=headers)
        if r.status_code == 201:
            log_test("US", "Create Meter", True, f"Meter: {r.json()['meter_id']}")
        else:
            log_test("US", "Create Meter", False, f"Status: {r.status_code}")
    except Exception as e:
        log_test("US", "Create Meter", False, str(e))


def test_meter_crud_india():
    """Test meter CRUD for India"""
    print("\n=== Testing India (IN) ===")
    
    user_data = {
        "email": f"test_in_{datetime.now().timestamp()}@example.com",
        "password": "TestPassword123",
        "country_code": "IN"
    }
    
    try:
        r = requests.post(f"{BASE_URL}/auth/register", json=user_data)
        if r.status_code == 201:
            token = r.json()["token"]
            log_test("IN", "User Registration", True)
        else:
            log_test("IN", "User Registration", False, f"Status: {r.status_code}")
            return
    except Exception as e:
        log_test("IN", "User Registration", False, str(e))
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    meter_data = {
        "meter_id": "IN-TEST-001",
        "utility_provider_id": 3,  # Assuming Tata Power
        "meter_type": "DIGITAL"
    }
    
    try:
        r = requests.post(f"{BASE_URL}/meters", json=meter_data, headers=headers)
        if r.status_code == 201:
            log_test("IN", "Create Meter", True, f"Meter: {r.json()['meter_id']}")
        else:
            log_test("IN", "Create Meter", False, f"Status: {r.status_code}")
    except Exception as e:
        log_test("IN", "Create Meter", False, str(e))


def test_meter_crud_brazil():
    """Test meter CRUD for Brazil"""
    print("\n=== Testing Brazil (BR) ===")
    
    user_data = {
        "email": f"test_br_{datetime.now().timestamp()}@example.com",
        "password": "TestPassword123",
        "country_code": "BR"
    }
    
    try:
        r = requests.post(f"{BASE_URL}/auth/register", json=user_data)
        if r.status_code == 201:
            token = r.json()["token"]
            log_test("BR", "User Registration", True)
        else:
            log_test("BR", "User Registration", False, f"Status: {r.status_code}")
            return
    except Exception as e:
        log_test("BR", "User Registration", False, str(e))
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    meter_data = {
        "meter_id": "BR-TEST-001",
        "utility_provider_id": 4,  # Assuming Enel
        "meter_type": "DIGITAL"
    }
    
    try:
        r = requests.post(f"{BASE_URL}/meters", json=meter_data, headers=headers)
        if r.status_code == 201:
            log_test("BR", "Create Meter", True, f"Meter: {r.json()['meter_id']}")
        else:
            log_test("BR", "Create Meter", False, f"Status: {r.status_code}")
    except Exception as e:
        log_test("BR", "Create Meter", False, str(e))


def test_meter_crud_nigeria():
    """Test meter CRUD for Nigeria"""
    print("\n=== Testing Nigeria (NG) ===")
    
    user_data = {
        "email": f"test_ng_{datetime.now().timestamp()}@example.com",
        "password": "TestPassword123",
        "country_code": "NG"
    }
    
    try:
        r = requests.post(f"{BASE_URL}/auth/register", json=user_data)
        if r.status_code == 201:
            token = r.json()["token"]
            log_test("NG", "User Registration", True)
        else:
            log_test("NG", "User Registration", False, f"Status: {r.status_code}")
            return
    except Exception as e:
        log_test("NG", "User Registration", False, str(e))
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test prepaid meter with band classification
    meter_data = {
        "meter_id": "NG-TEST-001",
        "utility_provider_id": 5,  # Assuming EKEDC
        "meter_type": "PREPAID",
        "is_prepaid": True,
        "band_classification": "A"
    }
    
    try:
        r = requests.post(f"{BASE_URL}/meters", json=meter_data, headers=headers)
        if r.status_code == 201:
            meter = r.json()
            log_test("NG", "Create Prepaid Meter", True, f"Band: {meter.get('band_classification', 'N/A')}")
        else:
            log_test("NG", "Create Prepaid Meter", False, f"Status: {r.status_code}")
    except Exception as e:
        log_test("NG", "Create Prepaid Meter", False, str(e))


def print_summary():
    """Print test summary"""
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    total = len(results)
    passed = sum(1 for r in results if r["success"])
    failed = total - passed
    
    print(f"\nTotal Tests: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Success Rate: {(passed/total*100):.1f}%\n")
    
    # Group by region
    regions = {}
    for r in results:
        region = r["region"]
        if region not in regions:
            regions[region] = {"passed": 0, "failed": 0}
        if r["success"]:
            regions[region]["passed"] += 1
        else:
            regions[region]["failed"] += 1
    
    print("Results by Region:")
    for region, stats in regions.items():
        total_region = stats["passed"] + stats["failed"]
        print(f"  {region}: {stats['passed']}/{total_region} passed")
    
    print("\n" + "="*60)


def main():
    """Run all tests"""
    print("="*60)
    print("METER CRUD TESTING - ALL 5 REGIONS")
    print("="*60)
    print(f"\nTesting against: {BASE_URL}")
    print(f"Timestamp: {datetime.now().isoformat()}\n")
    
    # Check if backend is running
    try:
        r = requests.get(f"{BASE_URL}/health", timeout=2)
        if r.status_code == 200:
            print("[OK] Backend is running\n")
        else:
            print("[FAIL] Backend returned unexpected status")
            return
    except:
        print("[FAIL] Backend is NOT running!")
        print("\nPlease start the backend first:")
        print("  cd backend")
        print("  python run.py")
        return
    
    # Run tests for each region
    test_meter_crud_spain()
    test_meter_crud_usa()
    test_meter_crud_india()
    test_meter_crud_brazil()
    test_meter_crud_nigeria()
    
    # Print summary
    print_summary()


if __name__ == "__main__":
    main()
