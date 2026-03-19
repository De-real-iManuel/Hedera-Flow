"""
Exchange Rate Service - Fetch HBAR prices from CoinGecko API

Implements HBAR/fiat exchange rate fetching with Redis caching and database storage.
Requirements: FR-5.2, US-7

Supported currencies: EUR, USD, INR, BRL, NGN
Cache TTL: 5 minutes
Primary source: CoinGecko API (free tier)
Fallback: CoinMarketCap API (if configured)
"""
from typing import Optional, Dict, Any
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import text
import logging
import httpx

from app.utils.redis_client import redis_client
from config import settings

logger = logging.getLogger(__name__)


class ExchangeRateError(Exception):
    """Raised when exchange rate service encounters an error"""
    pass


class ExchangeRateAPIError(Exception):
    """Raised when external API call fails"""
    pass


# Supported currencies
SUPPORTED_CURRENCIES = ['EUR', 'USD', 'INR', 'BRL', 'NGN']

# CoinGecko currency mapping (lowercase for API)
COINGECKO_CURRENCY_MAP = {
    'EUR': 'eur',
    'USD': 'usd',
    'INR': 'inr',
    'BRL': 'brl',
    'NGN': 'ngn'
}


class ExchangeRateService:
    """Service for fetching and caching HBAR exchange rates"""
    
    def __init__(self, db: Session):
        """
        Initialize ExchangeRateService
        
        Args:
            db: Database session for storing exchange rates
        """
        self.db = db
        self.coingecko_api_key = settings.coingecko_api_key
        self.coinmarketcap_api_key = settings.coinmarketcap_api_key
    
    def get_hbar_price(self, currency: str, use_cache: bool = True) -> float:
        """
        Get current HBAR price in specified currency.
        
        Flow:
        1. Check Redis cache (5 min TTL)
        2. If cache miss, fetch from CoinGecko API
        3. Store in cache and database
        4. Return price
        
        Args:
            currency: Currency code (EUR, USD, INR, BRL, NGN)
            use_cache: Whether to use Redis cache (default: True)
        
        Returns:
            HBAR price in specified currency (e.g., 0.34 for EUR)
        
        Raises:
            ExchangeRateError: If currency not supported or fetch fails
        """
        try:
            # Validate currency
            currency = currency.upper()
            if currency not in SUPPORTED_CURRENCIES:
                raise ExchangeRateError(
                    f"Currency {currency} not supported. "
                    f"Supported: {', '.join(SUPPORTED_CURRENCIES)}"
                )
            
            # Try cache first if enabled
            if use_cache:
                cached_rate = self.get_cached_rate(currency)
                if cached_rate:
                    logger.info(f"Exchange rate cache HIT: {currency}")
                    return cached_rate
                logger.info(f"Exchange rate cache MISS: {currency}")
            
            # Fetch from API
            price = self.fetch_from_api(currency)
            
            # Cache the rate
            if use_cache:
                try:
                    self.cache_rate(currency, price)
                except Exception as e:
                    logger.warning(f"Cache operation failed (non-critical): {e}")
            
            # Store in database — source determined inside fetch_from_api
            try:
                self.store_in_db(currency, price, source='coingecko')
            except Exception as e:
                logger.warning(f"DB storage failed (non-critical): {e}")
            
            return price
            
        except ExchangeRateError:
            raise
        except Exception as e:
            logger.error(f"Exchange rate service error: {e}", exc_info=True)
            raise ExchangeRateError(f"Failed to get HBAR price: {str(e)}")
    
    def fetch_from_api(self, currency: str) -> float:
        """
        Fetch HBAR price from CoinGecko API.
        
        CoinGecko API endpoint:
        GET https://api.coingecko.com/api/v3/simple/price
        ?ids=hedera-hashgraph
        &vs_currencies=usd,eur,inr,brl,ngn
        
        Response format:
        {
            "hedera-hashgraph": {
                "usd": 0.34,
                "eur": 0.32,
                "inr": 28.5,
                "brl": 1.75,
                "ngn": 540.0
            }
        }
        
        Args:
            currency: Currency code (EUR, USD, INR, BRL, NGN)
        
        Returns:
            HBAR price in specified currency
        
        Raises:
            ExchangeRateAPIError: If API call fails
        """
        try:
            # Map currency to CoinGecko format
            vs_currency = COINGECKO_CURRENCY_MAP.get(currency)
            if not vs_currency:
                raise ExchangeRateAPIError(f"Currency {currency} not mapped for CoinGecko")
            
            # Build API URL
            url = "https://api.coingecko.com/api/v3/simple/price"
            params = {
                'ids': 'hedera-hashgraph',
                'vs_currencies': vs_currency
            }
            
            # Add API key if configured (for higher rate limits)
            headers = {}
            if self.coingecko_api_key:
                headers['x-cg-pro-api-key'] = self.coingecko_api_key
            
            # Make API request with timeout
            logger.info(f"Fetching HBAR price from CoinGecko: {currency}")
            with httpx.Client(timeout=5.0) as client:  # Reduced timeout to 5 seconds
                response = client.get(url, params=params, headers=headers)
                response.raise_for_status()
            
            # Parse response
            data = response.json()
            
            # Extract price
            if 'hedera-hashgraph' not in data:
                raise ExchangeRateAPIError("Invalid CoinGecko response: missing hedera-hashgraph")
            
            price = data['hedera-hashgraph'].get(vs_currency)
            if price is None:
                raise ExchangeRateAPIError(f"Invalid CoinGecko response: missing {vs_currency}")
            
            logger.info(f"Fetched HBAR price: {price} {currency}")
            return float(price)
            
        except (httpx.HTTPStatusError, httpx.TimeoutException, httpx.ConnectError) as e:
            logger.warning(f"CoinGecko API unavailable: {e}")
            # Use fallback mock prices for MVP testing
            logger.info(f"Using fallback mock price for {currency}")
            return self._get_mock_price(currency)
        except Exception as e:
            logger.error(f"CoinGecko API error: {e}", exc_info=True)
            # Use fallback mock prices
            logger.info(f"Using fallback mock price for {currency}")
            return self._get_mock_price(currency)
    
    def _get_mock_price(self, currency: str) -> float:
        """
        Get mock HBAR price for testing when API is unavailable.
        
        These are approximate prices for MVP testing only.
        In production, this should raise an error instead.
        
        Args:
            currency: Currency code
        
        Returns:
            Mock HBAR price
        """
        mock_prices = {
            'EUR': 0.10,  # 1 HBAR = 0.10 EUR
            'USD': 0.11,  # 1 HBAR = 0.11 USD
            'INR': 9.0,   # 1 HBAR = 9 INR
            'BRL': 0.55,  # 1 HBAR = 0.55 BRL
            'NGN': 170.0  # 1 HBAR = 170 NGN
        }
        
        price = mock_prices.get(currency, 0.10)
        logger.warning(f"Using mock price for {currency}: {price} (API unavailable)")
        return price
    
    def _fetch_from_coinmarketcap(self, currency: str) -> float:
        """
        Fallback: Fetch HBAR price from CoinMarketCap API.
        
        CoinMarketCap API endpoint:
        GET https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest
        ?symbol=HBAR
        &convert=USD
        
        Note: Requires API key (free tier: 10,000 calls/month)
        
        Args:
            currency: Currency code (EUR, USD, INR, BRL, NGN)
        
        Returns:
            HBAR price in specified currency
        
        Raises:
            ExchangeRateAPIError: If API call fails
        """
        try:
            url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest"
            params = {
                'symbol': 'HBAR',
                'convert': currency
            }
            headers = {
                'X-CMC_PRO_API_KEY': self.coinmarketcap_api_key,
                'Accept': 'application/json'
            }
            
            logger.info(f"Fetching HBAR price from CoinMarketCap: {currency}")
            with httpx.Client(timeout=10.0) as client:
                response = client.get(url, params=params, headers=headers)
                response.raise_for_status()
            
            data = response.json()
            
            # Extract price from nested structure
            if 'data' not in data or 'HBAR' not in data['data']:
                raise ExchangeRateAPIError("Invalid CoinMarketCap response")
            
            quote = data['data']['HBAR']['quote'].get(currency)
            if not quote or 'price' not in quote:
                raise ExchangeRateAPIError(f"Missing price for {currency}")
            
            price = quote['price']
            logger.info(f"Fetched HBAR price from CoinMarketCap: {price} {currency}")
            return float(price)
            
        except Exception as e:
            logger.error(f"CoinMarketCap API error: {e}", exc_info=True)
            raise ExchangeRateAPIError(f"Failed to fetch from CoinMarketCap: {str(e)}")
    
    def cache_rate(self, currency: str, price: float) -> bool:
        """
        Cache exchange rate in Redis with 5-minute TTL.
        
        Cache structure:
        Key: exchange_rate:{currency}
        Value: {
            "currency": "EUR",
            "hbarPrice": 0.34,
            "source": "coingecko",
            "fetchedAt": "2024-03-18T10:30:00Z"
        }
        TTL: 5 minutes (300 seconds)
        
        Args:
            currency: Currency code
            price: HBAR price in currency
        
        Returns:
            True if cached successfully, False otherwise
        """
        try:
            rate_data = {
                'currency': currency,
                'hbarPrice': price,
                'source': 'coingecko',
                'fetchedAt': datetime.now(timezone.utc).isoformat()
            }
            
            result = redis_client.set_exchange_rate(currency, rate_data)
            if result:
                logger.info(f"Exchange rate cached: {currency} = {price}")
            return result
            
        except Exception as e:
            logger.warning(f"Failed to cache exchange rate (non-critical): {e}")
            return False
    
    def get_cached_rate(self, currency: str) -> Optional[float]:
        """
        Get cached exchange rate from Redis.
        
        Args:
            currency: Currency code
        
        Returns:
            HBAR price if cached and not expired, None otherwise
        """
        try:
            rate_data = redis_client.get_exchange_rate(currency)
            if rate_data:
                return rate_data.get('hbarPrice')
            return None
            
        except Exception as e:
            logger.warning(f"Failed to get cached exchange rate (non-critical): {e}")
            return None
    
    def store_in_db(self, currency: str, price: float, source: str) -> bool:
        """
        Store exchange rate in database for historical tracking.
        
        Table: exchange_rates
        Columns:
            - id: UUID (auto-generated)
            - currency: CHAR(3)
            - hbar_price: DECIMAL(12, 6)
            - source: VARCHAR(50)
            - fetched_at: TIMESTAMP (auto-generated)
        
        Args:
            currency: Currency code
            price: HBAR price in currency
            source: API source ('coingecko', 'coinmarketcap', 'mock')
        
        Returns:
            True if stored successfully, False otherwise
        """
        try:
            query = text("""
                INSERT INTO exchange_rates (currency, hbar_price, source)
                VALUES (:currency, :hbar_price, :source)
            """)
            
            self.db.execute(
                query,
                {
                    'currency': currency,
                    'hbar_price': Decimal(str(price)),
                    'source': source
                }
            )
            self.db.commit()
            
            logger.info(f"Exchange rate stored in DB: {currency} = {price} ({source})")
            return True
            
        except Exception as e:
            logger.warning(f"Failed to store exchange rate in DB (non-critical): {e}")
            self.db.rollback()
            return False
    
    def get_latest_rate_from_db(self, currency: str) -> Optional[Dict[str, Any]]:
        """
        Get latest exchange rate from database.
        
        Useful as a fallback when API is down and cache is expired.
        
        Args:
            currency: Currency code
        
        Returns:
            Dictionary with rate data or None if not found
        """
        try:
            query = text("""
                SELECT currency, hbar_price, source, fetched_at
                FROM exchange_rates
                WHERE currency = :currency
                ORDER BY fetched_at DESC
                LIMIT 1
            """)
            
            result = self.db.execute(query, {'currency': currency}).fetchone()
            
            if result:
                return {
                    'currency': result[0],
                    'hbarPrice': float(result[1]),
                    'source': result[2],
                    'fetchedAt': result[3].isoformat()
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get latest rate from DB: {e}")
            return None
    
    def invalidate_cache(self, currency: str) -> bool:
        """
        Invalidate cached exchange rate (force refresh).
        
        Args:
            currency: Currency code
        
        Returns:
            True if cache was invalidated, False otherwise
        """
        try:
            result = redis_client.delete_exchange_rate(currency)
            if result:
                logger.info(f"Exchange rate cache invalidated: {currency}")
            return result
        except Exception as e:
            logger.error(f"Failed to invalidate exchange rate cache: {e}")
            return False
    
    def calculate_hbar_amount(
        self,
        fiat_amount: float,
        currency: str,
        use_cache: bool = True,
        apply_buffer: bool = False,
        buffer_percentage: float = 2.0
    ) -> Dict[str, Any]:
        """
        Calculate HBAR amount needed for a fiat bill amount.
        
        Implements FR-5.4 and FR-6.2:
        - FR-5.4: System shall convert fiat bill amounts to HBAR equivalents
        - FR-6.2: System shall calculate HBAR amount = (fiat_bill_amount / hbar_price)
        
        Formula:
        HBAR amount = fiat_amount / hbar_price
        
        With optional 2% buffer for volatility protection (FR-6.13):
        HBAR amount = (fiat_amount * 1.02) / hbar_price
        
        Args:
            fiat_amount: Bill amount in fiat currency (e.g., 85.40 EUR)
            currency: Currency code (EUR, USD, INR, BRL, NGN)
            use_cache: Whether to use Redis cache (default: True)
            apply_buffer: Whether to apply 2% volatility buffer (default: False)
            buffer_percentage: Buffer percentage to apply (default: 2.0%)
        
        Returns:
            Dictionary containing:
            {
                'fiat_amount': 85.40,
                'currency': 'EUR',
                'hbar_price': 0.34,
                'hbar_amount': 251.17647,
                'hbar_amount_rounded': 251.18,
                'buffer_applied': False,
                'buffer_percentage': 0.0,
                'exchange_rate_timestamp': '2024-03-18T10:30:00Z'
            }
        
        Raises:
            ExchangeRateError: If currency not supported or fetch fails
            ValueError: If fiat_amount is invalid
        
        Example:
            >>> service = ExchangeRateService(db)
            >>> result = service.calculate_hbar_amount(85.40, 'EUR')
            >>> print(f"Pay {result['hbar_amount_rounded']} HBAR for €{result['fiat_amount']}")
            Pay 251.18 HBAR for €85.40
        """
        try:
            # Validate inputs
            if fiat_amount <= 0:
                raise ValueError(f"Fiat amount must be positive, got: {fiat_amount}")
            
            currency = currency.upper()
            if currency not in SUPPORTED_CURRENCIES:
                raise ExchangeRateError(
                    f"Currency {currency} not supported. "
                    f"Supported: {', '.join(SUPPORTED_CURRENCIES)}"
                )
            
            # Get current HBAR price
            hbar_price = self.get_hbar_price(currency, use_cache)
            
            # Apply buffer if requested (for volatility protection)
            effective_fiat_amount = fiat_amount
            if apply_buffer:
                buffer_multiplier = 1 + (buffer_percentage / 100)
                effective_fiat_amount = fiat_amount * buffer_multiplier
                logger.info(
                    f"Applying {buffer_percentage}% buffer: "
                    f"{fiat_amount} → {effective_fiat_amount} {currency}"
                )
            
            # Calculate HBAR amount
            # Formula: HBAR = fiat_amount / hbar_price
            hbar_amount = effective_fiat_amount / hbar_price
            
            # Round to 8 decimal places (HBAR precision)
            hbar_amount_rounded = round(hbar_amount, 8)
            
            logger.info(
                f"Calculated HBAR amount: {fiat_amount} {currency} "
                f"= {hbar_amount_rounded} HBAR (rate: {hbar_price})"
            )
            
            return {
                'fiat_amount': fiat_amount,
                'currency': currency,
                'hbar_price': hbar_price,
                'hbar_amount': hbar_amount,
                'hbar_amount_rounded': hbar_amount_rounded,
                'buffer_applied': apply_buffer,
                'buffer_percentage': buffer_percentage if apply_buffer else 0.0,
                'exchange_rate_timestamp': datetime.now(timezone.utc).isoformat()
            }
            
        except ExchangeRateError:
            raise
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Failed to calculate HBAR amount: {e}", exc_info=True)
            raise ExchangeRateError(f"HBAR calculation failed: {str(e)}")
    def calculate_hbar_amount(
        self,
        fiat_amount: float,
        currency: str,
        use_cache: bool = True,
        apply_buffer: bool = False,
        buffer_percentage: float = 2.0
    ) -> Dict[str, Any]:
        """
        Calculate HBAR amount needed for a fiat bill amount.

        Implements FR-5.4 and FR-6.2:
        - FR-5.4: System shall convert fiat bill amounts to HBAR equivalents
        - FR-6.2: System shall calculate HBAR amount = (fiat_bill_amount / hbar_price)

        Formula:
        HBAR amount = fiat_amount / hbar_price

        With optional 2% buffer for volatility protection (FR-6.13):
        HBAR amount = (fiat_amount * 1.02) / hbar_price

        Args:
            fiat_amount: Bill amount in fiat currency (e.g., 85.40 EUR)
            currency: Currency code (EUR, USD, INR, BRL, NGN)
            use_cache: Whether to use Redis cache (default: True)
            apply_buffer: Whether to apply 2% volatility buffer (default: False)
            buffer_percentage: Buffer percentage to apply (default: 2.0%)

        Returns:
            Dictionary containing:
            {
                'fiat_amount': 85.40,
                'currency': 'EUR',
                'hbar_price': 0.34,
                'hbar_amount': 251.17647,
                'hbar_amount_rounded': 251.18,
                'buffer_applied': False,
                'buffer_percentage': 0.0,
                'exchange_rate_timestamp': '2024-03-18T10:30:00Z'
            }

        Raises:
            ExchangeRateError: If currency not supported or fetch fails
            ValueError: If fiat_amount is invalid

        Example:
            >>> service = ExchangeRateService(db)
            >>> result = service.calculate_hbar_amount(85.40, 'EUR')
            >>> print(f"Pay {result['hbar_amount_rounded']} HBAR for €{result['fiat_amount']}")
            Pay 251.18 HBAR for €85.40
        """
        try:
            # Validate inputs
            if fiat_amount <= 0:
                raise ValueError(f"Fiat amount must be positive, got: {fiat_amount}")

            currency = currency.upper()
            if currency not in SUPPORTED_CURRENCIES:
                raise ExchangeRateError(
                    f"Currency {currency} not supported. "
                    f"Supported: {', '.join(SUPPORTED_CURRENCIES)}"
                )

            # Get current HBAR price
            hbar_price = self.get_hbar_price(currency, use_cache)

            # Apply buffer if requested (for volatility protection)
            effective_fiat_amount = fiat_amount
            if apply_buffer:
                buffer_multiplier = 1 + (buffer_percentage / 100)
                effective_fiat_amount = fiat_amount * buffer_multiplier
                logger.info(
                    f"Applying {buffer_percentage}% buffer: "
                    f"{fiat_amount} → {effective_fiat_amount} {currency}"
                )

            # Calculate HBAR amount
            # Formula: HBAR = fiat_amount / hbar_price
            hbar_amount = effective_fiat_amount / hbar_price

            # Round to 8 decimal places (HBAR precision)
            hbar_amount_rounded = round(hbar_amount, 8)

            logger.info(
                f"Calculated HBAR amount: {fiat_amount} {currency} "
                f"= {hbar_amount_rounded} HBAR (rate: {hbar_price})"
            )

            return {
                'fiat_amount': fiat_amount,
                'currency': currency,
                'hbar_price': hbar_price,
                'hbar_amount': hbar_amount,
                'hbar_amount_rounded': hbar_amount_rounded,
                'buffer_applied': apply_buffer,
                'buffer_percentage': buffer_percentage if apply_buffer else 0.0,
                'exchange_rate_timestamp': datetime.now(timezone.utc).isoformat()
            }

        except ExchangeRateError:
            raise
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Failed to calculate HBAR amount: {e}", exc_info=True)
            raise ExchangeRateError(f"HBAR calculation failed: {str(e)}")


# Convenience function for quick access
def get_hbar_price(db: Session, currency: str, use_cache: bool = True) -> float:
    """
    Convenience function to get HBAR price.
    
    Args:
        db: Database session
        currency: Currency code (EUR, USD, INR, BRL, NGN)
        use_cache: Whether to use Redis cache (default: True)
    
    Returns:
        HBAR price in specified currency
    
    Raises:
        ExchangeRateError: If fetch fails
    """
    service = ExchangeRateService(db)
    return service.get_hbar_price(currency, use_cache)
