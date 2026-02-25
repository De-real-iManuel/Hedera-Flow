"""
Tests for Redis Client Cache Structure
"""
import pytest
from datetime import datetime
from app.utils.redis_client import RedisClient


@pytest.fixture
def redis_client():
    """Create Redis client instance for testing"""
    client = RedisClient()
    yield client
    # Cleanup after tests (only in test environment)
    # client.flush_all()


class TestSessionCache:
    """Test session cache operations"""
    
    def test_set_and_get_session(self, redis_client):
        """Test setting and retrieving session data"""
        user_id = "test-user-123"
        session_data = {
            "userId": user_id,
            "email": "test@example.com",
            "countryCode": "ES",
            "hederaAccountId": "0.0.12345",
            "lastActivity": datetime.utcnow().isoformat()
        }
        
        # Set session
        result = redis_client.set_session(user_id, session_data)
        assert result is True
        
        # Get session
        retrieved = redis_client.get_session(user_id)
        assert retrieved is not None
        assert retrieved["userId"] == user_id
        assert retrieved["email"] == "test@example.com"
        assert retrieved["countryCode"] == "ES"
    
    def test_update_session_activity(self, redis_client):
        """Test updating session activity timestamp"""
        user_id = "test-user-456"
        session_data = {
            "userId": user_id,
            "email": "test2@example.com",
            "countryCode": "US",
            "hederaAccountId": "0.0.67890",
            "lastActivity": "2024-01-01T00:00:00"
        }
        
        redis_client.set_session(user_id, session_data)
        
        # Update activity
        result = redis_client.update_session_activity(user_id)
        assert result is True
        
        # Verify timestamp changed
        updated = redis_client.get_session(user_id)
        assert updated["lastActivity"] != "2024-01-01T00:00:00"
    
    def test_delete_session(self, redis_client):
        """Test deleting session data"""
        user_id = "test-user-789"
        session_data = {
            "userId": user_id,
            "email": "test3@example.com",
            "countryCode": "IN",
            "hederaAccountId": "0.0.11111",
            "lastActivity": datetime.utcnow().isoformat()
        }
        
        redis_client.set_session(user_id, session_data)
        
        # Delete session
        result = redis_client.delete_session(user_id)
        assert result is True
        
        # Verify deleted
        retrieved = redis_client.get_session(user_id)
        assert retrieved is None


class TestExchangeRateCache:
    """Test exchange rate cache operations"""
    
    def test_set_and_get_exchange_rate(self, redis_client):
        """Test setting and retrieving exchange rate data"""
        currency = "EUR"
        rate_data = {
            "currency": currency,
            "hbarPrice": 0.34,
            "source": "coingecko",
            "fetchedAt": datetime.utcnow().isoformat()
        }
        
        # Set rate
        result = redis_client.set_exchange_rate(currency, rate_data)
        assert result is True
        
        # Get rate
        retrieved = redis_client.get_exchange_rate(currency)
        assert retrieved is not None
        assert retrieved["currency"] == currency
        assert retrieved["hbarPrice"] == 0.34
        assert retrieved["source"] == "coingecko"
    
    def test_exchange_rate_case_insensitive(self, redis_client):
        """Test that currency codes are case-insensitive"""
        rate_data = {
            "currency": "USD",
            "hbarPrice": 0.35,
            "source": "coinmarketcap",
            "fetchedAt": datetime.utcnow().isoformat()
        }
        
        # Set with lowercase
        redis_client.set_exchange_rate("usd", rate_data)
        
        # Get with uppercase
        retrieved = redis_client.get_exchange_rate("USD")
        assert retrieved is not None
        assert retrieved["hbarPrice"] == 0.35
    
    def test_delete_exchange_rate(self, redis_client):
        """Test deleting exchange rate cache"""
        currency = "BRL"
        rate_data = {
            "currency": currency,
            "hbarPrice": 1.75,
            "source": "coingecko",
            "fetchedAt": datetime.utcnow().isoformat()
        }
        
        redis_client.set_exchange_rate(currency, rate_data)
        
        # Delete rate
        result = redis_client.delete_exchange_rate(currency)
        assert result is True
        
        # Verify deleted
        retrieved = redis_client.get_exchange_rate(currency)
        assert retrieved is None


class TestTariffCache:
    """Test tariff cache operations"""
    
    def test_set_and_get_tariff(self, redis_client):
        """Test setting and retrieving tariff data"""
        country_code = "ES"
        utility_provider = "Iberdrola"
        tariff_data = {
            "tariffId": "tariff-123",
            "rateStructure": {
                "type": "time_of_use",
                "periods": [
                    {"name": "peak", "price": 0.40},
                    {"name": "off_peak", "price": 0.15}
                ]
            },
            "taxesAndFees": {
                "vat": 0.21,
                "distribution_charge": 0.045
            },
            "validFrom": "2024-01-01"
        }
        
        # Set tariff
        result = redis_client.set_tariff(country_code, utility_provider, tariff_data)
        assert result is True
        
        # Get tariff
        retrieved = redis_client.get_tariff(country_code, utility_provider)
        assert retrieved is not None
        assert retrieved["tariffId"] == "tariff-123"
        assert retrieved["rateStructure"]["type"] == "time_of_use"
        assert retrieved["taxesAndFees"]["vat"] == 0.21
    
    def test_tariff_case_insensitive(self, redis_client):
        """Test that country codes are case-insensitive"""
        tariff_data = {
            "tariffId": "tariff-456",
            "rateStructure": {"type": "flat", "price": 0.30},
            "taxesAndFees": {"vat": 0.18},
            "validFrom": "2024-01-01"
        }
        
        # Set with lowercase
        redis_client.set_tariff("ng", "IKEDP", tariff_data)
        
        # Get with uppercase
        retrieved = redis_client.get_tariff("NG", "IKEDP")
        assert retrieved is not None
        assert retrieved["tariffId"] == "tariff-456"
    
    def test_delete_tariff(self, redis_client):
        """Test deleting tariff cache"""
        country_code = "US"
        utility_provider = "PG&E"
        tariff_data = {
            "tariffId": "tariff-789",
            "rateStructure": {"type": "tiered"},
            "taxesAndFees": {"sales_tax": 0.0725},
            "validFrom": "2024-01-01"
        }
        
        redis_client.set_tariff(country_code, utility_provider, tariff_data)
        
        # Delete tariff
        result = redis_client.delete_tariff(country_code, utility_provider)
        assert result is True
        
        # Verify deleted
        retrieved = redis_client.get_tariff(country_code, utility_provider)
        assert retrieved is None


class TestRateLimiting:
    """Test rate limiting operations"""
    
    def test_increment_rate_limit(self, redis_client):
        """Test incrementing rate limit counter"""
        ip_address = "192.168.1.100"
        
        # First request
        count = redis_client.increment_rate_limit(ip_address)
        assert count == 1
        
        # Second request
        count = redis_client.increment_rate_limit(ip_address)
        assert count == 2
        
        # Third request
        count = redis_client.increment_rate_limit(ip_address)
        assert count == 3
    
    def test_get_rate_limit(self, redis_client):
        """Test getting current rate limit count"""
        ip_address = "192.168.1.101"
        
        # No requests yet
        count = redis_client.get_rate_limit(ip_address)
        assert count == 0
        
        # Make some requests
        redis_client.increment_rate_limit(ip_address)
        redis_client.increment_rate_limit(ip_address)
        
        # Check count
        count = redis_client.get_rate_limit(ip_address)
        assert count == 2
    
    def test_reset_rate_limit(self, redis_client):
        """Test resetting rate limit counter"""
        ip_address = "192.168.1.102"
        
        # Make some requests
        redis_client.increment_rate_limit(ip_address)
        redis_client.increment_rate_limit(ip_address)
        
        # Reset
        result = redis_client.reset_rate_limit(ip_address)
        assert result is True
        
        # Verify reset
        count = redis_client.get_rate_limit(ip_address)
        assert count == 0


class TestUtilityMethods:
    """Test utility methods"""
    
    def test_ping(self, redis_client):
        """Test Redis connection"""
        result = redis_client.ping()
        assert result is True
    
    def test_get_keys_by_pattern(self, redis_client):
        """Test getting keys by pattern"""
        # Set some test data
        redis_client.set_session("user-1", {"userId": "user-1"})
        redis_client.set_session("user-2", {"userId": "user-2"})
        
        # Get all session keys
        keys = redis_client.get_keys_by_pattern("session:*")
        assert len(keys) >= 2
        assert any("user-1" in key for key in keys)
        assert any("user-2" in key for key in keys)
    
    def test_get_ttl(self, redis_client):
        """Test getting TTL for a key"""
        user_id = "test-ttl-user"
        session_data = {
            "userId": user_id,
            "email": "ttl@example.com",
            "countryCode": "ES",
            "hederaAccountId": "0.0.99999",
            "lastActivity": datetime.utcnow().isoformat()
        }
        
        redis_client.set_session(user_id, session_data)
        
        # Get TTL (should be around 30 days = 2592000 seconds)
        ttl = redis_client.get_ttl(f"session:{user_id}")
        assert ttl > 0
        assert ttl <= 2592000  # 30 days in seconds
