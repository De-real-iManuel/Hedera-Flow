#!/usr/bin/env python3
"""
Create a test scenario with positive consumption to generate bills
"""
import sys
import uuid
from decimal import Decimal
from datetime import datetime, timezone

# Import config first
sys.path.append('.')
from config import settings
from app.core.database import get_db
from sqlalchemy import text

def create_positive_consumption_scenario():
    """Create a meter reading scenario that will generate a bill"""
    
    # Test user and meter IDs
    user_id = "790b78b0-aca4-45a3-8b34-2d9261870c5a"
    meter_id = "029e73b0-9235-45aa-bdf3-900eabe87b76"
    
    db = next(get_db())
    
    try:
        # First, update the meter to have a lower previous reading
        # This will ensure positive consumption when we scan
        print("Setting up positive consumption scenario...")
        
        # Check current meter state
        check_query = text("""
            SELECT meter_id, state_province, utility_provider 
            FROM meters 
            WHERE id = :meter_id AND user_id = :user_id
        """)
        
        result = db.execute(check_query, {
            'meter_id': uuid.UUID(meter_id),
            'user_id': uuid.UUID(user_id)
        })
        
        meter_info = result.fetchone()
        if not meter_info:
            print("❌ Meter not found")
            return False
            
        print(f"✅ Found meter: {meter_info[0]} in {meter_info[1]}, {meter_info[2]}")
        
        # Create a verification record with a lower previous reading
        # This simulates a scenario where the next scan will show positive consumption
        verification_id = uuid.uuid4()
        
        insert_verification_query = text("""
            INSERT INTO verifications (
                id, user_id, meter_id, reading_value, 
                previous_reading, consumption_kwh, 
                image_ipfs_hash, ocr_engine, confidence,
                fraud_score, fraud_flags, status,
                hcs_topic_id, hcs_sequence_number, created_at
            ) VALUES (
                :id, :user_id, :meter_id, :reading_value,
                :previous_reading, :consumption_kwh,
                :image_ipfs_hash, :ocr_engine, :confidence,
                :fraud_score, :fraud_flags, :status,
                :hcs_topic_id, :hcs_sequence_number, :created_at
            )
        """)
        
        # Set a baseline reading that's lower than what we'll scan next
        baseline_reading = Decimal('82000.0')  # Lower than the 83372.0 we scanned
        
        db.execute(insert_verification_query, {
            'id': verification_id,
            'user_id': uuid.UUID(user_id),
            'meter_id': uuid.UUID(meter_id),
            'reading_value': baseline_reading,
            'previous_reading': Decimal('81500.0'),  # Even lower previous
            'consumption_kwh': Decimal('500.0'),  # 500 kWh consumption
            'image_ipfs_hash': 'ipfs://baseline-reading-test',
            'ocr_engine': 'test_setup',
            'confidence': Decimal('1.0'),
            'fraud_score': Decimal('0.0'),
            'fraud_flags': '{}',
            'status': 'VERIFIED',
            'hcs_topic_id': '0.0.8052391',
            'hcs_sequence_number': 1,
            'created_at': datetime.now(timezone.utc)
        })
        
        db.commit()
        
        print(f"✅ Created baseline verification record")
        print(f"   Reading: {baseline_reading} kWh")
        print(f"   Previous: 81500.0 kWh")
        print(f"   Consumption: 500.0 kWh")
        print(f"\n📋 Next scan scenario:")
        print(f"   If you scan 83372.0 kWh (from your previous test)")
        print(f"   Consumption will be: 83372.0 - 82000.0 = 1372.0 kWh")
        print(f"   This should generate a bill!")
        
        return True
        
    except Exception as e:
        print(f"❌ Error setting up scenario: {e}")
        db.rollback()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    success = create_positive_consumption_scenario()
    if success:
        print("\n🎉 Positive consumption scenario ready!")
        print("Now scan your meter again to generate a bill.")
    else:
        print("\n❌ Failed to set up scenario")