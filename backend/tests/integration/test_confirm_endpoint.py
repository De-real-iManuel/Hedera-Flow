"""Test the confirm endpoint to see what error it returns"""
import requests

# You'll need to get a real token first by logging in
# For now, let's just test if the endpoint exists

url = "http://localhost:8000/api/prepaid/confirm-payment"

# Test with dummy data to see the error
data = {
    'token_id': 'TOKEN-NG-2026-010',
    'hedera_tx_id': '0xb86ff5eaef4812c6427ed5056b8f4f3c5f6c938e0917d0a04c782d11daa7d7d8'
}

try:
    response = requests.post(url, data=data)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
    if response.status_code != 200:
        print(f"Error details: {response.json()}")
except Exception as e:
    print(f"Error: {e}")
