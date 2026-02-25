"""
API Router
Aggregates all API route modules
"""
from fastapi import APIRouter

from app.api.endpoints import health, auth, meters, bills, payments, utility_providers, verify

# Create main API router
api_router = APIRouter()

# Include endpoint routers
api_router.include_router(
    health.router,
    tags=["health"]
)

api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["auth"]
)

api_router.include_router(
    meters.router,
    prefix="/meters",
    tags=["meters"]
)

api_router.include_router(
    verify.router,
    tags=["verification"]
)

api_router.include_router(
    bills.router,
    prefix="/bills",
    tags=["bills"]
)

api_router.include_router(
    payments.router,
    prefix="/payments",
    tags=["payments"]
)

api_router.include_router(
    utility_providers.router,
    prefix="/utility-providers",
    tags=["utility-providers"]
)

# TODO: Add more routers as they are implemented
# api_router.include_router(disputes.router, prefix="/disputes", tags=["disputes"])
# api_router.include_router(tariffs.router, prefix="/tariffs", tags=["tariffs"])

