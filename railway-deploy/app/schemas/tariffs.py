"""
Tariff Schemas
Pydantic models for tariff-related API requests and responses
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from .bills import Currency


class RateStructureType(str, Enum):
    """Rate structure types"""
    FLAT = "flat"
    TIERED = "tiered"
    TIME_OF_USE = "time_of_use"
    BAND_BASED = "band_based"


# Request Schemas
class TariffCreateRequest(BaseModel):
    """Create tariff request (admin only)"""
    utility_provider_id: str
    country_code: str = Field(..., pattern=r"^(ES|US|IN|BR|NG)$")
    state_province: str = Field(..., min_length=2, max_length=100)
    utility_provider: str = Field(..., min_length=2, max_length=100)
    currency: Currency
    rate_structure: Dict[str, Any]
    taxes_and_fees: Dict[str, Any]
    subsidies: Optional[Dict[str, Any]] = None
    valid_from: date
    valid_until: Optional[date] = None
    is_active: bool = True


class TariffUpdateRequest(BaseModel):
    """Update tariff request (admin only)"""
    rate_structure: Optional[Dict[str, Any]] = None
    taxes_and_fees: Optional[Dict[str, Any]] = None
    subsidies: Optional[Dict[str, Any]] = None
    valid_from: Optional[date] = None
    valid_until: Optional[date] = None
    is_active: Optional[bool] = None


# Response Schemas
class TariffResponse(BaseModel):
    """Tariff data in responses"""
    id: str
    utility_provider_id: str
    country_code: str
    state_province: str
    utility_provider: str
    currency: Currency
    
    # Rate structure
    rate_structure: Dict[str, Any]
    
    # Taxes and fees
    taxes_and_fees: Dict[str, Any]
    
    # Subsidies
    subsidies: Optional[Dict[str, Any]]
    
    # Validity
    valid_from: date
    valid_until: Optional[date]
    is_active: bool
    
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TariffListResponse(BaseModel):
    """List of tariffs response"""
    tariffs: List[TariffResponse]
    total: int


class TariffSummary(BaseModel):
    """Simplified tariff data for lists"""
    id: str
    country_code: str
    utility_provider: str
    currency: Currency
    rate_structure_type: str
    valid_from: date
    valid_until: Optional[date]
    is_active: bool

    class Config:
        from_attributes = True


# Example rate structure schemas for documentation
class FlatRateStructure(BaseModel):
    """Flat rate structure example"""
    type: str = "flat"
    price_per_kwh: Decimal


class TieredRateStructure(BaseModel):
    """Tiered rate structure example"""
    type: str = "tiered"
    tiers: List[Dict[str, Any]]  # [{"min": 0, "max": 100, "price": 0.10}, ...]


class TimeOfUseRateStructure(BaseModel):
    """Time-of-use rate structure example"""
    type: str = "time_of_use"
    periods: List[Dict[str, Any]]  # [{"name": "peak", "hours": [10,11,...], "price": 0.40}, ...]


class BandBasedRateStructure(BaseModel):
    """Band-based rate structure example (Nigeria)"""
    type: str = "band_based"
    bands: List[Dict[str, Any]]  # [{"name": "A", "hours_min": 20, "price": 225.00}, ...]
