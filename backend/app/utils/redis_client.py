"""
Redis Client and Cache Management
Provides structured caching for sessions, exchange rates, tariffs, and rate limiting
"""
import redis
import json
from typing import Optional, Dict, Any
from datetime import datetime, timedelta, timezone
from config import settings


class RedisClient:
    """Redis client wrapper with structured cache management"""
    
    def __init__(self):
        """Initialize Redis connection"""
        self.client = redis.from_url(
            settings.redis_url,
            decode_responses=True,
            socket_timeout=10,  # Increased from 5 to 10 seconds
            socket_connect_timeout=10,  # Increased from 5 to 10 seconds
            max_connections=10,
            retry_on_timeout=True,  # Retry on timeout
            health_check_interval=30  # Health check every 30 seconds
        )
    
    def ping(self) -> bool:
        """Test Redis connection"""
        try:
            return self.client.ping()
        except Exception:
            return False

    
    # ==================== SESSION CACHE ====================
    
    def set_session(self, user_id: str, session_data: Dict[str, Any]) -> bool:
        """
        Store user session data
        
        Key: session:{user_id}
        TTL: 30 days
        
        Args:
            user_id: User UUID
            session_data: {
                userId: str,
                email: str,
                countryCode: str,
                hederaAccountId: str,
                lastActivity: timestamp
            }
        """
        try:
            key = f"session:{user_id}"
            value = json.dumps(session_data)
            ttl = timedelta(days=30)
            return self.client.setex(key, ttl, value)
        except Exception as e:
            print(f"Error setting session: {e}")
            return False
    
    def get_session(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve user session data
        
        Args:
            user_id: User UUID
            
        Returns:
            Session data dict or None if not found
        """
        try:
            key = f"session:{user_id}"
            value = self.client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            print(f"Error getting session: {e}")
            return None
    
    def delete_session(self, user_id: str) -> bool:
        """
        Delete user session (logout)
        
        Args:
            user_id: User UUID
        """
        try:
            key = f"session:{user_id}"
            return bool(self.client.delete(key))
        except Exception as e:
            print(f"Error deleting session: {e}")
            return False
    
    def update_session_activity(self, user_id: str) -> bool:
        """
        Update last activity timestamp for session
        
        Args:
            user_id: User UUID
        """
        try:
            session = self.get_session(user_id)
            if session:
                session['lastActivity'] = datetime.now(timezone.utc).isoformat()
                return self.set_session(user_id, session)
            return False
        except Exception as e:
            print(f"Error updating session activity: {e}")
            return False

    
    # ==================== EXCHANGE RATE CACHE ====================
    
    def set_exchange_rate(self, currency: str, rate_data: Dict[str, Any]) -> bool:
        """
        Store exchange rate data
        
        Key: exchange_rate:{currency}
        TTL: 5 minutes
        
        Args:
            currency: Currency code (EUR, USD, INR, BRL, NGN)
            rate_data: {
                currency: str,
                hbarPrice: float,
                source: str,
                fetchedAt: timestamp
            }
        """
        try:
            key = f"exchange_rate:{currency.upper()}"
            value = json.dumps(rate_data)
            ttl = timedelta(minutes=5)
            return self.client.setex(key, ttl, value)
        except Exception as e:
            print(f"Error setting exchange rate: {e}")
            return False
    
    def get_exchange_rate(self, currency: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve exchange rate data
        
        Args:
            currency: Currency code (EUR, USD, INR, BRL, NGN)
            
        Returns:
            Exchange rate data dict or None if not found/expired
        """
        try:
            key = f"exchange_rate:{currency.upper()}"
            value = self.client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            print(f"Error getting exchange rate: {e}")
            return None
    
    def delete_exchange_rate(self, currency: str) -> bool:
        """
        Delete exchange rate cache (force refresh)
        
        Args:
            currency: Currency code
        """
        try:
            key = f"exchange_rate:{currency.upper()}"
            return bool(self.client.delete(key))
        except Exception as e:
            print(f"Error deleting exchange rate: {e}")
            return False

    
    # ==================== TARIFF CACHE ====================
    
    def set_tariff(self, country_code: str, utility_provider: str, tariff_data: Dict[str, Any]) -> bool:
        """
        Store tariff data
        
        Key: tariff:{country_code}:{utility_provider}
        TTL: 1 hour
        
        Args:
            country_code: Country code (ES, US, IN, BR, NG)
            utility_provider: Utility provider name
            tariff_data: {
                tariffId: str,
                rateStructure: dict,
                taxesAndFees: dict,
                validFrom: date
            }
        """
        try:
            key = f"tariff:{country_code.upper()}:{utility_provider}"
            value = json.dumps(tariff_data)
            ttl = timedelta(hours=1)
            return self.client.setex(key, ttl, value)
        except Exception as e:
            print(f"Error setting tariff: {e}")
            return False
    
    def get_tariff(self, country_code: str, utility_provider: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve tariff data
        
        Args:
            country_code: Country code (ES, US, IN, BR, NG)
            utility_provider: Utility provider name
            
        Returns:
            Tariff data dict or None if not found/expired
        """
        try:
            key = f"tariff:{country_code.upper()}:{utility_provider}"
            value = self.client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            print(f"Error getting tariff: {e}")
            return None
    
    def delete_tariff(self, country_code: str, utility_provider: str) -> bool:
        """
        Delete tariff cache (force refresh)
        
        Args:
            country_code: Country code
            utility_provider: Utility provider name
        """
        try:
            key = f"tariff:{country_code.upper()}:{utility_provider}"
            return bool(self.client.delete(key))
        except Exception as e:
            print(f"Error deleting tariff: {e}")
            return False

    
    # ==================== RATE LIMITING ====================
    
    def increment_rate_limit(self, ip_address: str) -> int:
        """
        Increment rate limit counter for IP address
        
        Key: rate_limit:{ip_address}
        TTL: 1 minute
        
        Args:
            ip_address: Client IP address
            
        Returns:
            Current request count
        """
        try:
            key = f"rate_limit:{ip_address}"
            count = self.client.incr(key)
            
            # Set TTL on first request
            if count == 1:
                self.client.expire(key, timedelta(minutes=1))
            
            return count
        except Exception as e:
            print(f"Error incrementing rate limit: {e}")
            return 0
    
    def get_rate_limit(self, ip_address: str) -> int:
        """
        Get current rate limit count for IP address
        
        Args:
            ip_address: Client IP address
            
        Returns:
            Current request count
        """
        try:
            key = f"rate_limit:{ip_address}"
            count = self.client.get(key)
            return int(count) if count else 0
        except Exception as e:
            print(f"Error getting rate limit: {e}")
            return 0
    
    def reset_rate_limit(self, ip_address: str) -> bool:
        """
        Reset rate limit for IP address
        
        Args:
            ip_address: Client IP address
        """
        try:
            key = f"rate_limit:{ip_address}"
            return bool(self.client.delete(key))
        except Exception as e:
            print(f"Error resetting rate limit: {e}")
            return False

    
    # ==================== UTILITY METHODS ====================
    
    def flush_all(self) -> bool:
        """
        Flush all cache data (use with caution!)
        Only for development/testing
        """
        try:
            return self.client.flushall()
        except Exception as e:
            print(f"Error flushing cache: {e}")
            return False
    
    def get_keys_by_pattern(self, pattern: str) -> list:
        """
        Get all keys matching pattern
        
        Args:
            pattern: Redis key pattern (e.g., "session:*")
            
        Returns:
            List of matching keys
        """
        try:
            return self.client.keys(pattern)
        except Exception as e:
            print(f"Error getting keys: {e}")
            return []
    
    def get_ttl(self, key: str) -> int:
        """
        Get time-to-live for a key
        
        Args:
            key: Redis key
            
        Returns:
            TTL in seconds, -1 if no expiry, -2 if key doesn't exist
        """
        try:
            return self.client.ttl(key)
        except Exception as e:
            print(f"Error getting TTL: {e}")
            return -2


# Global Redis client instance
redis_client = RedisClient()
