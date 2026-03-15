"""
Common Schemas
Shared Pydantic models used across multiple endpoints
"""

from pydantic import BaseModel, Field
from typing import Optional, Any, Dict
from datetime import datetime


class ErrorResponse(BaseModel):
    """Standard error response"""
    error: str
    detail: Optional[str] = None
    code: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class SuccessResponse(BaseModel):
    """Standard success response"""
    message: str
    data: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class PaginationParams(BaseModel):
    """Pagination query parameters"""
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


class PaginatedResponse(BaseModel):
    """Base paginated response"""
    total: int
    limit: int
    offset: int
    has_more: bool


class HealthCheckResponse(BaseModel):
    """Health check endpoint response"""
    status: str = "healthy"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    version: str = "1.0.0"
    services: Dict[str, str] = Field(default_factory=dict)
    # services example: {"database": "connected", "redis": "connected", "hedera": "connected"}


class ValidationErrorDetail(BaseModel):
    """Validation error detail"""
    loc: list[str | int]
    msg: str
    type: str


class ValidationErrorResponse(BaseModel):
    """Validation error response (422)"""
    detail: list[ValidationErrorDetail]


class ExchangeRateResponse(BaseModel):
    """Exchange rate response schema"""
    currency: str = Field(..., description="Currency code (EUR, USD, INR, BRL, NGN)")
    hbar_price: float = Field(..., description="Price of 1 HBAR in fiat currency", alias="hbarPrice")
    source: str = Field(..., description="API source (coingecko, coinmarketcap)")
    fetched_at: str = Field(..., description="ISO 8601 timestamp when rate was fetched", alias="fetchedAt")
    
    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "currency": "EUR",
                "hbarPrice": 0.34,
                "source": "coingecko",
                "fetchedAt": "2024-03-18T10:30:00Z"
            }
        }
