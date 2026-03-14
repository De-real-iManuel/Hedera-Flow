#!/usr/bin/env python3
"""
Test script to verify the prepaid token buy endpoint is working
"""
import requests
import json

# Test data
test_data = {
    "meter_id": "123e4567-e89b-12d3-a456-426614174001",
    "amount_fiat": 50.0,
    "currency": "NGN",
    "payment_method": "HBAR"
}

# Make request to buy endpoint (without auth - should get 401)
try:
    response = requests.post(
        "http://localhost:8000/api/prepaid/buy",
        json=test_data,
        headers={"Content-Type": "application/json"}
    )
    
    print(f"Status Code: {response.status_code}")
    print(f"Response Headers: {dict(response.headers)}")
    print(f"Response Body: {response.text}")
    
    if response.status_code == 401:
        print("\n✅ Endpoint is accessible (401 = authentication required)")
    else:
        print(f"\n❌ Unexpected status code: {response.status_code}")
        
except Exception as e:
    print(f"❌ Request failed: {e}")