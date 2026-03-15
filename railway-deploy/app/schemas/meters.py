"""
Meter Management Schemas
Pydantic models for meter-related API requests and responses
"""

from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime
from enum import Enum


class MeterType(str, Enum):
    """Meter types"""
    PREPAID = "prepaid"
    POSTPAID = "postpaid"


class BandClassification(str, Enum):
    """Nigeria band classification"""
    A = "A"  # 20+ hours supply
    B = "B"  # 16-20 hours
    C = "C"  # 12-16 hours
    D = "D"  # 8-12 hours
    E = "E"  # <8 hours


# Request Schemas
class MeterCreateRequest(BaseModel):
    """Create meter request"""
    meter_id: str = Field(..., min_length=5, max_length=50)
    utility_provider_id: str
    state_province: str = Field(..., min_length=2, max_length=100)
    utility_provider: str = Field(..., min_length=2, max_length=100)
    meter_type: MeterType
    band_classification: Optional[BandClassification] = None
    address: Optional[str] = Field(None, max_length=500)
    is_primary: bool = False

    @validator('band_classification')
    def validate_band_for_nigeria(cls, v, values):
        """Band classification is required for Nigeria meters"""
        # Note: This validation would need country_code from user context
        # For now, we just validate the field itself
        return v


class MeterUpdateRequest(BaseModel):
    """Update meter request"""
    utility_provider_id: Optional[str] = None
    state_province: Optional[str] = Field(None, min_length=2, max_length=100)
    utility_provider: Optional[str] = Field(None, min_length=2, max_length=100)
    meter_type: Optional[MeterType] = None
    band_classification: Optional[BandClassification] = None
    address: Optional[str] = Field(None, max_length=500)
    is_primary: Optional[bool] = None


# Response Schemas
class MeterResponse(BaseModel):
    """Meter data in responses"""
    id: str
    user_id: str
    meter_id: str
    utility_provider_id: str
    state_province: str
    utility_provider: str
    meter_type: MeterType
    band_classification: Optional[BandClassification]
    address: Optional[str]
    is_primary: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class MeterListResponse(BaseModel):
    """List of meters response"""
    meters: list[MeterResponse]
    total: int
