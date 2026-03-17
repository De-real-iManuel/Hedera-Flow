"""
Test script for generate_keypair() method in SmartMeterService

This script verifies that the ED25519 keypair generation works correctly.
"""
import sys
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add backend to path
sys.path.insert(0, os.path.dirname(__file__))

from app.services.smart_meter_service import SmartMeterService
from config import settings

def test_generate_keypair():
    """Test ED25519 keypair generation"""
    print("=" * 60)
    print("Testing generate_keypair() method")
    print("=" * 60)
    
    # Create database connection
    engine = create_engine(settings.database_url)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        # Initialize service
        service = SmartMeterService(db)
        print("✅ SmartMeterService initialized")
        
        # Create a test meter_id (valid UUID)
        import uuid
        test_meter_id = str(uuid.uuid4())
        
        # Create a test user and meter in the database
        test_user_id = str(uuid.uuid4())
        
        # Insert test user
        user_insert = text("""
            INSERT INTO users (id, email, password_hash, full_name, country_code, currency)
            VALUES (:id, :email, :password_hash, :full_name, :country_code, :currency)
        """)
        db.execute(user_insert, {
            'id': test_user_id,
            'email': 'test@example.com',
            'password_hash': 'test_hash',
            'full_name': 'Test User',
            'country_code': 'ES',
            'currency': 'EUR'
        })
        
        # Insert test meter
        meter_insert = text("""
            INSERT INTO meters (id, user_id, meter_number, utility_provider_id, meter_type, status)
            VALUES (:id, :user_id, :meter_number, :utility_provider_id, :meter_type, :status)
        """)
        
        # Get a utility provider ID
        utility_query = text("SELECT id FROM utility_providers LIMIT 1")
        utility_result = db.execute(utility_query).fetchone()
        utility_id = utility_result[0] if utility_result else None
        
        if not utility_id:
            # Create a test utility provider
            utility_id = str(uuid.uuid4())
            utility_insert = text("""
                INSERT INTO utility_providers (id, name, country_code, provider_type)
                VALUES (:id, :name, :country_code, :provider_type)
            """)
            db.execute(utility_insert, {
                'id': utility_id,
                'name': 'Test Utility',
                'country_code': 'ES',
                'provider_type': 'electricity'
            })
        
        db.execute(meter_insert, {
            'id': test_meter_id,
            'user_id': test_user_id,
            'meter_number': 'TEST-METER-001',
            'utility_provider_id': utility_id,
            'meter_type': 'smart',
            'status': 'active'
        })
        db.commit()
        
        # Clean up any existing keypair for this test meter
        cleanup_query = text("""
            DELETE FROM smart_meter_keys
            WHERE meter_id = :meter_id
        """)
        db.execute(cleanup_query, {'meter_id': test_meter_id})
        db.commit()
        print(f"✅ Cleaned up existing test data for meter {test_meter_id}")
        
        # Generate keypair
        print(f"\n🔑 Generating ED25519 keypair for meter {test_meter_id}...")
        result = service.generate_keypair(test_meter_id)
        
        # Verify result structure
        assert 'meter_id' in result, "Result missing meter_id"
        assert 'public_key' in result, "Result missing public_key"
        assert 'algorithm' in result, "Result missing algorithm"
        assert 'created_at' in result, "Result missing created_at"
        
        assert result['meter_id'] == test_meter_id, "Meter ID mismatch"
        assert result['algorithm'] == 'ED25519', "Algorithm should be ED25519"
        assert result['public_key'].startswith('-----BEGIN PUBLIC KEY-----'), "Invalid public key format"
        
        print("\n✅ Keypair generated successfully!")
        print(f"   Meter ID: {result['meter_id']}")
        print(f"   Algorithm: {result['algorithm']}")
        print(f"   Created at: {result['created_at']}")
        print(f"   Public key (first 50 chars): {result['public_key'][:50]}...")
        
        # Verify keypair is stored in database
        verify_query = text("""
            SELECT 
                meter_id, 
                algorithm, 
                LENGTH(public_key) as public_key_len,
                LENGTH(private_key_encrypted) as private_key_len,
                encryption_iv IS NOT NULL as has_iv
            FROM smart_meter_keys
            WHERE meter_id = :meter_id
        """)
        
        db_result = db.execute(verify_query, {'meter_id': test_meter_id}).fetchone()
        
        assert db_result is not None, "Keypair not found in database"
        print("\n✅ Keypair verified in database:")
        print(f"   Meter ID: {db_result[0]}")
        print(f"   Algorithm: {db_result[1]}")
        print(f"   Public key length: {db_result[2]} bytes")
        print(f"   Encrypted private key length: {db_result[3]} bytes")
        print(f"   Has encryption IV: {db_result[4]}")
        
        # Test that duplicate generation fails
        print("\n🔒 Testing duplicate prevention...")
        try:
            service.generate_keypair(test_meter_id)
            print("❌ ERROR: Should have raised SmartMeterError for duplicate")
            return False
        except Exception as e:
            if "already exists" in str(e):
                print(f"✅ Duplicate prevention works: {e}")
            else:
                print(f"❌ Unexpected error: {e}")
                return False
        
        # Test get_public_key method
        print("\n🔍 Testing get_public_key() method...")
        public_key = service.get_public_key(test_meter_id)
        assert public_key == result['public_key'], "Public key mismatch"
        print("✅ get_public_key() works correctly")
        
        # Test keypair_exists method
        print("\n🔍 Testing keypair_exists() method...")
        exists = service.keypair_exists(test_meter_id)
        assert exists is True, "keypair_exists should return True"
        print("✅ keypair_exists() works correctly")
        
        # Clean up
        db.execute(cleanup_query, {'meter_id': test_meter_id})
        db.execute(text("DELETE FROM meters WHERE id = :id"), {'id': test_meter_id})
        db.execute(text("DELETE FROM users WHERE id = :id"), {'id': test_user_id})
        db.commit()
        print("\n🧹 Cleaned up test data")
        
        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED!")
        print("=" * 60)
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
