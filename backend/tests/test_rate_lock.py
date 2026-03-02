"""
Test Rate Lock Functionality
Tests the 5-minute rate lock feature for payment protection against volatility

Requirements:
    - FR-6.13: System shall handle exchange rate volatility with 2% buffer
    - FR-17.4: Set 5-minute rate lock to protect against volatility
    - US-7: Show exchange rate, timestamp, and 5-minute expiry
"""
import pytest
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import time
import json

from app.utils.redis_client import redis_client


class TestRateLock:
    """Test suite for rate lock functionality"""
    
    @pytest.fixture(autouse=True)
    def setup_teardown(self):
        """Setup and teardown for each test"""
        # Setup: Clear any existing rate locks
        keys = redis_client.get_keys_by_pattern("rate_lock:*")
        for key in keys:
            redis_client.client.delete(key)
        
        yield
        
        # Teardown: Clean up test data
        keys = redis_client.get_keys_by_pattern("rate_lock:*")
        for key in keys:
            redis_client.client.delete(key)
    
    def test_create_rate_lock(self):
        """Test creating a rate lock"""
        bill_id = "test-bill-123"
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(minutes=5)
        
        rate_data = {
            'bill_id': bill_id,
            'currency': 'EUR',
            'hbar_price': 0.36,
            'amount_hbar': 251.17,
            'fiat_amount': 85.40,
            'buffer_applied': True,
            'buffer_percentage': 2.0,
            'locked_at': now.isoformat() + 'Z',
            'expires_at': expires_at.isoformat() + 'Z',
            'source': 'coingecko'
        }
        
        # Create rate lock
        result = redis_client.set_rate_lock(bill_id, rate_data)
        
        assert result is True, "Rate lock should be created successfully"
        
        # Verify it was stored
        stored_lock = redis_client.get_rate_lock(bill_id)
        assert stored_lock is not None, "Rate lock should be retrievable"
        assert stored_lock['bill_id'] == bill_id
        assert stored_lock['currency'] == 'EUR'
        assert stored_lock['hbar_price'] == 0.36
        assert stored_lock['amount_hbar'] == 251.17
        assert stored_lock['buffer_applied'] is True
        
        print(f"✅ Rate lock created: {stored_lock['amount_hbar']} HBAR @ {stored_lock['hbar_price']} EUR/HBAR")
    
    def test_rate_lock_ttl(self):
        """Test that rate lock has correct TTL (5 minutes)"""
        bill_id = "test-bill-ttl"
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(minutes=5)
        
        rate_data = {
            'bill_id': bill_id,
            'currency': 'USD',
            'hbar_price': 0.05,
            'amount_hbar': 2000.0,
            'fiat_amount': 100.0,
            'buffer_applied': True,
            'buffer_percentage': 2.0,
            'locked_at': now.isoformat() + 'Z',
            'expires_at': expires_at.isoformat() + 'Z',
            'source': 'coingecko'
        }
        
        redis_client.set_rate_lock(bill_id, rate_data)
        
        # Check TTL
        ttl = redis_client.get_rate_lock_ttl(bill_id)
        
        assert ttl > 0, "TTL should be positive"
        assert ttl <= 300, "TTL should be <= 5 minutes (300 seconds)"
        assert ttl >= 295, "TTL should be close to 5 minutes (allowing for execution time)"
        
        print(f"✅ Rate lock TTL: {ttl} seconds (expected ~300)")
    
    def test_rate_lock_expiry(self):
        """Test that rate lock expires after TTL"""
        bill_id = "test-bill-expiry"
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(seconds=2)  # Short expiry for testing
        
        rate_data = {
            'bill_id': bill_id,
            'currency': 'EUR',
            'hbar_price': 0.36,
            'amount_hbar': 251.17,
            'fiat_amount': 85.40,
            'buffer_applied': True,
            'buffer_percentage': 2.0,
            'locked_at': now.isoformat() + 'Z',
            'expires_at': expires_at.isoformat() + 'Z',
            'source': 'coingecko'
        }
        
        # Create rate lock with 2-second TTL
        redis_client.client.setex(
            f"rate_lock:{bill_id}",
            timedelta(seconds=2),
            json.dumps(rate_data)
        )
        
        # Verify it exists
        lock = redis_client.get_rate_lock(bill_id)
        assert lock is not None, "Rate lock should exist initially"
        
        # Wait for expiry
        print("⏳ Waiting 3 seconds for rate lock to expire...")
        time.sleep(3)
        
        # Verify it expired
        lock = redis_client.get_rate_lock(bill_id)
        assert lock is None, "Rate lock should be expired and return None"
        
        ttl = redis_client.get_rate_lock_ttl(bill_id)
        assert ttl == -2, "TTL should be -2 (key doesn't exist)"
        
        print("✅ Rate lock expired as expected")
    
    def test_validate_rate_lock_valid(self):
        """Test validating a valid rate lock"""
        bill_id = "test-bill-valid"
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(minutes=5)
        
        rate_data = {
            'bill_id': bill_id,
            'currency': 'EUR',
            'hbar_price': 0.36,
            'amount_hbar': 251.17,
            'fiat_amount': 85.40,
            'buffer_applied': True,
            'buffer_percentage': 2.0,
            'locked_at': now.isoformat() + 'Z',
            'expires_at': expires_at.isoformat() + 'Z',
            'source': 'coingecko'
        }
        
        redis_client.set_rate_lock(bill_id, rate_data)
        
        # Validate
        validation = redis_client.validate_rate_lock(bill_id)
        
        assert validation['valid'] is True, "Rate lock should be valid"
        assert validation['reason'] is None, "No error reason for valid lock"
        assert validation['rate_lock'] is not None, "Rate lock data should be returned"
        assert validation['ttl_seconds'] > 0, "TTL should be positive"
        
        print(f"✅ Rate lock validated: {validation['ttl_seconds']}s remaining")
    
    def test_validate_rate_lock_not_found(self):
        """Test validating a non-existent rate lock"""
        bill_id = "test-bill-nonexistent"
        
        # Validate without creating lock
        validation = redis_client.validate_rate_lock(bill_id)
        
        assert validation['valid'] is False, "Validation should fail"
        assert 'not found' in validation['reason'].lower(), "Reason should mention not found"
        assert validation['rate_lock'] is None, "No rate lock data"
        assert validation['ttl_seconds'] == 0, "TTL should be 0"
        
        print(f"✅ Validation failed as expected: {validation['reason']}")
    
    def test_validate_rate_lock_expired(self):
        """Test validating an expired rate lock"""
        bill_id = "test-bill-expired"
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(seconds=1)  # Short expiry
        
        rate_data = {
            'bill_id': bill_id,
            'currency': 'EUR',
            'hbar_price': 0.36,
            'amount_hbar': 251.17,
            'fiat_amount': 85.40,
            'buffer_applied': True,
            'buffer_percentage': 2.0,
            'locked_at': now.isoformat() + 'Z',
            'expires_at': expires_at.isoformat() + 'Z',
            'source': 'coingecko'
        }
        
        # Create with 1-second TTL
        redis_client.client.setex(
            f"rate_lock:{bill_id}",
            timedelta(seconds=1),
            json.dumps(rate_data)
        )
        
        # Wait for expiry
        print("⏳ Waiting 2 seconds for rate lock to expire...")
        time.sleep(2)
        
        # Validate
        validation = redis_client.validate_rate_lock(bill_id)
        
        assert validation['valid'] is False, "Validation should fail for expired lock"
        assert 'expired' in validation['reason'].lower() or 'not found' in validation['reason'].lower()
        
        print(f"✅ Expired lock validation failed as expected: {validation['reason']}")
    
    def test_delete_rate_lock(self):
        """Test deleting a rate lock"""
        bill_id = "test-bill-delete"
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(minutes=5)
        
        rate_data = {
            'bill_id': bill_id,
            'currency': 'EUR',
            'hbar_price': 0.36,
            'amount_hbar': 251.17,
            'fiat_amount': 85.40,
            'buffer_applied': True,
            'buffer_percentage': 2.0,
            'locked_at': now.isoformat() + 'Z',
            'expires_at': expires_at.isoformat() + 'Z',
            'source': 'coingecko'
        }
        
        # Create rate lock
        redis_client.set_rate_lock(bill_id, rate_data)
        
        # Verify it exists
        lock = redis_client.get_rate_lock(bill_id)
        assert lock is not None, "Rate lock should exist"
        
        # Delete it
        result = redis_client.delete_rate_lock(bill_id)
        assert result is True, "Delete should succeed"
        
        # Verify it's gone
        lock = redis_client.get_rate_lock(bill_id)
        assert lock is None, "Rate lock should be deleted"
        
        print("✅ Rate lock deleted successfully")
    
    def test_multiple_rate_locks(self):
        """Test creating multiple rate locks for different bills"""
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(minutes=5)
        
        bills = ['bill-1', 'bill-2', 'bill-3']
        
        for bill_id in bills:
            rate_data = {
                'bill_id': bill_id,
                'currency': 'EUR',
                'hbar_price': 0.36,
                'amount_hbar': 251.17,
                'fiat_amount': 85.40,
                'buffer_applied': True,
                'buffer_percentage': 2.0,
                'locked_at': now.isoformat() + 'Z',
                'expires_at': expires_at.isoformat() + 'Z',
                'source': 'coingecko'
            }
            redis_client.set_rate_lock(bill_id, rate_data)
        
        # Verify all exist
        for bill_id in bills:
            lock = redis_client.get_rate_lock(bill_id)
            assert lock is not None, f"Rate lock for {bill_id} should exist"
            assert lock['bill_id'] == bill_id
        
        print(f"✅ Created {len(bills)} rate locks successfully")
    
    def test_rate_lock_with_different_currencies(self):
        """Test rate locks with different currencies"""
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(minutes=5)
        
        currencies = {
            'EUR': {'price': 0.36, 'amount': 251.17, 'fiat': 85.40},
            'USD': {'price': 0.05, 'amount': 2000.0, 'fiat': 100.0},
            'INR': {'price': 4.5, 'amount': 1000.0, 'fiat': 4500.0},
            'BRL': {'price': 0.25, 'amount': 400.0, 'fiat': 100.0},
            'NGN': {'price': 75.0, 'amount': 100.0, 'fiat': 7500.0}
        }
        
        for currency, data in currencies.items():
            bill_id = f"bill-{currency}"
            rate_data = {
                'bill_id': bill_id,
                'currency': currency,
                'hbar_price': data['price'],
                'amount_hbar': data['amount'],
                'fiat_amount': data['fiat'],
                'buffer_applied': True,
                'buffer_percentage': 2.0,
                'locked_at': now.isoformat() + 'Z',
                'expires_at': expires_at.isoformat() + 'Z',
                'source': 'coingecko'
            }
            redis_client.set_rate_lock(bill_id, rate_data)
            
            # Verify
            lock = redis_client.get_rate_lock(bill_id)
            assert lock is not None
            assert lock['currency'] == currency
            assert lock['hbar_price'] == data['price']
            
            print(f"✅ Rate lock for {currency}: {lock['amount_hbar']} HBAR @ {lock['hbar_price']} {currency}/HBAR")
    
    def test_rate_lock_buffer_applied(self):
        """Test that buffer information is stored correctly"""
        bill_id = "test-bill-buffer"
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(minutes=5)
        
        # Test with buffer applied
        rate_data_with_buffer = {
            'bill_id': bill_id,
            'currency': 'EUR',
            'hbar_price': 0.36,
            'amount_hbar': 251.17,
            'fiat_amount': 85.40,
            'buffer_applied': True,
            'buffer_percentage': 2.0,
            'locked_at': now.isoformat() + 'Z',
            'expires_at': expires_at.isoformat() + 'Z',
            'source': 'coingecko'
        }
        
        redis_client.set_rate_lock(bill_id, rate_data_with_buffer)
        lock = redis_client.get_rate_lock(bill_id)
        
        assert lock['buffer_applied'] is True
        assert lock['buffer_percentage'] == 2.0
        
        print(f"✅ Buffer info stored: {lock['buffer_percentage']}% buffer applied")
        
        # Clean up
        redis_client.delete_rate_lock(bill_id)
        
        # Test without buffer
        rate_data_no_buffer = {
            'bill_id': bill_id,
            'currency': 'EUR',
            'hbar_price': 0.36,
            'amount_hbar': 237.22,  # No buffer
            'fiat_amount': 85.40,
            'buffer_applied': False,
            'buffer_percentage': 0.0,
            'locked_at': now.isoformat() + 'Z',
            'expires_at': expires_at.isoformat() + 'Z',
            'source': 'coingecko'
        }
        
        redis_client.set_rate_lock(bill_id, rate_data_no_buffer)
        lock = redis_client.get_rate_lock(bill_id)
        
        assert lock['buffer_applied'] is False
        assert lock['buffer_percentage'] == 0.0
        
        print(f"✅ No buffer info stored correctly")


def test_rate_lock_integration():
    """
    Integration test: Full payment preparation flow with rate lock
    
    This test simulates the complete flow:
    1. Prepare payment (create rate lock)
    2. User reviews and signs transaction (within 5 minutes)
    3. Confirm payment (validate and use rate lock)
    4. Clean up rate lock
    """
    print("\n" + "="*60)
    print("INTEGRATION TEST: Payment Preparation with Rate Lock")
    print("="*60)
    
    bill_id = "integration-test-bill"
    
    # Step 1: Prepare payment (create rate lock)
    print("\n📝 Step 1: Prepare payment...")
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(minutes=5)
    
    rate_data = {
        'bill_id': bill_id,
        'currency': 'EUR',
        'hbar_price': 0.36,
        'amount_hbar': 251.17,
        'fiat_amount': 85.40,
        'buffer_applied': True,
        'buffer_percentage': 2.0,
        'locked_at': now.isoformat() + 'Z',
        'expires_at': expires_at.isoformat() + 'Z',
        'source': 'coingecko'
    }
    
    result = redis_client.set_rate_lock(bill_id, rate_data)
    assert result is True
    print(f"✅ Rate lock created: {rate_data['amount_hbar']} HBAR @ {rate_data['hbar_price']} EUR/HBAR")
    print(f"   Expires at: {expires_at.strftime('%Y-%m-%d %H:%M:%S UTC')}")
    
    # Step 2: User reviews (simulate delay)
    print("\n⏳ Step 2: User reviews transaction (simulating 2-second delay)...")
    time.sleep(2)
    
    # Step 3: Validate rate lock before confirmation
    print("\n🔍 Step 3: Validate rate lock...")
    validation = redis_client.validate_rate_lock(bill_id)
    assert validation['valid'] is True
    print(f"✅ Rate lock valid: {validation['ttl_seconds']}s remaining")
    print(f"   Rate: {validation['rate_lock']['hbar_price']} EUR/HBAR")
    print(f"   Amount: {validation['rate_lock']['amount_hbar']} HBAR")
    
    # Step 4: Confirm payment (use rate lock)
    print("\n💰 Step 4: Confirm payment...")
    locked_rate = validation['rate_lock']
    print(f"   Using locked rate: {locked_rate['hbar_price']} EUR/HBAR")
    print(f"   Paying: {locked_rate['amount_hbar']} HBAR for €{locked_rate['fiat_amount']}")
    
    # Step 5: Clean up rate lock after successful payment
    print("\n🧹 Step 5: Clean up rate lock...")
    result = redis_client.delete_rate_lock(bill_id)
    assert result is True
    print("✅ Rate lock deleted after successful payment")
    
    # Verify cleanup
    lock = redis_client.get_rate_lock(bill_id)
    assert lock is None
    print("✅ Cleanup verified")
    
    print("\n" + "="*60)
    print("✅ INTEGRATION TEST PASSED")
    print("="*60)


if __name__ == "__main__":
    # Run tests
    print("Running rate lock tests...")
    pytest.main([__file__, "-v", "-s"])
