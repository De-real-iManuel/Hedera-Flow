"""
User Preferences Schemas
Pydantic models for user preferences and settings
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class NotificationPreferences(BaseModel):
    """Notification preferences"""
    bill_reminders: bool = Field(default=True, description="Enable bill payment reminders")
    payment_confirmations: bool = Field(default=True, description="Enable payment confirmations")
    subsidy_updates: bool = Field(default=True, description="Enable subsidy eligibility updates")
    email_notifications: bool = Field(default=True, description="Enable email notifications")
    push_notifications: bool = Field(default=False, description="Enable push notifications")


class UserPreferences(BaseModel):
    """User preferences"""
    theme: str = Field(default="light", description="UI theme (light/dark)")
    language: str = Field(default="en", description="Preferred language")
    currency_display: str = Field(default="local", description="Currency display preference")
    notifications: NotificationPreferences = Field(default_factory=NotificationPreferences)


class SecuritySettings(BaseModel):
    """Security settings"""
    biometric_enabled: bool = Field(default=False, description="Biometric authentication enabled")
    pin_enabled: bool = Field(default=False, description="PIN authentication enabled")
    two_factor_enabled: bool = Field(default=False, description="Two-factor authentication enabled")


class UpdateProfileRequest(BaseModel):
    """Update user profile request"""
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    email: Optional[str] = Field(None, max_length=255)


class UserProfileResponse(BaseModel):
    """User profile response"""
    id: str
    email: str
    first_name: Optional[str]
    last_name: Optional[str]
    country_code: str
    hedera_account_id: Optional[str]
    wallet_type: Optional[str]
    created_at: datetime
    last_login: Optional[datetime]
    is_active: bool
    preferences: UserPreferences
    security: SecuritySettings
    
    class Config:
        from_attributes = True
