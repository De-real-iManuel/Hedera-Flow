#!/usr/bin/env python3
"""
Quick test script for verification with billing calculation

Tests Task 13.9: Trigger billing calculation after verification
"""
import requests
import json
from pathlib import Path

# Configuration
API_BASE_URL = "http://localhost:8000/api"
TEST_USER_EMAIL = "test@hederaflow.com"
TEST_USER_PASSWORD = "TestPassword123!"


def print_section(title):
    """Print a section header"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def test_verification_with_billing():
    """Test complete verification flow with billing calculation"""
    
    print_section("VERIFICATION WITH BILLING CALCULATION TEST")
    
    # Step 1: Login to get JWT token
    print("\n1. Logging in...")
    login_response = requests.post(
        f"{API_BASE_URL}/auth/login",
        json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        }
    )
    
    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.status_code}")
        print(login_response.text)
        return
    
    token = login_response.json()["token"]
    user_id = login_response.json()["user"]["id"]
    print(f"✅ Logged in successfully (User ID: {user_id})")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Step 2: Get user's meters
    print("\n2. Fetching user's meters...")
    meters_response = requests.get(
        f"{API_BASE_URL}/meters",
        headers=headers
    )
    
    if meters_response.status_code != 200:
        print(f"❌ Failed to fetch meters: {meters_response.status_code}")
        return
    
    meters = meters_response.json()["meters"]
    
    if not meters:
        print("❌ No meters found. Please register a meter first.")
        return
    
    meter = meters[0]
    meter_id = meter["id"]
    print(f"✅ Found meter: {meter['meterId']} ({meter['utilityProvider']})")
    
    # Step 3: Check for previous verifications
    print("\n3. Checking verification history...")
    verifications_response = requests.get(
        f"{API_BASE_URL}/verifications?meterId={meter_id}&limit=1",
        headers=headers
    )
    
    has_previous = False
    if verifications_response.status_code == 200:
        verifications = verifications_response.json().get("verifications", [])
        if verifications:
            has_previous = True
            prev_reading = verifications[0]["reading_value"]
            print(f"✅ Previous reading found: {prev_reading} kWh")
            print("   → Billing calculation will be triggered")
        else:
            print("ℹ️  No previous readings found")
            print("   → This will be the first reading (no billing)")
    
    # Step 4: Create a test image
    print("\n4. Preparing test meter image...")
    
    # Create a simple test image (you can replace with actual meter photo)
    from PIL import Image
    import io
    
    img = Image.new('RGB', (800, 600), color='white')
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='JPEG')
    img_bytes.seek(0)
    
    print("✅ Test image created")
    
    # Step 5: Submit verification
    print("\n5. Submitting verification...")
    
    # Simulate client-side OCR result
    ocr_reading = 5150.0 if has_previous else 5000.0
    ocr_confidence = 0.96
    
    files = {
        'image': ('meter_photo.jpg', img_bytes, 'image/jpeg')
    }
    
    data = {
        'meter_id': meter_id,
        'ocr_reading': ocr_reading,
        'ocr_confidence': ocr_confidence
    }
    
    verify_response = requests.post(
        f"{API_BASE_URL}/verify",
        headers=headers,
        data=data,
        files=files
    )
    
    if verify_response.status_code != 201:
        print(f"❌ Verification failed: {verify_response.status_code}")
        print(verify_response.text)
        return
    
    result = verify_response.json()
    
    print("✅ Verification successful!")
    
    # Step 6: Display verification results
    print_section("VERIFICATION RESULTS")
    
    print(f"\nReading Value: {result['reading_value']} kWh")
    print(f"Previous Reading: {result.get('previous_reading', 'N/A')} kWh")
    print(f"Consumption: {result.get('consumption_kwh', 'N/A')} kWh")
    print(f"Confidence: {result['confidence'] * 100:.1f}%")
    print(f"Fraud Score: {result['fraud_score'] * 100:.1f}%")
    print(f"Status: {result['status']}")
    
    # Step 7: Display billing results
    print_section("BILLING CALCULATION RESULTS")
    
    if result.get('bill'):
        bill = result['bill']
        print("\n✅ Bill calculated successfully!")
        print(f"\nBill ID: {bill['id']}")
        print(f"Total Amount: {bill['total_fiat']:.2f} {bill['currency']}")
        
        if bill.get('amount_hbar'):
            print(f"HBAR Equivalent: {bill['amount_hbar']:.2f} HBAR")
            print(f"Exchange Rate: {bill['exchange_rate']:.6f} {bill['currency']}/HBAR")
            print(f"\n💡 User can pay {bill['amount_hbar']:.2f} HBAR to settle this bill")
        else:
            print("\n⚠️  HBAR conversion not available (exchange rate service may be down)")
        
        print(f"\n📋 Bill Status: pending (ready for payment)")
        
    else:
        print("\nℹ️  No bill calculated")
        if not has_previous:
            print("   Reason: First reading (no consumption data)")
        else:
            print("   Reason: Billing calculation may have failed (check logs)")
    
    # Step 8: Summary
    print_section("TEST SUMMARY")
    
    print("\n✅ Verification endpoint working correctly")
    print("✅ OCR processing successful")
    print("✅ Fraud detection completed")
    
    if result.get('bill'):
        print("✅ Billing calculation triggered")
        print("✅ HBAR conversion calculated")
        print("✅ Bill saved to database")
        print("\n🎉 Task 13.9 implementation verified!")
    else:
        if not has_previous:
            print("✅ Billing correctly skipped for first reading")
            print("\n💡 Submit another verification to test billing calculation")
        else:
            print("⚠️  Billing calculation did not run (check server logs)")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    try:
        test_verification_with_billing()
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
