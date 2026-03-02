# ExchangeRateService Quick Reference

## Overview

The `ExchangeRateService` fetches real-time HBAR prices from CoinGecko API with Redis caching and database storage.

**Requirements**: FR-5.2, US-7  
**Supported Currencies**: EUR, USD, INR, BRL, NGN  
**Cache TTL**: 5 minutes  
**Primary Source**: CoinGecko API (free tier)  
**Fallback**: CoinMarketCap API (if configured)

---

## Quick Start

### Basic Usage

```python
from sqlalchemy.orm import Session
from app.services.exchange_rate_service import ExchangeRateService

# In your endpoint
def get_bill_payment_info(db: Session, bill_id: str):
    service = ExchangeRateService(db)
    
    # Get HBAR price in EUR
    hbar_price_eur = service.get_hbar_price('EUR')
    
    # Calculate HBAR amount needed
    bill_amount_eur = 85.40
    hbar_amount = bill_amount_eur / hbar_price_eur
    
    return {
        'bill_amount_fiat': bill_amount_eur,
        'currency': 'EUR',
        'hbar_amount': hbar_amount,
        'exchange_rate': hbar_price_eur
    }
```

### Convenience Function

```python
from app.services.exchange_rate_service import get_hbar_price

# Quick access without creating service instance
price = get_hbar_price(db, 'USD')
```

---

## API Reference

### ExchangeRateService Class

#### `__init__(db: Session)`
Initialize service with database session.

#### `get_hbar_price(currency: str, use_cache: bool = True) -> float`
Get current HBAR price in specified currency.

**Parameters**:
- `currency`: Currency code (EUR, USD, INR, BRL, NGN)
- `use_cache`: Whether to use Redis cache (default: True)

**Returns**: HBAR price as float (e.g., 0.34 for EUR)

**Raises**: `ExchangeRateError` if currency not supported or fetch fails

**Example**:
```python
service = ExchangeRateService(db)
price = service.get_hbar_price('EUR')  # 0.34
```

#### `fetch_from_api(currency: str) -> float`
Fetch HBAR price directly from CoinGecko API (bypasses cache).

**Example**:
```python
price = service.fetch_from_api('USD')
```

#### `cache_rate(currency: str, price: float) -> bool`
Cache exchange rate in Redis with 5-minute TTL.

**Example**:
```python
service.cache_rate('EUR', 0.34)
```

#### `get_cached_rate(currency: str) -> Optional[float]`
Get cached exchange rate from Redis.

**Returns**: Price if cached, None if not found or expired

**Example**:
```python
cached_price = service.get_cached_rate('EUR')
if cached_price:
    print(f"Using cached price: {cached_price}")
```

#### `store_in_db(currency: str, price: float, source: str) -> bool`
Store exchange rate in database for historical tracking.

**Parameters**:
- `currency`: Currency code
- `price`: HBAR price
- `source`: API source ('coingecko', 'coinmarketcap')

**Example**:
```python
service.store_in_db('EUR', 0.34, 'coingecko')
```

#### `get_latest_rate_from_db(currency: str) -> Optional[Dict[str, Any]]`
Get latest exchange rate from database (fallback when API is down).

**Returns**: Dictionary with rate data or None

**Example**:
```python
latest = service.get_latest_rate_from_db('EUR')
# {'currency': 'EUR', 'hbarPrice': 0.34, 'source': 'coingecko', 'fetchedAt': '2024-03-18T10:30:00Z'}
```

#### `invalidate_cache(currency: str) -> bool`
Invalidate cached exchange rate (force refresh).

**Example**:
```python
service.invalidate_cache('EUR')
```

---

## Configuration

### Environment Variables

Add to `.env`:

```bash
# CoinGecko API (optional - for higher rate limits)
COINGECKO_API_KEY=your_api_key_here

# CoinMarketCap API (optional - fallback)
COINMARKETCAP_API_KEY=your_api_key_here
```

**Note**: Both APIs work without keys (free tier), but keys provide higher rate limits.

### CoinGecko Free Tier
- **Rate Limit**: 10-50 calls/minute
- **No API Key Required**: Yes
- **Currencies Supported**: All major currencies

### CoinMarketCap Free Tier
- **Rate Limit**: 10,000 calls/month
- **API Key Required**: Yes
- **Currencies Supported**: All major currencies

---

## Cache Structure

### Redis Cache

**Key**: `exchange_rate:{currency}`  
**TTL**: 5 minutes (300 seconds)

**Value**:
```json
{
  "currency": "EUR",
  "hbarPrice": 0.34,
  "source": "coingecko",
  "fetchedAt": "2024-03-18T10:30:00Z"
}
```

### Database Table

**Table**: `exchange_rates`

```sql
CREATE TABLE exchange_rates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    currency CHAR(3) NOT NULL,
    hbar_price DECIMAL(12, 6) NOT NULL,
    source VARCHAR(50) NOT NULL,
    fetched_at TIMESTAMP DEFAULT NOW(),
    INDEX idx_currency_time (currency, fetched_at DESC)
);
```

---

## Usage Examples

### Example 1: Payment Flow

```python
from app.services.exchange_rate_service import ExchangeRateService

def prepare_payment(db: Session, bill_id: str):
    """Prepare payment with HBAR conversion"""
    service = ExchangeRateService(db)
    
    # Get bill details
    bill = get_bill(db, bill_id)
    
    # Get current HBAR price
    hbar_price = service.get_hbar_price(bill.currency)
    
    # Calculate HBAR amount with 2% buffer for volatility
    hbar_amount = (bill.total_fiat / hbar_price) * 1.02
    
    return {
        'bill_id': bill_id,
        'amount_fiat': bill.total_fiat,
        'currency': bill.currency,
        'amount_hbar': round(hbar_amount, 8),
        'exchange_rate': hbar_price,
        'exchange_rate_expiry': datetime.now() + timedelta(minutes=5)
    }
```

### Example 2: Display Bill with HBAR Equivalent

```python
def get_bill_with_hbar(db: Session, bill_id: str):
    """Get bill with HBAR equivalent"""
    service = ExchangeRateService(db)
    
    bill = get_bill(db, bill_id)
    hbar_price = service.get_hbar_price(bill.currency)
    hbar_amount = bill.total_fiat / hbar_price
    
    return {
        'bill_id': bill_id,
        'amount_fiat': f"{bill.total_fiat} {bill.currency}",
        'amount_hbar': f"{hbar_amount:.2f} HBAR",
        'exchange_rate': f"1 HBAR = {hbar_price} {bill.currency}"
    }
```

### Example 3: Batch Fetch All Currencies

```python
def get_all_hbar_prices(db: Session):
    """Fetch HBAR prices for all supported currencies"""
    service = ExchangeRateService(db)
    
    prices = {}
    for currency in ['EUR', 'USD', 'INR', 'BRL', 'NGN']:
        try:
            prices[currency] = service.get_hbar_price(currency)
        except Exception as e:
            print(f"Failed to fetch {currency}: {e}")
            prices[currency] = None
    
    return prices
```

### Example 4: Fallback to Database

```python
def get_hbar_price_with_fallback(db: Session, currency: str):
    """Get HBAR price with database fallback"""
    service = ExchangeRateService(db)
    
    try:
        # Try to fetch from API/cache
        return service.get_hbar_price(currency)
    except Exception as e:
        print(f"API failed: {e}, trying database fallback...")
        
        # Fallback to latest DB rate
        latest = service.get_latest_rate_from_db(currency)
        if latest:
            print(f"Using DB rate from {latest['fetchedAt']}")
            return latest['hbarPrice']
        
        raise Exception(f"No exchange rate available for {currency}")
```

---

## Testing

### Unit Tests

```bash
# Run unit tests
cd backend
python -m pytest tests/test_exchange_rate_service.py -v
```

### Manual Integration Test

```bash
# Test with real API calls
cd backend
python test_exchange_rate_manual.py
```

**Note**: Manual test requires:
- Redis running
- Database connection
- Internet access for API calls

---

## Error Handling

### Common Errors

#### `ExchangeRateError: Currency XXX not supported`
**Cause**: Invalid currency code  
**Solution**: Use one of: EUR, USD, INR, BRL, NGN

#### `ExchangeRateAPIError: CoinGecko API error: 429`
**Cause**: Rate limit exceeded  
**Solution**: 
- Add API key to `.env`
- Increase cache TTL
- Use database fallback

#### `ExchangeRateAPIError: CoinGecko API timeout`
**Cause**: Network issue or API down  
**Solution**: 
- Check internet connection
- Use CoinMarketCap fallback
- Use database fallback

### Graceful Degradation

```python
def get_hbar_price_safe(db: Session, currency: str):
    """Get HBAR price with graceful degradation"""
    service = ExchangeRateService(db)
    
    try:
        # Try cache + API
        return service.get_hbar_price(currency)
    except Exception as e:
        print(f"Primary fetch failed: {e}")
        
        # Try database fallback
        latest = service.get_latest_rate_from_db(currency)
        if latest:
            age_minutes = (datetime.now() - latest['fetchedAt']).total_seconds() / 60
            if age_minutes < 60:  # Use if less than 1 hour old
                return latest['hbarPrice']
        
        # Last resort: use hardcoded fallback
        fallback_rates = {
            'EUR': 0.34,
            'USD': 0.35,
            'INR': 28.5,
            'BRL': 1.75,
            'NGN': 540.0
        }
        return fallback_rates.get(currency, 0.35)
```

---

## Performance

### Caching Strategy

1. **First Request**: Fetch from API (~500ms) + Store in cache + Store in DB
2. **Subsequent Requests**: Fetch from cache (~5ms)
3. **After 5 Minutes**: Cache expires, fetch from API again

### Optimization Tips

1. **Use Cache**: Always use `use_cache=True` (default) in production
2. **Batch Requests**: Fetch all currencies at once if needed
3. **Preload Cache**: Warm up cache on application startup
4. **Monitor Rate Limits**: Track API usage to avoid 429 errors

### Preload Cache Example

```python
def preload_exchange_rates(db: Session):
    """Preload all exchange rates on startup"""
    service = ExchangeRateService(db)
    
    for currency in ['EUR', 'USD', 'INR', 'BRL', 'NGN']:
        try:
            service.get_hbar_price(currency, use_cache=False)
            print(f"✓ Preloaded {currency}")
        except Exception as e:
            print(f"✗ Failed to preload {currency}: {e}")
```

---

## Next Steps

1. **Task 16.2**: Integrate CoinGecko API as primary source ✅ (Already done)
2. **Task 16.3**: Add CoinMarketCap fallback (Optional - already implemented)
3. **Task 17**: Implement payment endpoints using ExchangeRateService
4. **Task 18**: Add exchange rate display to frontend

---

## Support

For issues or questions:
1. Check logs: `backend/backend.log`
2. Test Redis: `python test_exchange_rate_manual.py`
3. Verify API keys in `.env`
4. Check CoinGecko status: https://status.coingecko.com/
