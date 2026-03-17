#!/usr/bin/env python3
"""Test creating a meter directly"""
import sys
sys.path.insert(0, '.')

from app.core.database import SessionLocal
from app.models.meter import Meter, MeterTypeEnum, BandClassificationEnum
from uuid import UUID

# User ID and provider ID from request
user_id = UUID("790b78b0-aca4-45a3-8b34-2d9261870c5a")
provider_id = UUID("ea3cc7e9-dc21-4c86-bb92-fb36f69ce7fd")

db = SessionLocal()
try:
    new_meter = Meter(
        user_id=user_id,
        meter_id="0137234144889",
        utility_provider_id=provider_id,
        state_province="Rivers",
        utility_provider="Port Harcourt Electricity Distribution Company",
        meter_type=MeterTypeEnum.PREPAID,
        band_classification=BandClassificationEnum.C,
        address="10b Agip road, Port Harcourt",
        is_primary=False
    )
    
    db.add(new_meter)
    db.commit()
    db.refresh(new_meter)
    
    print(f"SUCCESS! Meter created with ID: {new_meter.id}")
    print(f"Meter ID: {new_meter.meter_id}")
    
except Exception as e:
    db.rollback()
    print(f"ERROR: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
    
finally:
    db.close()
