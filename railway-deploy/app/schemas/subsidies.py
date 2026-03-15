"""
Pydantic schemas for subsidy eligibility endpoints

Requirements: FR-4.5 (System shall apply subsidies if user eligible)
"""
from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime


class SubsidyEligibilityResponse(BaseModel):
    """Response schema for subsidy eligibility check"""
    user_id: str = Field(..., description="User UUID")
    eligible: bool = Field(..., description="Whether user is eligible for subsidies")
    subsidy_type: Optional[str] = Field(None, description="Type of subsidy (low_income, senior_citizen, disability, energy_efficiency)")
    verified_at: Optional[datetime] = Field(None, description="When eligibility was verified")
    expires_at: Optional[datetime] = Field(None, description="When eligibility expires")
    expired: bool = Field(False, description="Whether eligibility has expired")
    reason: Optional[str] = Field(None, description="Reason for ineligibility (if not eligible)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "123e4567-e89b-12d3-a456-426614174000",
                "eligible": True,
                "subsidy_type": "low_income",
                "verified_at": "2024-01-15T10:30:00Z",
                "expires_at": "2025-01-15T10:30:00Z",
                "expired": False,
                "reason": None
            }
        }


class SetSubsidyEligibilityRequest(BaseModel):
    """Request schema for setting user subsidy eligibility (admin only)"""
    eligible: bool = Field(..., description="Whether user is eligible for subsidies")
    subsidy_type: Optional[str] = Field(None, description="Type of subsidy")
    expires_at: Optional[datetime] = Field(None, description="When eligibility expires (optional)")
    
    @validator('subsidy_type')
    def validate_subsidy_type(cls, v, values):
        """Validate subsidy type if user is eligible"""
        if values.get('eligible') and v:
            valid_types = ['low_income', 'senior_citizen', 'disability', 'energy_efficiency']
            if v not in valid_types:
                raise ValueError(f"subsidy_type must be one of: {', '.join(valid_types)}")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "eligible": True,
                "subsidy_type": "low_income",
                "expires_at": "2025-12-31T23:59:59Z"
            }
        }


class SetSubsidyEligibilityResponse(BaseModel):
    """Response schema for setting user subsidy eligibility"""
    user_id: str = Field(..., description="User UUID")
    eligible: bool = Field(..., description="Whether user is eligible for subsidies")
    subsidy_type: Optional[str] = Field(None, description="Type of subsidy")
    verified_at: Optional[datetime] = Field(None, description="When eligibility was verified")
    expires_at: Optional[datetime] = Field(None, description="When eligibility expires")
    message: str = Field(..., description="Success message")
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "123e4567-e89b-12d3-a456-426614174000",
                "eligible": True,
                "subsidy_type": "low_income",
                "verified_at": "2024-02-22T10:30:00Z",
                "expires_at": "2025-12-31T23:59:59Z",
                "message": "Subsidy eligibility updated successfully"
            }
        }
