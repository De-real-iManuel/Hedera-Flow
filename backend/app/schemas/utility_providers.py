"""
Utility Provider Schemas
Pydantic models for utility provider-related API requests and responses
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# Request Schemas
class UtilityProviderCreateRequest(BaseModel):
    """Create utility provider request (admin only)"""
    country_code: str = Field(..., pattern=r"^(ES|US|IN|BR|NG)$")
    state_province: str = Field(..., min_length=2, max_length=100)
    provider_name: str = Field(..., min_length=2, max_length=100)
    provider_code: str = Field(..., min_length=2, max_length=20)
    service_areas: List[str] = Field(default_factory=list)
    is_active: bool = True


class UtilityProviderUpdateRequest(BaseModel):
    """Update utility provider request (admin only)"""
    provider_name: Optional[str] = Field(None, min_length=2, max_length=100)
    service_areas: Optional[List[str]] = None
    is_active: Optional[bool] = None


# Response Schemas
class UtilityProviderResponse(BaseModel):
    """Utility provider data in responses"""
    id: str
    country_code: str
    state_province: str
    provider_name: str
    provider_code: str
    service_areas: List[str]
    is_active: bool

    class Config:
        from_attributes = True


class UtilityProviderListResponse(BaseModel):
    """List of utility providers response"""
    providers: List[UtilityProviderResponse]
    total: int


class UtilityProviderSummary(BaseModel):
    """Simplified utility provider data for dropdowns"""
    id: str
    provider_name: str
    provider_code: str
    state_province: str

    class Config:
        from_attributes = True
