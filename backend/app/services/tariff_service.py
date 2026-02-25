"""
Tariff Service - Fetch tariffs from database with Redis caching

Implements tariff fetching logic with 1-hour cache for performance.
Requirements: FR-4.1
"""
from typing import Dict, Any, Optional
from datetime import datetime, date
from sqlalchemy.orm import Session
from sqlalchemy import text
import logging

from app.utils.redis_client import redis_client

logger = logging.getLogger(__name__)


class TariffNotFoundError(Exception):
    """Raised when tariff is not found for given parameters"""
    pass


class TariffServiceError(Exception):
    """Raised when tariff service encounters an error"""
    pass


def get_tariff(
    db: Session,
    country_code: str,
    utility_provider: str,
    use_cache: bool = True
) -> Dict[str, Any]:
    """
    Fetch tariff data from cache or database.
    
    Caching Strategy:
    1. Check Redis cache first (TTL: 1 hour)
    2. If cache miss, query database
    3. Store result in cache for future requests
    
    Args:
        db: Database session
        country_code: Country code (ES, US, IN, BR, NG)
        utility_provider: Utility provider name
        use_cache: Whether to use Redis cache (default: True)
    
    Returns:
        Dictionary containing:
            - tariff_id: UUID of tariff
            - country_code: Country code
            - utility_provider: Utility provider name
            - currency: Currency code (EUR, USD, INR, BRL, NGN)
            - rate_structure: Rate structure (JSONB)
            - taxes_and_fees: Taxes and fees (JSONB)
            - subsidies: Subsidies (JSONB)
            - valid_from: Valid from date
            - valid_until: Valid until date (optional)
    
    Raises:
        TariffNotFoundError: If no active tariff found
        TariffServiceError: If service encounters an error
    """
    try:
        # Normalize inputs
        country_code = country_code.upper()
        
        # Try cache first if enabled
        if use_cache:
            cached_tariff = redis_client.get_tariff(country_code, utility_provider)
            if cached_tariff:
                logger.info(f"Tariff cache HIT: {country_code}/{utility_provider}")
                return cached_tariff
            logger.info(f"Tariff cache MISS: {country_code}/{utility_provider}")
        
        # Query database for active tariff
        tariff = _fetch_tariff_from_db(db, country_code, utility_provider)
        
        if not tariff:
            raise TariffNotFoundError(
                f"No active tariff found for {country_code}/{utility_provider}"
            )
        
        # Convert to dictionary
        tariff_data = {
            'tariff_id': str(tariff['id']),
            'country_code': tariff['country_code'],
            'utility_provider': tariff['utility_provider'],
            'currency': tariff['currency'],
            'rate_structure': tariff['rate_structure'],
            'taxes_and_fees': tariff['taxes_and_fees'] or {},
            'subsidies': tariff['subsidies'] or {},
            'valid_from': tariff['valid_from'].isoformat() if tariff['valid_from'] else None,
            'valid_until': tariff['valid_until'].isoformat() if tariff['valid_until'] else None,
        }
        
        # Store in cache if enabled
        if use_cache:
            redis_client.set_tariff(country_code, utility_provider, tariff_data)
            logger.info(f"Tariff cached: {country_code}/{utility_provider}")
        
        return tariff_data
        
    except TariffNotFoundError:
        raise
    except Exception as e:
        logger.error(f"Tariff service error: {e}", exc_info=True)
        raise TariffServiceError(f"Failed to fetch tariff: {str(e)}")


def _fetch_tariff_from_db(
    db: Session,
    country_code: str,
    utility_provider: str
) -> Optional[Dict[str, Any]]:
    """
    Fetch active tariff from database.
    
    Query logic:
    1. Match country_code and utility_provider
    2. Filter by is_active = true
    3. Filter by valid date range (valid_from <= today <= valid_until)
    4. Order by valid_from DESC (most recent first)
    5. Return first result
    
    Args:
        db: Database session
        country_code: Country code
        utility_provider: Utility provider name
    
    Returns:
        Tariff row as dictionary or None if not found
    """
    today = date.today()
    
    query = text("""
        SELECT 
            id,
            country_code,
            utility_provider,
            currency,
            rate_structure,
            taxes_and_fees,
            subsidies,
            valid_from,
            valid_until
        FROM tariffs
        WHERE country_code = :country_code
          AND utility_provider = :utility_provider
          AND is_active = true
          AND valid_from <= :today
          AND (valid_until IS NULL OR valid_until >= :today)
        ORDER BY valid_from DESC
        LIMIT 1
    """)
    
    result = db.execute(
        query,
        {
            'country_code': country_code,
            'utility_provider': utility_provider,
            'today': today
        }
    ).fetchone()
    
    if result:
        # Convert Row to dictionary
        return {
            'id': result[0],
            'country_code': result[1],
            'utility_provider': result[2],
            'currency': result[3],
            'rate_structure': result[4],
            'taxes_and_fees': result[5],
            'subsidies': result[6],
            'valid_from': result[7],
            'valid_until': result[8]
        }
    
    return None


def invalidate_tariff_cache(
    country_code: str,
    utility_provider: str
) -> bool:
    """
    Invalidate tariff cache for a specific country/provider.
    
    Use this when tariff data is updated in the database.
    
    Args:
        country_code: Country code
        utility_provider: Utility provider name
    
    Returns:
        True if cache was invalidated, False otherwise
    """
    try:
        country_code = country_code.upper()
        result = redis_client.delete_tariff(country_code, utility_provider)
        if result:
            logger.info(f"Tariff cache invalidated: {country_code}/{utility_provider}")
        return result
    except Exception as e:
        logger.error(f"Failed to invalidate tariff cache: {e}")
        return False


def get_all_tariffs(
    db: Session,
    country_code: Optional[str] = None,
    utility_provider: Optional[str] = None,
    active_only: bool = True
) -> list[Dict[str, Any]]:
    """
    Fetch all tariffs from database with optional filters.
    
    Note: This function does NOT use cache as it returns multiple results.
    
    Args:
        db: Database session
        country_code: Filter by country code (optional)
        utility_provider: Filter by utility provider (optional)
        active_only: Only return active tariffs (default: True)
    
    Returns:
        List of tariff dictionaries
    """
    try:
        # Build query dynamically based on filters
        conditions = []
        params = {}
        
        if country_code:
            conditions.append("country_code = :country_code")
            params['country_code'] = country_code.upper()
        
        if utility_provider:
            conditions.append("utility_provider = :utility_provider")
            params['utility_provider'] = utility_provider
        
        if active_only:
            conditions.append("is_active = true")
            today = date.today()
            conditions.append("valid_from <= :today")
            conditions.append("(valid_until IS NULL OR valid_until >= :today)")
            params['today'] = today
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        query = text(f"""
            SELECT 
                id,
                country_code,
                utility_provider,
                currency,
                rate_structure,
                taxes_and_fees,
                subsidies,
                valid_from,
                valid_until,
                is_active
            FROM tariffs
            WHERE {where_clause}
            ORDER BY country_code, utility_provider, valid_from DESC
        """)
        
        results = db.execute(query, params).fetchall()
        
        tariffs = []
        for row in results:
            tariffs.append({
                'tariff_id': str(row[0]),
                'country_code': row[1],
                'utility_provider': row[2],
                'currency': row[3],
                'rate_structure': row[4],
                'taxes_and_fees': row[5] or {},
                'subsidies': row[6] or {},
                'valid_from': row[7].isoformat() if row[7] else None,
                'valid_until': row[8].isoformat() if row[8] else None,
                'is_active': row[9]
            })
        
        return tariffs
        
    except Exception as e:
        logger.error(f"Failed to fetch all tariffs: {e}", exc_info=True)
        raise TariffServiceError(f"Failed to fetch tariffs: {str(e)}")
