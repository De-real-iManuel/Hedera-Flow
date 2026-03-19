"""
Health Check Endpoints
System health and status monitoring
"""
from fastapi import APIRouter, Request, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime

from config import settings
from app.core.rate_limit import limiter
from app.core.database import check_db_connection, get_db_stats, get_db

router = APIRouter()


@router.get("/health")
@limiter.limit(f"{settings.rate_limit_per_minute}/minute")
async def health_check(request: Request):
    """
    Comprehensive health check endpoint
    Returns status of all system components
    
    Rate limited to prevent abuse
    """
    # Check database connection
    db_healthy = check_db_connection()
    db_status = "operational" if db_healthy else "unavailable"
    
    # Get database pool stats if healthy
    db_stats = None
    if db_healthy:
        try:
            db_stats = get_db_stats()
        except Exception:
            db_stats = None
    
    return JSONResponse({
        "status": "healthy" if db_healthy else "degraded",
        "timestamp": datetime.utcnow().isoformat(),
        "environment": settings.environment,
        "version": "1.0.0",
        "components": {
            "api": "operational",
            "database": db_status,
            "redis": "not_configured",      # TODO: Check Redis connection
            "hedera": "not_configured"      # TODO: Check Hedera network
        },
        "database_pool": db_stats
    })


@router.get("/health/ready")
async def readiness_check():
    """
    Readiness probe for Kubernetes/container orchestration
    Returns 200 if service is ready to accept traffic
    """
    # Check if database is ready
    db_ready = check_db_connection()
    
    if not db_ready:
        return JSONResponse(
            status_code=503,
            content={"ready": False, "reason": "Database not ready"}
        )
    
    return {"ready": True}


@router.get("/health/live")
async def liveness_check():
    """
    Liveness probe for Kubernetes/container orchestration
    Returns 200 if service is alive
    """
    return {"alive": True}


@router.post("/health/seed-tariffs")
async def seed_tariffs(db: Session = Depends(get_db)):
    """Force-seed tariffs and return current DB state"""
    NG_BANDS = '{"type":"band_based","bands":[{"name":"A","hours_min":20,"price":225},{"name":"B","hours_min":16,"price":63},{"name":"C","hours_min":12,"price":50},{"name":"D","hours_min":8,"price":43},{"name":"E","hours_min":0,"price":40}]}'
    ROWS = [
        ('NG','Eko Electricity Distribution Company',   'NGN', NG_BANDS, '{"vat":0.075}'),
        ('NG','Ikeja Electric',                         'NGN', NG_BANDS, '{"vat":0.075}'),
        ('NG','Abuja Electricity Distribution Company', 'NGN', NG_BANDS, '{"vat":0.075}'),
        ('NG','Enugu Electricity Distribution Company', 'NGN', NG_BANDS, '{"vat":0.075}'),
        ('NG','Port Harcourt Electricity Distribution', 'NGN', NG_BANDS, '{"vat":0.075}'),
        ('NG','Ibadan Electricity Distribution Company','NGN', NG_BANDS, '{"vat":0.075}'),
        ('NG','Kano Electricity Distribution Company',  'NGN', NG_BANDS, '{"vat":0.075}'),
        ('NG','Kaduna Electricity Distribution Company','NGN', NG_BANDS, '{"vat":0.075}'),
        ('NG','Jos Electricity Distribution Company',   'NGN', NG_BANDS, '{"vat":0.075}'),
        ('NG','Benin Electricity Distribution Company', 'NGN', NG_BANDS, '{"vat":0.075}'),
        ('NG','Yola Electricity Distribution Company',  'NGN', NG_BANDS, '{"vat":0.075}'),
        ('ES','Iberdrola','EUR','{"type":"flat","rate":0.18}','{"vat":0.21}'),
        ('ES','Endesa',   'EUR','{"type":"flat","rate":0.18}','{"vat":0.21}'),
        ('ES','Naturgy',  'EUR','{"type":"flat","rate":0.18}','{"vat":0.21}'),
        ('US','Pacific Gas & Electric','USD','{"type":"tiered","tiers":[{"limit":500,"price":0.12},{"limit":null,"price":0.18}]}','{"tax":0.08}'),
        ('US','Con Edison',            'USD','{"type":"tiered","tiers":[{"limit":500,"price":0.12},{"limit":null,"price":0.18}]}','{"tax":0.08}'),
        ('US','ComEd',                 'USD','{"type":"tiered","tiers":[{"limit":500,"price":0.12},{"limit":null,"price":0.18}]}','{"tax":0.08}'),
        ('US','Florida Power & Light', 'USD','{"type":"tiered","tiers":[{"limit":500,"price":0.12},{"limit":null,"price":0.18}]}','{"tax":0.08}'),
        ('US','Texas Electric',        'USD','{"type":"tiered","tiers":[{"limit":500,"price":0.12},{"limit":null,"price":0.18}]}','{"tax":0.08}'),
        ('IN','Tata Power',   'INR','{"type":"tiered","tiers":[{"limit":100,"price":3.5},{"limit":300,"price":5.5},{"limit":null,"price":7.5}]}','{"tax":0.05}'),
        ('IN','BSES Rajdhani','INR','{"type":"tiered","tiers":[{"limit":100,"price":3.5},{"limit":300,"price":5.5},{"limit":null,"price":7.5}]}','{"tax":0.05}'),
        ('IN','BSES Yamuna',  'INR','{"type":"tiered","tiers":[{"limit":100,"price":3.5},{"limit":300,"price":5.5},{"limit":null,"price":7.5}]}','{"tax":0.05}'),
        ('IN','BESCOM',       'INR','{"type":"tiered","tiers":[{"limit":100,"price":3.5},{"limit":300,"price":5.5},{"limit":null,"price":7.5}]}','{"tax":0.05}'),
        ('IN','TNEB',         'INR','{"type":"tiered","tiers":[{"limit":100,"price":3.5},{"limit":300,"price":5.5},{"limit":null,"price":7.5}]}','{"tax":0.05}'),
        ('BR','CEMIG',         'BRL','{"type":"tiered","tiers":[{"limit":200,"price":0.65},{"limit":null,"price":0.85}]}','{"icms":0.20}'),
        ('BR','ENEL São Paulo','BRL','{"type":"tiered","tiers":[{"limit":200,"price":0.65},{"limit":null,"price":0.85}]}','{"icms":0.20}'),
        ('BR','COPEL',         'BRL','{"type":"tiered","tiers":[{"limit":200,"price":0.65},{"limit":null,"price":0.85}]}','{"icms":0.20}'),
        ('BR','CELPE',         'BRL','{"type":"tiered","tiers":[{"limit":200,"price":0.65},{"limit":null,"price":0.85}]}','{"icms":0.20}'),
    ]

    inserted = []
    errors = []
    for (cc, provider, currency, rate_json, taxes_json) in ROWS:
        try:
            result = db.execute(text("""
                INSERT INTO tariffs (country_code, utility_provider, currency, rate_structure, taxes_and_fees, valid_from, is_active)
                SELECT :cc, :provider, :currency, :rate::jsonb, :taxes::jsonb, '2024-01-01', true
                WHERE NOT EXISTS (
                    SELECT 1 FROM tariffs WHERE country_code=:cc AND utility_provider=:provider AND is_active=true
                )
            """), {'cc': cc, 'provider': provider, 'currency': currency, 'rate': rate_json, 'taxes': taxes_json})
            if result.rowcount > 0:
                inserted.append(f"{cc}/{provider}")
        except Exception as e:
            errors.append(f"{cc}/{provider}: {str(e)}")
            db.rollback()

    db.commit()

    # Return current state
    all_tariffs = db.execute(text(
        "SELECT country_code, utility_provider FROM tariffs WHERE is_active=true ORDER BY country_code, utility_provider"
    )).fetchall()

    return {
        "inserted": inserted,
        "errors": errors,
        "total_active_tariffs": len(all_tariffs),
        "tariffs": [{"country": r[0], "provider": r[1]} for r in all_tariffs]
    }
