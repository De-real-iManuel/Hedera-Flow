#!/usr/bin/env python3
"""Test prepaid token preview"""
import requests
import json

token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI3OTBiNzhiMC1hY2E0LTQ1YTMtOGIzNC0yZDkyNjE4NzBjNWEiLCJlbWFpbCI6Im5pY3hicm93bjM1QGdtYWlsLmNvbSIsImNvdW50cnlfY29kZSI6Ik5HIiwiaGVkZXJhX2FjY291bnRfaWQiOiIwLjAuVEVTVF81N2VjMjk5YyIsImV4cCI6MTc3NTIzMjUzNSwiaWF0IjoxNzcyNjQwNTM1LCJ0eXBlIjoiYWNjZXNzIn0.0sh0LFQt5OBEt3_TsBC-jKyBVMcdGBCsEkmJvkl8kKo"

headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

data = {
    "meter_id": "029e73b0-9235-45aa-bdf3-900eabe87b76",
    "amount_fiat": 1000,
    "currency": "NGN",
    "payment_method": "HBAR"
}

try:
    response = requests.post(
        "http://localhost:8000/api/prepaid/preview",
        headers=headers,
        json=data
    )
    
    if response.status_code == 200:
        result = response.json()
        print("✓ Preview successful!")
        print(f"\nPreview Details:")
        print(f"  Amount: {result['amount_fiat']} {result['currency']}")
        print(f"  HBAR needed: {result['amount_hbar']}")
        print(f"  Units: {result['units_kwh']} kWh")
        print(f"  Exchange rate: {result['exchange_rate']}")
        print(f"  Tariff rate: {result['tariff_rate']} {result['currency']}/kWh")
    else:
        print(f"✗ Error {response.status_code}")
        print(response.text)
        
except Exception as e:
    print(f"✗ Exception: {e}")
