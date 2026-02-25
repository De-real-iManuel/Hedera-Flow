"""
Health Check Endpoints
System health and status monitoring
"""
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from datetime import datetime

from config import settings
from app.core.rate_limit import limiter
from app.core.database import check_db_connection, get_db_stats

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
