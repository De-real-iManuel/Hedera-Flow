"""
Exchange Rate Endpoints
HBAR/fiat exchange rate queries

Implements FR-5.2, US-7:
- FR-5.2: System shall fetch real-time HBAR exchange rates from CoinGecko/CoinMarketCap API
- US-7: Payment with HBAR (Native Token)
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Annotated
import logging

from app.core.dependencies import get_db
from app.services.exchange_rate_service import ExchangeRateService, ExchangeRateError
from app.schemas.common import ExchangeRateResponse, ErrorResponse

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/exchange-rate/{currency}",
    response_model=ExchangeRateResponse,
    responses={
        200: {
            "description": "Exchange rate fetched successfully",
            "model": ExchangeRateResponse
        },
        404: {
            "description": "Currency not supported",
            "model": ErrorResponse
        },
        503: {
            "description": "Exchange rate API unavailable",
            "model": ErrorResponse
        }
    },
    summary="Get HBAR exchange rate",
    description="""
    Get current HBAR price in specified currency.
    
    **Supported currencies**: EUR, USD, INR, BRL, NGN
    
    **Flow**:
    1. Check Redis cache (5 min TTL)
    2. If cache miss, fetch from CoinGecko API
    3. Store in cache and database
    4. Return price
    
    **Requirements**: FR-5.2, US-7
    
    **Example**:
    ```
    GET /api/exchange-rate/EUR
    
    Response:
    {
        "currency": "EUR",
        "hbarPrice": 0.34,
        "source": "coingecko",
        "fetchedAt": "2024-03-18T10:30:00Z"
    }
    ```
    """
)
async def get_exchange_rate(
    currency: str,
    db: Annotated[Session, Depends(get_db)]
) -> ExchangeRateResponse:
    """
    Get current HBAR exchange rate for specified currency.
    
    Args:
        currency: Currency code (EUR, USD, INR, BRL, NGN)
        db: Database session (injected)
    
    Returns:
        ExchangeRateResponse with current HBAR price
    
    Raises:
        HTTPException 404: Currency not supported
        HTTPException 503: Exchange rate API unavailable
    """
    try:
        # Initialize exchange rate service
        service = ExchangeRateService(db)
        
        # Validate and normalize currency
        currency = currency.upper()
        
        # Get HBAR price (uses cache if available)
        hbar_price = service.get_hbar_price(currency, use_cache=True)
        
        # Get cached rate data for metadata
        rate_data = service.get_cached_rate(currency)
        
        # If not in cache (shouldn't happen since we just fetched), get from DB
        if not rate_data:
            db_rate = service.get_latest_rate_from_db(currency)
            if db_rate:
                rate_data = db_rate
            else:
                # Fallback to minimal response
                from datetime import datetime, timezone
                rate_data = {
                    'currency': currency,
                    'hbarPrice': hbar_price,
                    'source': 'coingecko',
                    'fetchedAt': datetime.now(timezone.utc).isoformat()
                }
        
        logger.info(f"Exchange rate fetched: {currency} = {hbar_price}")
        
        return ExchangeRateResponse(
            currency=rate_data['currency'],
            hbarPrice=rate_data['hbarPrice'],
            source=rate_data['source'],
            fetchedAt=rate_data['fetchedAt']
        )
        
    except ExchangeRateError as e:
        error_msg = str(e)
        
        # Check if it's a currency not supported error
        if "not supported" in error_msg.lower():
            logger.warning(f"Currency not supported: {currency}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Currency {currency} not supported. Supported currencies: EUR, USD, INR, BRL, NGN"
            )
        
        # Otherwise it's an API error
        logger.error(f"Exchange rate API error: {error_msg}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Exchange rate API unavailable: {error_msg}"
        )
        
    except Exception as e:
        logger.error(f"Unexpected error in exchange rate endpoint: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while fetching exchange rate"
        )
