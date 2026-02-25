# Rate Limiting Implementation

## Overview

The Hedera Flow API implements rate limiting to prevent abuse and ensure fair usage across all users. The rate limiting is implemented using the `slowapi` library with a fixed-window strategy.

## Configuration

### Default Limits
- **100 requests per minute** per client (configurable via `RATE_LIMIT_PER_MINUTE` environment variable)
- Fixed-window strategy (resets every minute)
- In-memory storage (will be upgraded to Redis in Task 5.5)

### Client Identification
Rate limits are applied based on:
1. **Authenticated users**: User ID from JWT token
2. **Anonymous users**: IP address

This ensures that authenticated users have their own rate limit quota, while anonymous requests are limited per IP address.

## Usage

### Applying Rate Limits to Endpoints

To apply rate limiting to an endpoint, use the `@limiter.limit()` decorator:

```python
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from app.core.rate_limit import limiter
from config import settings

router = APIRouter()

@router.get("/my-endpoint")
@limiter.limit(f"{settings.rate_limit_per_minute}/minute")
async def my_endpoint(request: Request):
    """
    Your endpoint logic here
    Note: Must include Request parameter and return JSONResponse
    """
    return JSONResponse({"message": "Success"})
```

### Custom Rate Limits

You can override the default rate limit for specific endpoints:

```python
@router.post("/expensive-operation")
@limiter.limit("10/minute")  # Only 10 requests per minute
async def expensive_operation(request: Request):
    return JSONResponse({"message": "Operation completed"})
```

### Multiple Rate Limits

You can apply multiple rate limits to a single endpoint:

```python
@router.post("/critical-endpoint")
@limiter.limit("100/minute")  # 100 per minute
@limiter.limit("1000/hour")   # 1000 per hour
async def critical_endpoint(request: Request):
    return JSONResponse({"message": "Success"})
```

## Response Headers

When rate limiting is active, the following headers are included in responses:

- `X-RateLimit-Limit`: Maximum number of requests allowed in the time window
- `X-RateLimit-Remaining`: Number of requests remaining in the current window
- `X-RateLimit-Reset`: Unix timestamp when the rate limit resets

Example:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1710789660
```

## Rate Limit Exceeded Response

When a client exceeds the rate limit, they receive a `429 Too Many Requests` response:

```json
{
  "error": "Rate limit exceeded: 100 per 1 minute"
}
```

## Testing

Run the rate limiting tests:

```bash
pytest tests/test_rate_limit.py -v
```

## Future Enhancements (Task 5.5)

When Redis is integrated:
1. Update `get_storage_uri()` in `app/core/rate_limit.py` to use Redis
2. This will enable distributed rate limiting across multiple server instances
3. Rate limit state will persist across server restarts

Example Redis integration:
```python
def get_storage_uri() -> str:
    """Get storage URI for rate limiting"""
    if settings.redis_url:
        return settings.redis_url
    return "memory://"
```

## Security Considerations

1. **DDoS Protection**: Rate limiting helps prevent denial-of-service attacks
2. **Fair Usage**: Ensures all users get fair access to API resources
3. **Cost Control**: Prevents excessive API calls that could increase infrastructure costs
4. **Per-User Limits**: Authenticated users have individual quotas, preventing one user from affecting others

## Monitoring

To monitor rate limiting effectiveness:
1. Check application logs for rate limit exceeded events
2. Monitor `X-RateLimit-*` headers in responses
3. Track which endpoints are hitting rate limits most frequently
4. Adjust limits based on usage patterns

## Configuration Options

Environment variables:
- `RATE_LIMIT_PER_MINUTE`: Number of requests allowed per minute (default: 100)

Example `.env`:
```
RATE_LIMIT_PER_MINUTE=100
```

## Troubleshooting

### Issue: Rate limit too restrictive
**Solution**: Increase `RATE_LIMIT_PER_MINUTE` in `.env` file

### Issue: Rate limit not working
**Solution**: Ensure `@limiter.limit()` decorator is applied and endpoint returns `JSONResponse`

### Issue: Rate limit resets unexpectedly
**Solution**: This is expected with in-memory storage. Will be resolved when Redis is integrated (Task 5.5)

## References

- [SlowAPI Documentation](https://slowapi.readthedocs.io/)
- [FastAPI Middleware](https://fastapi.tiangolo.com/tutorial/middleware/)
- [Rate Limiting Best Practices](https://cloud.google.com/architecture/rate-limiting-strategies-techniques)
