"""
Simple test for POST /api/verify endpoint
Tests the basic verification flow
"""
import pytest
import sys
import os
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont

# Add backend directory to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import uuid
from datetime import datetime

# Import app components
from app.core.database import Base, get_db
from app.core.dependencies import get_current_user
from fastapi import FastAPI
from app.api.routes import api_router

# Test database setup
TEST_DATABASE_URL = "sqlite:///./test_verify.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables
Base.metadata.create_all(bind=engine)


def override_get_db():
    """Override database dependency for testing"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


# Create FastAPI app for testing
app = FastAPI(title="Hedera Flow Test")
app.include_router(api_router, prefix="/api")

# Mock current user dependency
def override_get_current_user():
    return {
        "user_id": "test-user-id",
        "email": "test@verify.com"
    }

# Override dependencies
app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[get_current_user] = override_get_current_user

# Create test client
client = TestClient(app)


def create_test_image():
    """Create a simple test image with a number"""
    # Create a white image
    img = Image.new('RGB', (400, 200), color='white')
    draw = ImageDraw.Draw(img)
    
    # Draw a simple number (simulating meter reading)
    try:
        font = ImageFont.truetype("arial.ttf", 60)
    except:
        font = ImageFont.load_default()
    
    # Draw the number 5142.7
    draw.text((100, 70), "5142.7", fill='black', font=font)
    
    # Save to bytes
    img_bytes = BytesIO()
    img.save(img_bytes, format='JPEG')
    img_bytes.seek(0)
    
    return img_bytes


def test_verify_endpoint_basic():
    """Test basic verification endpoint functionality"""
    print("\n" + "="*60)
    print("TEST: POST /api/verify - Basic Verification Flow")
    print("="*60)
    
    # Setup test data
    db = TestingSessionLocal()
    
    try:
        # Step 1: Create test user
        user_id = str(uuid.uuid4())
        
        db.execute(text("""
            INSERT INTO users (id, email, password_hash, country_code, hedera_account_id, created_at)
            VALUES (:id, :email, :password_hash, :country_code, :hedera_account_id, :created_at)
        """), {
            'id': user_id,
            'email': 'test@verify.com',
            'password_hash': 'hashed_password',
            'country_code': 'ES',
            'hedera_account_id': '0.0.12345',
            'created_at': datetime.utcnow()
        })
        
        # Step 2: Create test meter
        meter_id = str(uuid.uuid4())
        
        db.execute(text("""
            INSERT INTO meters (id, user_id, meter_id, utility_provider_id, state_province, 
                              utility_provider, meter_type, created_at)
            VALUES (:id, :user_id, :meter_id, :utility_provider_id, :state_province,
                   :utility_provider, :meter_type, :created_at)
        """), {
            'id': meter_id,
            'user_id': user_id,
            'meter_id': 'ESP-TEST-001',
            'utility_provider_id': None,
            'state_province': 'Madrid',
            'utility_provider': 'Iberdrola',
            'meter_type': 'postpaid',
            'created_at': datetime.utcnow()
        })
        
        db.commit()
        
        print(f"\n✅ Test user created: {user_id}")
        print(f"✅ Test meter created: {meter_id}")
        
        # Step 3: Override the current user for this test
        def override_current_user_for_test():
            return {
                "user_id": user_id,
                "email": "test@verify.com"
            }
        
        app.dependency_overrides[get_current_user] = override_current_user_for_test
        
        print(f"✅ User authentication mocked")
        
        # Step 4: Create test image
        test_image = create_test_image()
        
        print(f"✅ Test image created")
        
        # Step 5: Call verify endpoint
        print(f"\n📤 Calling POST /api/verify...")
        
        response = client.post(
            "/api/verify",
            data={
                "meter_id": meter_id,
                "ocr_reading": "5142.7",
                "ocr_confidence": "0.95"
            },
            files={
                "image": ("meter.jpg", test_image, "image/jpeg")
            }
        )
        
        print(f"\n📥 Response Status: {response.status_code}")
        
        # Step 6: Verify response
        if response.status_code == 201:
            data = response.json()
            print(f"\n✅ VERIFICATION SUCCESSFUL!")
            print(f"\nVerification Details:")
            print(f"  - ID: {data.get('id')}")
            print(f"  - Reading: {data.get('reading_value')} kWh")
            print(f"  - Confidence: {data.get('confidence')}")
            print(f"  - Fraud Score: {data.get('fraud_score')}")
            print(f"  - Status: {data.get('status')}")
            print(f"  - OCR Engine: {data.get('ocr_engine')}")
            
            if data.get('hcs_sequence_number'):
                print(f"  - HCS Sequence: {data.get('hcs_sequence_number')}")
            
            # Assertions
            assert data['reading_value'] == 5142.7
            assert data['status'] in ['VERIFIED', 'WARNING', 'DISCREPANCY', 'FRAUD_DETECTED']
            assert 0 <= float(data['confidence']) <= 1
            assert 0 <= float(data['fraud_score']) <= 1
            
            print(f"\n✅ All assertions passed!")
            
        else:
            print(f"\n❌ VERIFICATION FAILED!")
            print(f"Response: {response.text}")
            assert False, f"Expected 201, got {response.status_code}"
        
    finally:
        # Cleanup
        db.execute(text("DELETE FROM verifications WHERE user_id = :user_id"), {'user_id': user_id})
        db.execute(text("DELETE FROM meters WHERE user_id = :user_id"), {'user_id': user_id})
        db.execute(text("DELETE FROM users WHERE id = :id"), {'id': user_id})
        db.commit()
        db.close()
        
        print(f"\n🧹 Test data cleaned up")
    
    print("\n" + "="*60)
    print("TEST COMPLETED SUCCESSFULLY ✅")
    print("="*60)


if __name__ == "__main__":
    test_verify_endpoint_basic()
