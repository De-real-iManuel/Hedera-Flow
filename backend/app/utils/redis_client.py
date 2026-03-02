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

    
    # ==================== RATE LOCK (Payment Protection) ====================
    
    def set_rate_lock(self, bill_id: str, rate_data: Dict[str, Any]) -> bool:
        """
        Create a 5-minute rate lock for a payment preparation.
        
        This protects users from exchange rate volatility during the payment flow.
        The locked rate is valid for 5 minutes, after which the user must re-prepare.
        
        Key: rate_lock:{bill_id}
        TTL: 5 minutes (300 seconds)
        
        Requirements:
            - FR-6.13: System shall handle exchange rate volatility with 2% buffer
            - FR-17.4: Set 5-minute rate lock to protect against volatility
            - US-7: Show exchange rate, timestamp, and 5-minute expiry
        
        Args:
            bill_id: Bill UUID
            rate_data: {
                bill_id: str,
                currency: str,
                hbar_price: float,
                amount_hbar: float,
                fiat_amount: float,
                buffer_applied: bool,
                buffer_percentage: float,
                locked_at: timestamp (ISO format),
                expires_at: timestamp (ISO format),
                source: str
            }
        
        Returns:
            True if rate lock created successfully, False otherwise
        
        Example:
            >>> redis_client.set_rate_lock('abc-123', {
            ...     'bill_id': 'abc-123',
            ...     'currency': 'EUR',
            ...     'hbar_price': 0.36,
            ...     'amount_hbar': 251.17,
            ...     'fiat_amount': 85.40,
            ...     'buffer_applied': True,
            ...     'buffer_percentage': 2.0,
            ...     'locked_at': '2026-03-02T10:00:00Z',
            ...     'expires_at': '2026-03-02T10:05:00Z',
            ...     'source': 'coingecko'
            ... })
        """
        try:
            key = f"rate_lock:{bill_id}"
            value = json.dumps(rate_data)
            ttl = timedelta(minutes=5)  # 5-minute lock
            result = self.client.setex(key, ttl, value)
            
            if result:
                print(f"✅ Rate lock created for bill {bill_id}: {rate_data['amount_hbar']} HBAR @ {rate_data['hbar_price']} {rate_data['currency']}/HBAR (expires in 5 min)")
            
            return result
        except Exception as e:
            print(f"Error setting rate lock: {e}")
            return False
    
    def get_rate_lock(self, bill_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve rate lock data for a bill.
        
        Args:
            bill_id: Bill UUID
            
        Returns:
            Rate lock data dict or None if not found/expired
            
        Example:
            >>> lock = redis_client.get_rate_lock('abc-123')
            >>> if lock:
            ...     print(f"Locked rate: {lock['hbar_price']} {lock['currency']}/HBAR")
            ...     print(f"Expires at: {lock['expires_at']}")
        """
        try:
            key = f"rate_lock:{bill_id}"
            value = self.client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            print(f"Error getting rate lock: {e}")
            return None
    
    def delete_rate_lock(self, bill_id: str) -> bool:
        """
        Delete rate lock (after payment confirmed or cancelled).
        
        Args:
            bill_id: Bill UUID
            
        Returns:
            True if deleted, False otherwise
        """
        try:
            key = f"rate_lock:{bill_id}"
            result = bool(self.client.delete(key))
            if result:
                print(f"✅ Rate lock deleted for bill {bill_id}")
            return result
        except Exception as e:
            print(f"Error deleting rate lock: {e}")
            return False
    
    def get_rate_lock_ttl(self, bill_id: str) -> int:
        """
        Get remaining time-to-live for a rate lock.
        
        Args:
            bill_id: Bill UUID
            
        Returns:
            TTL in seconds, -1 if no expiry, -2 if key doesn't exist
            
        Example:
            >>> ttl = redis_client.get_rate_lock_ttl('abc-123')
            >>> if ttl > 0:
            ...     print(f"Rate lock expires in {ttl} seconds")
        """
        try:
            key = f"rate_lock:{bill_id}"
            return self.client.ttl(key)
        except Exception as e:
            print(f"Error getting rate lock TTL: {e}")
            return -2
    
    def validate_rate_lock(self, bill_id: str, tolerance_percent: float = 5.0) -> Dict[str, Any]:
        """
        Validate that a rate lock exists and is still valid.
        
        This method checks:
        1. Rate lock exists
        2. Rate lock has not expired
        3. Optionally validates amount is within tolerance
        
        Args:
            bill_id: Bill UUID
            tolerance_percent: Allowed deviation percentage (default: 5%)
            
        Returns:
            Dictionary with validation result:
            {
                'valid': bool,
                'reason': str,  # If invalid
                'rate_lock': dict,  # If valid
                'ttl_seconds': int  # Remaining time
            }
            
        Example:
            >>> result = redis_client.validate_rate_lock('abc-123')
            >>> if result['valid']:
            ...     print(f"Rate lock valid, {result['ttl_seconds']}s remaining")
            ... else:
            ...     print(f"Rate lock invalid: {result['reason']}")
        """
        try:
            # Check if rate lock exists
            rate_lock = self.get_rate_lock(bill_id)
            if not rate_lock:
                return {
                    'valid': False,
                    'reason': 'Rate lock not found or expired. Please re-prepare payment.',
                    'rate_lock': None,
                    'ttl_seconds': 0
                }
            
            # Get TTL
            ttl = self.get_rate_lock_ttl(bill_id)
            if ttl <= 0:
                return {
                    'valid': False,
                    'reason': 'Rate lock has expired. Please re-prepare payment.',
                    'rate_lock': None,
                    'ttl_seconds': 0
                }
            
            # Check expiry timestamp
            expires_at_str = rate_lock.get('expires_at')
            if expires_at_str:
                # Handle both 'Z' suffix and '+00:00' suffix
                # Remove 'Z' if present, fromisoformat will handle '+00:00'
                if expires_at_str.endswith('Z'):
                    expires_at_str = expires_at_str[:-1]
                    if not expires_at_str.endswith('+00:00'):
                        expires_at_str += '+00:00'
                
                expires_at = datetime.fromisoformat(expires_at_str)
                now = datetime.now(timezone.utc)
                
                if now > expires_at:
                    return {
                        'valid': False,
                        'reason': 'Rate lock has expired. Please re-prepare payment.',
                        'rate_lock': None,
                        'ttl_seconds': 0
                    }
            
            # Rate lock is valid
            return {
                'valid': True,
                'reason': None,
                'rate_lock': rate_lock,
                'ttl_seconds': ttl
            }
            
        except Exception as e:
            print(f"Error validating rate lock: {e}")
            return {
                'valid': False,
                'reason': f'Rate lock validation error: {str(e)}',
                'rate_lock': None,
                'ttl_seconds': 0
            }

    
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
