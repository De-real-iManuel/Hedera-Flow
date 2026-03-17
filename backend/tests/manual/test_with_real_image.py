#!/usr/bin/env python3
"""
Test verification endpoint with a real image containing text
"""
import requests
import json
from PIL import Image, ImageDraw, ImageFont
import io
import sys

# Import config first to set environment variables
sys.path.append('.')
from config import settings

API_BASE = "http://localhost:8000/api"

def create_test_meter_image():
    """Create a simple test image with meter reading text"""
    
    # Create a simple image with text that looks like a meter reading
    img = Image.new('RGB', (400, 200), color='white')
    draw = ImageDraw.Draw(img)
    
    # Try to use a default font, fallback to basic if not available
    try:
        font = ImageFont.truetype("arial.ttf", 40)
    except:
        font = ImageFont.load_default()
    
    # Draw meter reading text
    draw.text((50, 50), "12345.67", fill='black', font=font)
    draw.text((50, 100), "kWh", fill='black', font=font)
    
    # Convert to bytes
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='JPEG', quality=95)
    img_bytes.seek(0)
    
    return img_bytes.getvalue()

def test_verification_with_real_image():
    """Test the verification endpoint with a realistic image"""
    
    print("Creating test meter image...")
    image_data = create_test_meter_image()
    print(f"Created image: {len(image_data)} bytes")
    
    # Login first
    print("\nLogging in...")
    login_data = {
        "username": "testuser@hederaflow.com",
        "password": "TestPassword123!"
    }
    
    login_response = requests.post(f"{API_BASE}/auth/login", data=login_data)
    if login_response.status_code != 200:
        print(f"Login failed: {login_response.text}")
        return
    
    auth_data = login_response.json()
    token = auth_data.get("token")
    print("✅ Login successful")
    
    # Test verification endpoint
    print("\nTesting verification endpoint with realistic image...")
    
    headers = {"Authorization": f"Bearer {token}"}
    files = {"image": ("meter_reading.jpg", image_data, "image/jpeg")}
    data = {"meter_id": "79c3c974-f1e3-432e-8e6e-0fefa91f1835"}
    
    verify_response = requests.post(
        f"{API_BASE}/verify/scan", 
        files=files, 
        data=data, 
        headers=headers
    )
    
    print(f"Status Code: {verify_response.status_code}")
    
    if verify_response.status_code == 201:  # 201 Created is the success status
        print("✅ Verification successful!")
        result = verify_response.json()
        print(f"Reading: {result.get('reading_value')}")
        print(f"Confidence: {result.get('confidence')}")
        print(f"Status: {result.get('status')}")
        print(f"Fraud Score: {result.get('fraud_score')}")
        print(f"OCR Engine: {result.get('ocr_engine')}")
        print(f"Raw OCR Text: {result.get('raw_ocr_text')}")
        print(f"HCS Sequence: {result.get('hcs_sequence_number')}")
        if result.get('bill'):
            print(f"Bill Total: {result['bill']['total_fiat']} {result['bill']['currency']}")
        else:
            print("No bill generated (no consumption change)")
    else:
        print(f"❌ Verification failed: {verify_response.text}")

if __name__ == "__main__":
    test_verification_with_real_image()