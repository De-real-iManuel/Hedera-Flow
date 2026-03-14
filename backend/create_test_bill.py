#!/usr/bin/env python3
"""
Create a test bill for payment flow testing
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

def create_test_bill():
    """Create a test bill for the test user"""
    
    # Test user and meter IDs from the verification
    user_id = "790b78b0-aca4-45a3-8b34-2d9261870c5a"
    meter_id = "029e73b0-9235-45aa-bdf3-900eabe87b76"
    
    db = next(get_db())
    
    try:
        # Create a test bill
        bill_id = uuid.uuid4()
        
        insert_bill_query = text("""
            INSERT INTO bills (
                id, user_id, meter_id, verification_id,
                consumption_kwh, base_charge, taxes, subsidies, total_fiat, currency,
                tariff_id, tariff_snapshot, amount_hbar, exchange_rate,
                exchange_rate_timestamp, status, created_at
            ) VALUES (
                :id, :user_id, :meter_id, :verification_id,
                :consumption_kwh, :base_charge, :taxes, :subsidies, :total_fiat, :currency,
                :tariff_id, :tariff_snapshot, :amount_hbar, :exchange_rate,
                :exchange_rate_timestamp, :status, :created_at
            ) RETURNING id, total_fiat, currency, amount_hbar, exchange_rate
        """)
        
        result = db.execute(
            insert_bill_query,
            {
                'id': bill_id,
                'user_id': uuid.UUID(user_id),
                'meter_id': uuid.UUID(meter_id),
                'verification_id': None,  # No specific verification
                'consumption_kwh': Decimal('150.0'),  # 150 kWh consumption
                'base_charge': Decimal('25.00'),
                'taxes': Decimal('5.00'),
                'subsidies': Decimal('0.00'),
                'total_fiat': Decimal('30.00'),
                'currency': 'NGN',
                'tariff_id': None,
                'tariff_snapshot': '{}',
                'amount_hbar': Decimal('0.5'),  # Assuming 60 NGN/HBAR rate
                'exchange_rate': Decimal('60.0'),
                'exchange_rate_timestamp': datetime.now(timezone.utc),
                'status': 'pending',
                'created_at': datetime.now(timezone.utc)
            }
        )
        
        db.commit()
        bill_row = result.fetchone()
        
        print(f"✅ Test bill created successfully!")
        print(f"   Bill ID: {bill_row[0]}")
        print(f"   Amount: {bill_row[1]} {bill_row[2]}")
        print(f"   HBAR Amount: {bill_row[3]}")
        print(f"   Exchange Rate: {bill_row[4]} {bill_row[2]}/HBAR")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating test bill: {e}")
        db.rollback()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    success = create_test_bill()
    if success:
        print("\n🎉 Test bill created! You can now test the payment flow.")
    else:
        print("\n❌ Failed to create test bill")