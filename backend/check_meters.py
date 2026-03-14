#!/usr/bin/env python3
"""Check meters in database"""
import sys
sys.path.insert(0, '.')

from app.core.database import SessionLocal
from app.models.meter import Meter
from uuid import UUID

# User ID from JWT token
user_id = UUID("790b78b0-aca4-45a3-8b34-2d9261870c5a")

db = SessionLocal()
try:
    # Find all meters
    all_meters = db.query(Meter).all()
    print(f"Total meters in database: {len(all_meters)}")
    
    # Find meters for this user
    user_meters = db.query(Meter).filter(Meter.user_id == user_id).all()
    print(f"Meters for user {user_id}: {len(user_meters)}")
    
    for meter in user_meters:
        print(f"  - Meter ID: {meter.meter_id}, UUID: {meter.id}")
    
    # Check for the specific meter
    specific_meter = db.query(Meter).filter(Meter.meter_id == "0137234144889").all()
    print(f"\nMeters with ID '0137234144889': {len(specific_meter)}")
    for meter in specific_meter:
        print(f"  - User ID: {meter.user_id}, UUID: {meter.id}")
        
finally:
    db.close()
