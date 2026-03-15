"""
Rate Limiting Helper for Exchange Rate Service
Prevents CoinGecko 429 errors by adding delays between API calls
"""
import time
from typing import List, Dict
from app.services.exchange_rate_service import ExchangeRateService
from sqlalchemy.orm import Session


class RateLimitedExchangeRateService:
    """Wrapper around ExchangeRateService with built-in rate limiting"""
    
    def __init__(self, db: Session, delay_seconds: float = 2.0):
        """
        Initialize rate-limited service
        
        Args:
            db: Database session
            delay_seconds: Delay between API calls (default: 2 seconds)
        """
        self.service = ExchangeRateService(db)
        self.delay_seconds = delay_seconds
        self.last_api_call = 0
    
    def get_hbar_price(self, currency: str, use_cache: bool = True) -> float:
        """
        Get HBAR price with automatic rate limiting
        
        Args:
            currency: Currency code (EUR, USD, INR, BRL, NGN)
            use_cache: Whether to use cache (default: True)
        
        Returns:
            HBAR price in specified currency
        """
        # If cache is disabled, enforce rate limiting
        if not use_cache:
            current_time = time.time()
            time_since_last_call = current_time - self.last_api_call
            
            if time_since_last_call < self.delay_seconds:
                sleep_time = self.delay_seconds - time_since_last_call
                time.sleep(sleep_time)
            
            self.last_api_call = time.time()
        
        return self.service.get_hbar_price(currency, use_cache)
    
    def get_multiple_prices(
        self, 
        currencies: List[str], 
        use_cache: bool = True
    ) -> Dict[str, float]:
        """
        Get HBAR prices for multiple currencies with rate limiting
        
        Args:
            currencies: List of currency codes
            use_cache: Whether to use cache (default: True)
        
        Returns:
            Dictionary mapping currency to price
        """
        results = {}
        
        for currency in currencies:
            try:
                price = self.get_hbar_price(currency, use_cache)
                results[currency] = price
            except Exception as e:
                print(f"Error fetching {currency}: {e}")
                results[currency] = None
        
        return results


# Usage example:
# from app.core.database import get_db
# from app.utils.rate_limited_exchange_rate import RateLimitedExchangeRateService
#
# db = next(get_db())
# service = RateLimitedExchangeRateService(db, delay_seconds=2.0)
#
# # Fetch multiple currencies safely
# prices = service.get_multiple_prices(['EUR', 'USD', 'INR', 'BRL', 'NGN'])
