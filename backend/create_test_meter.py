#!/usr/bin/env python3
"""
Create a test meter for the test user
"""
from app.core.database import get_db
from app.models.meter import Meter
from sqlalchemy.orm import Session
import uuid

def create_test_meter():
    """Create a test meter for the test user"""
    
    db = next(get_db())
    
    test_user_id = "6bbdb0df-7c97-48ef-8f80-383c0fb477fd"
    
    # Check if test meter already exists
    existing_meter = db.query(Meter).filter(
        Meter.user_id == test_user_id,
        Meter.meter_id == "TEST12345"
    ).first()
    
    if existing_meter:
        print("Test meter already exists")
        print(f"Meter ID: {existing_meter.meter_id}")
        print(f"UUID: {existing_meter.id}")
        return existing_meter.id
    
    # Create new test meter
    test_meter = Meter(
        id=uuid.uuid4(),
        user_id=uuid.UUID(test_user_id),
        utility_provider_id=uuid.UUID("4797ed06-cc72-40a3-a5ca-2e1d3667acf8"),  # Abuja Electricity
        meter_id="TEST12345",
        state_province="Madrid",
        utility_provider="TestCorp",
        meter_type="postpaid",
        band_classification="A",  # A for residential
        address="Test Address 123",
        is_primary=True
    )
    
    try:
        db.add(test_meter)
        db.commit()
        print("Test meter created successfully!")
        print(f"Meter ID: {test_meter.meter_id}")
        print(f"UUID: {test_meter.id}")
        return test_meter.id
        
    except Exception as e:
        db.rollback()
        print(f"Failed to create test meter: {e}")
        return None
    finally:
        db.close()

if __name__ == "__main__":
    meter_uuid = create_test_meter()
    if meter_uuid:
        print(f"\nUse this UUID in your test: {meter_uuid}")