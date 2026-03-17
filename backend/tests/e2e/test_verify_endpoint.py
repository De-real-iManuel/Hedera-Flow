#!/usr/bin/env python3
"""
Test script for the verify endpoint
"""
import requests
import json
from pathlib import Path

# Test data
API_BASE = "http://localhost:8000/api"

def test_verify_endpoint():
    """Test the verify endpoint with minimal data"""
    
    # Create a small test image file
    test_image_path = Path("test_image.jpg")
    if not test_image_path.exists():
        # Create a minimal JPEG file (just header bytes)
        with open(test_image_path, "wb") as f:
            # Minimal JPEG header
            f.write(b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c $.\' ",#\x1c\x1c(7),01444\x1f\'9=82<.342\xff\xc0\x00\x11\x08\x00\x01\x00\x01\x01\x01\x11\x00\x02\x11\x01\x03\x11\x01\xff\xc4\x00\x14\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x08\xff\xc4\x00\x14\x10\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xda\x00\x0c\x03\x01\x00\x02\x11\x03\x11\x00\x3f\x00\xaa\xff\xd9')
    
    # Test without authentication first
    print("Testing verify endpoint without authentication...")
    
    with open(test_image_path, "rb") as f:
        files = {"image": f}
        data = {"meter_id": "029e73b0-9235-45aa-bdf3-900eabe87b76"}  # Use existing meter ID
        
        try:
            response = requests.post(f"{API_BASE}/verify/scan", files=files, data=data)
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.text}")
            
            if response.status_code == 401:
                print("Authentication required - this is expected")
            elif response.status_code == 500:
                print("Internal server error - checking logs...")
            else:
                print("Unexpected response")
                
        except Exception as e:
            print(f"Request failed: {e}")
    
    # Clean up
    if test_image_path.exists():
        test_image_path.unlink()

if __name__ == "__main__":
    test_verify_endpoint()