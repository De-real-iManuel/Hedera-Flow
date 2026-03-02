# Redis Client Setup - Task 5.5 Complete

## Overview
Redis client has been successfully set up and tested for the Hedera Flow MVP backend. The client provides structured caching for sessions, exchange rates, tariffs, and rate limiting.

## Implementation Details

### Redis Client Location
- **File**: `backend/app/utils/redis_client.py`
- **Class**: `RedisClient`
- **Global Instance**: `redis_client`

### Configuration
- **Connection**: Upstash Redis (cloud-hosted)
- **URL**: Configured in `.env` as `REDIS_URL`
- **Timeout Settings**: 10 seconds (socket and connect)
- **Max Connections**: 10
- **Features**: Auto-retry on timeout, health checks every 30 seconds

### Supported Cache Types

#### 1. Session Cache
- **Key Format**: `session:{user_id}`
- **TTL**: 30 days
- **Data Structure**:
  ```json
  {
    "userId": "string",
    "email": "string",
    "countryCode": "string",
    "hederaAccountId": "string",
    "lastActivity": "ISO timestamp"
  }
  ```
- **Methods**:
  - `set_session(user_id, session_data)` - Store session
  - `get_session(user_id)` - Retrieve session
  - `delete_session(user_id)` - Delete session (logout)
  - `update_session_activity(user_id)` - Update last activity

#### 2. Exchange Rate Cache
- **Key Format**: `exchange_rate:{currency}`
- **TTL**: 5 minutes
- **Data Structure**:
  ```json
  {
    "currency": "EUR|USD|INR|BRL|NGN",
    "hbarPrice": 0.34,
    "source": "coingecko|coinmarketcap",
    "fetchedAt": "ISO timestamp"
  }
  ```
- **Methods**:
  - `set_exchange_rate(currency, rate_data)` - Store rate
  - `get_exchange_rate(currency)` - Retrieve rate
  - `delete_exchange_rate(currency)` - Force refresh

#### 3. Tariff Cache
- **Key Format**: `tariff:{country_code}:{utility_provider}`
- **TTL**: 1 hour
- **Data Structure**:
  ```json
  {
    "tariffId": "string",
    "rateStructure": {},
    "taxesAndFees": {},
    "validFrom": "date"
  }
  ```
- **Methods**:
  - `set_tariff(country_code, utility_provider, tariff_data)` - Store tariff
  - `get_tariff(country_code, utility_provider)` - Retrieve tariff
  - `delete_tariff(country_code, utility_provider)` - Force refresh

#### 4. Rate Limiting
- **Key Format**: `rate_limit:{ip_address}`
- **TTL**: 1 minute
- **Data**: Request count (integer)
- **Methods**:
  - `increment_rate_limit(ip_address)` - Increment counter
  - `get_rate_limit(ip_address)` - Get current count
  - `reset_rate_limit(ip_address)` - Reset counter

### Utility Methods
- `ping()` - Test Redis connection
- `flush_all()` - Clear all cache (dev/test only)
- `get_keys_by_pattern(pattern)` - Find keys by pattern
- `get_ttl(key)` - Get time-to-live for key

## Testing

### Test Script
- **File**: `backend/test_redis_client.py`
- **Coverage**: All cache types and utility methods
- **Results**: ✅ 6/6 tests passed

### Test Results
```
✓ PASS: Connection
✓ PASS: Session Cache
✓ PASS: Exchange Rate Cache
✓ PASS: Tariff Cache
✓ PASS: Rate Limiting
✓ PASS: Utility Methods
```

### Running Tests
```bash
cd backend
python test_redis_client.py
```

## Usage Examples

### Session Management
```python
from app.utils.redis_client import redis_client

# Store session
session_data = {
    "userId": "user-123",
    "email": "user@example.com",
    "countryCode": "ES",
    "hederaAccountId": "0.0.123456",
    "lastActivity": datetime.now(timezone.utc).isoformat()
}
redis_client.set_session("user-123", session_data)

# Retrieve session
session = redis_client.get_session("user-123")

# Update activity
redis_client.update_session_activity("user-123")

# Logout
redis_client.delete_session("user-123")
```

### Exchange Rate Caching
```python
# Store exchange rate
rate_data = {
    "currency": "EUR",
    "hbarPrice": 0.34,
    "source": "coingecko",
    "fetchedAt": datetime.now(timezone.utc).isoformat()
}
redis_client.set_exchange_rate("EUR", rate_data)

# Retrieve (returns None if expired)
rate = redis_client.get_exchange_rate("EUR")
if rate is None:
    # Fetch fresh rate from API
    pass
```

### Tariff Caching
```python
# Store tariff
tariff_data = {
    "tariffId": "tariff-123",
    "rateStructure": {...},
    "taxesAndFees": {...},
    "validFrom": "2024-01-01"
}
redis_client.set_tariff("ES", "Iberdrola", tariff_data)

# Retrieve
tariff = redis_client.get_tariff("ES", "Iberdrola")
```

### Rate Limiting
```python
# Check rate limit
ip = request.client.host
count = redis_client.increment_rate_limit(ip)

if count > 100:  # 100 requests per minute
    raise HTTPException(status_code=429, detail="Rate limit exceeded")
```

## Environment Configuration

### Required Environment Variables
```env
# Redis URL (Upstash or local)
REDIS_URL=rediss://default:[PASSWORD]@[ENDPOINT]:6379

# Optional: Local Redis settings
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=password
REDIS_DB=0
```

## Performance Characteristics

### Cache Hit Rates (Expected)
- **Sessions**: ~95% (30-day TTL)
- **Exchange Rates**: ~80% (5-minute TTL, frequent updates)
- **Tariffs**: ~90% (1-hour TTL, infrequent changes)

### Latency
- **Upstash Redis**: ~50-100ms (cloud-hosted)
- **Local Redis**: ~1-5ms (Docker)

### Database Load Reduction
- **Target**: 70% reduction in database queries
- **Mechanism**: Cache-first strategy for frequently accessed data

## Integration Points

### Current Integrations
- ✅ Configuration system (`config.py`)
- ✅ Test suite (`test_redis_client.py`)

### Future Integrations (Upcoming Tasks)
- ⏳ Authentication middleware (Task 6.x)
- ⏳ Exchange rate service (Task 16.x)
- ⏳ Billing engine (Task 15.x)
- ⏳ Rate limiting middleware (Task 5.3)

## Troubleshooting

### Connection Issues
If you see "Timeout connecting to server":
1. Check `REDIS_URL` in `.env`
2. Verify Upstash Redis instance is active
3. Check firewall/network settings
4. Increase timeout in `redis_client.py` if needed

### Cache Misses
If cache hit rate is low:
1. Check TTL settings are appropriate
2. Verify keys are being set correctly
3. Monitor Redis memory usage
4. Consider increasing TTL for stable data

### Memory Issues
If Redis runs out of memory:
1. Check cache eviction policy (LRU recommended)
2. Reduce TTL for less critical data
3. Implement cache size limits
4. Consider upgrading Redis instance

## Next Steps

### Immediate (Week 2)
- [ ] Integrate with authentication endpoints (Task 6.x)
- [ ] Add rate limiting middleware (Task 5.3)
- [ ] Implement session management in auth flow

### Short-term (Week 3-4)
- [ ] Integrate with exchange rate service (Task 16.x)
- [ ] Add tariff caching in billing engine (Task 15.x)
- [ ] Monitor cache performance metrics

### Long-term (Post-MVP)
- [ ] Add Redis Cluster support for high availability
- [ ] Implement cache warming strategies
- [ ] Add cache analytics dashboard
- [ ] Optimize TTL values based on usage patterns

## References

### Documentation
- [Redis Python Client](https://redis-py.readthedocs.io/)
- [Upstash Redis](https://upstash.com/docs/redis)
- [Hedera Flow Requirements](requirements.md) - FR-5.3, NFR-3.3

### Related Files
- `backend/app/utils/redis_client.py` - Redis client implementation
- `backend/config.py` - Configuration management
- `backend/.env` - Environment variables
- `backend/test_redis_client.py` - Test suite
- `backend/REDIS_CACHE_STRUCTURE.md` - Cache structure documentation

---

**Status**: ✅ Complete  
**Task**: 5.5 Set up Redis client  
**Date**: February 19, 2026  
**Test Results**: 6/6 tests passed
