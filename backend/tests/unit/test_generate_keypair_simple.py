"""
Simple test for generate_keypair() method

Uses an existing meter from the database.
"""
import sys
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, os.path.dirname(__file__))

from app.services.smart_meter_service import SmartMeterService
from config import settings

def test_generate_keypair():
    """Test ED25519 keypair generation with existing meter"""
    print("=" * 60)
    print("Testing generate_keypair() method")
    print("=" * 60)
    
    engine = create_engine(settings.database_url)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        # Initialize service
        service = SmartMeterService(db)
        print("✅ SmartMeterService initialized")
        
        # Get an existing meter
        meter_query = text("SELECT id FROM meters LIMIT 1")
        meter_result = db.execute(meter_query).fetchone()
        
        if not meter_result:
            print("❌ No meters found in database. Please create a meter first.")
            return False
        
        test_meter_id = str(meter_result[0])
        print(f"✅ Using existing meter: {test_meter_id}")
        
        # Clean up any existing keypair
        cleanup_query = text("DELETE FROM smart_meter_keys WHERE meter_id = :meter_id")
        db.execute(cleanup_query, {'meter_id': test_meter_id})
        db.commit()
        print(f"✅ Cleaned up existing keypair (if any)")
        
        # Generate keypair
        print(f"\n🔑 Generating ED25519 keypair...")
        result = service.generate_keypair(test_meter_id)
        
        # Verify result
        print("\n✅ Keypair generated successfully!")
        print(f"   Meter ID: {result['meter_id']}")
        print(f"   Algorithm: {result['algorithm']}")
        print(f"   Created at: {result['created_at']}")
        print(f"   Public key preview: {result['public_key'][:80]}...")
        
        # Verify in database
        verify_query = text("""
            SELECT algorithm, 
                   LENGTH(public_key) as pub_len,
                   LENGTH(private_key_encrypted) as priv_len
            FROM smart_meter_keys
            WHERE meter_id = :meter_id
        """)
        db_result = db.execute(verify_query, {'meter_id': test_meter_id}).fetchone()
        
        print("\n✅ Verified in database:")
        print(f"   Algorithm: {db_result[0]}")
        print(f"   Public key length: {db_result[1]} bytes")
        print(f"   Encrypted private key length: {db_result[2]} bytes")
        
        # Test duplicate prevention
        print("\n🔒 Testing duplicate prevention...")
        try:
            service.generate_keypair(test_meter_id)
            print("❌ Should have raised error for duplicate")
            return False
        except Exception as e:
            if "already exists" in str(e):
                print(f"✅ Duplicate prevention works")
            else:
                print(f"❌ Unexpected error: {e}")
                return False
        
        # Test get_public_key
        print("\n🔍 Testing get_public_key()...")
        public_key = service.get_public_key(test_meter_id)
        if public_key == result['public_key']:
            print("✅ get_public_key() works correctly")
        else:
            print("❌ Public key mismatch")
            return False
        
        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED!")
        print("=" * 60)
        print("\nNote: Keypair left in database for further testing.")
        print(f"To clean up, run: DELETE FROM smart_meter_keys WHERE meter_id = '{test_meter_id}';")
        
        return True
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    success = test_generate_keypair()
    sys.exit(0 if success else 1)
