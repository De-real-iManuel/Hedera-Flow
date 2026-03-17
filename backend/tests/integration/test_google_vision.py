#!/usr/bin/env python3
"""
Test Google Cloud Vision API configuration
"""
import os
import sys

# Import config first to set environment variables
sys.path.append('.')
from config import settings

from google.cloud import vision
from google.api_core import exceptions as google_exceptions
import json

def test_google_vision_setup():
    """Test Google Cloud Vision API setup"""
    
    print("Testing Google Cloud Vision API setup...")
    
    # Check environment variable
    credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
    print(f"GOOGLE_APPLICATION_CREDENTIALS: {credentials_path}")
    
    if not credentials_path:
        print("❌ GOOGLE_APPLICATION_CREDENTIALS environment variable not set")
        return False
    
    # Check if credentials file exists
    if not os.path.exists(credentials_path):
        print(f"❌ Credentials file not found: {credentials_path}")
        return False
    
    print(f"✅ Credentials file exists: {credentials_path}")
    
    # Try to load and validate credentials
    try:
        with open(credentials_path, 'r') as f:
            creds = json.load(f)
        
        required_fields = ['type', 'project_id', 'private_key', 'client_email']
        missing_fields = [field for field in required_fields if field not in creds]
        
        if missing_fields:
            print(f"❌ Missing required fields in credentials: {missing_fields}")
            return False
        
        print(f"✅ Credentials file format is valid")
        print(f"   Project ID: {creds['project_id']}")
        print(f"   Client Email: {creds['client_email']}")
        
    except Exception as e:
        print(f"❌ Error reading credentials file: {e}")
        return False
    
    # Try to initialize Vision API client
    try:
        print("\nTesting Vision API client initialization...")
        client = vision.ImageAnnotatorClient()
        print("✅ Vision API client initialized successfully")
        
        # Test with a simple image (minimal JPEG)
        print("\nTesting OCR with minimal image...")
        
        # Create a minimal test image (just JPEG headers)
        test_image_bytes = b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c $.\' ",#\x1c\x1c(7),01444\x1f\'9=82<.342\xff\xc0\x00\x11\x08\x00\x01\x00\x01\x01\x01\x11\x00\x02\x11\x01\x03\x11\x01\xff\xc4\x00\x14\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x08\xff\xc4\x00\x14\x10\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xda\x00\x0c\x03\x01\x00\x02\x11\x03\x11\x00\x3f\x00\xaa\xff\xd9'
        
        image = vision.Image(content=test_image_bytes)
        response = client.text_detection(image=image)
        
        if response.error.message:
            print(f"⚠️  Vision API returned error: {response.error.message}")
        else:
            print("✅ Vision API call successful (no text detected in test image - expected)")
        
        return True
        
    except google_exceptions.Forbidden as e:
        print(f"❌ Vision API access forbidden: {e}")
        print("   This usually means:")
        print("   1. Vision API is not enabled for this project")
        print("   2. Service account doesn't have proper permissions")
        return False
        
    except google_exceptions.Unauthenticated as e:
        print(f"❌ Authentication failed: {e}")
        print("   This usually means:")
        print("   1. Invalid credentials")
        print("   2. Service account key is expired or revoked")
        return False
        
    except Exception as e:
        print(f"❌ Vision API client initialization failed: {e}")
        return False

def check_project_and_api():
    """Check if the project exists and Vision API is enabled"""
    
    print("\n" + "="*50)
    print("GOOGLE CLOUD PROJECT SETUP GUIDE")
    print("="*50)
    
    print("\nTo fix Vision API issues, follow these steps:")
    print("\n1. Create/Verify Google Cloud Project:")
    print("   - Go to: https://console.cloud.google.com/")
    print("   - Create a new project or select existing one")
    print("   - Note the Project ID")
    
    print("\n2. Enable Vision API:")
    print("   - Go to: https://console.cloud.google.com/apis/library/vision.googleapis.com")
    print("   - Click 'Enable' if not already enabled")
    
    print("\n3. Create Service Account:")
    print("   - Go to: https://console.cloud.google.com/iam-admin/serviceaccounts")
    print("   - Click 'Create Service Account'")
    print("   - Give it a name like 'hedera-flow-vision'")
    print("   - Grant role: 'Cloud Vision AI Service Agent'")
    print("   - Create and download JSON key")
    
    print("\n4. Update credentials file:")
    print("   - Replace backend/credentials/google-vision-key.json with your downloaded key")
    print("   - Update GOOGLE_CLOUD_PROJECT_ID in .env file")
    
    print("\n5. Test the setup:")
    print("   - Run this script again to verify")

if __name__ == "__main__":
    success = test_google_vision_setup()
    
    if not success:
        check_project_and_api()
    else:
        print("\n🎉 Google Cloud Vision API is properly configured!")