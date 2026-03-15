"""
Pydantic Schemas Package

This package contains all Pydantic models for API request/response validation.
Organized by domain for better maintainability.
"""

# Authentication schemas
from .auth import (
    CountryCode,
    WalletType,
    RegisterRequest,
    LoginRequest,
    WalletConnectRequest,
    UserResponse,
    AuthResponse,
    TokenPayload,
)

# Meter schemas
from .meters import (
    MeterType,
    BandClassification,
    MeterCreateRequest,
    MeterUpdateRequest,
    MeterResponse,
    MeterListResponse,
)

# Verification schemas
from .verifications import (
    VerificationStatus,
    OCREngine,
    VerificationCreateRequest,
    FraudDetectionResult,
    VerificationResponse,
    VerificationListResponse,
    VerificationSummary,
)

# Bill schemas
from .bills import (
    BillStatus,
    Currency,
    BillBreakdown,
    BillResponse,
    BillListResponse,
    BillSummary,
)

# Payment schemas
from .payments import (
    PaymentPrepareRequest,
    PaymentConfirmRequest,
    TransactionDetails,
    ExchangeRateInfo,
    PaymentPrepareResponse,
    PaymentReceipt,
    PaymentConfirmResponse,
    ExchangeRateResponse,
    InsufficientBalanceResponse,
)

# Dispute schemas
from .disputes import (
    DisputeReason,
    DisputeStatus,
    DisputeCreateRequest,
    DisputeResolveRequest,
    DisputeResponse,
    DisputeListResponse,
    DisputeSummary,
    DisputeResolveResponse,
)

# Tariff schemas
from .tariffs import (
    RateStructureType,
    TariffCreateRequest,
    TariffUpdateRequest,
    TariffResponse,
    TariffListResponse,
    TariffSummary,
    FlatRateStructure,
    TieredRateStructure,
    TimeOfUseRateStructure,
    BandBasedRateStructure,
)

# Utility provider schemas
from .utility_providers import (
    UtilityProviderCreateRequest,
    UtilityProviderUpdateRequest,
    UtilityProviderResponse,
    UtilityProviderListResponse,
    UtilityProviderSummary,
)

# Common schemas
from .common import (
    ErrorResponse,
    SuccessResponse,
    PaginationParams,
    PaginatedResponse,
    HealthCheckResponse,
    ValidationErrorDetail,
    ValidationErrorResponse,
)

# Hedera blockchain schemas
from .hedera import (
    HCSMessageType,
    HCSTopicRegion,
    VerificationLogMessage,
    PaymentLogMessage,
    DisputeCreatedLogMessage,
    DisputeResolvedLogMessage,
    HederaAccountInfo,
    HederaTransactionInfo,
    HCSMessageInfo,
    MirrorNodeQueryResponse,
    SmartContractCallRequest,
    SmartContractCallResponse,
)

__all__ = [
    # Auth
    "CountryCode",
    "WalletType",
    "RegisterRequest",
    "LoginRequest",
    "WalletConnectRequest",
    "UserResponse",
    "AuthResponse",
    "TokenPayload",
    # Meters
    "MeterType",
    "BandClassification",
    "MeterCreateRequest",
    "MeterUpdateRequest",
    "MeterResponse",
    "MeterListResponse",
    # Verifications
    "VerificationStatus",
    "OCREngine",
    "VerificationCreateRequest",
    "FraudDetectionResult",
    "VerificationResponse",
    "VerificationListResponse",
    "VerificationSummary",
    # Bills
    "BillStatus",
    "Currency",
    "BillBreakdown",
    "BillResponse",
    "BillListResponse",
    "BillSummary",
    # Payments
    "PaymentPrepareRequest",
    "PaymentConfirmRequest",
    "TransactionDetails",
    "ExchangeRateInfo",
    "PaymentPrepareResponse",
    "PaymentReceipt",
    "PaymentConfirmResponse",
    "ExchangeRateResponse",
    "InsufficientBalanceResponse",
    # Disputes
    "DisputeReason",
    "DisputeStatus",
    "DisputeCreateRequest",
    "DisputeResolveRequest",
    "DisputeResponse",
    "DisputeListResponse",
    "DisputeSummary",
    "DisputeResolveResponse",
    # Tariffs
    "RateStructureType",
    "TariffCreateRequest",
    "TariffUpdateRequest",
    "TariffResponse",
    "TariffListResponse",
    "TariffSummary",
    "FlatRateStructure",
    "TieredRateStructure",
    "TimeOfUseRateStructure",
    "BandBasedRateStructure",
    # Utility Providers
    "UtilityProviderCreateRequest",
    "UtilityProviderUpdateRequest",
    "UtilityProviderResponse",
    "UtilityProviderListResponse",
    "UtilityProviderSummary",
    # Common
    "ErrorResponse",
    "SuccessResponse",
    "PaginationParams",
    "PaginatedResponse",
    "HealthCheckResponse",
    "ValidationErrorDetail",
    "ValidationErrorResponse",
    # Hedera
    "HCSMessageType",
    "HCSTopicRegion",
    "VerificationLogMessage",
    "PaymentLogMessage",
    "DisputeCreatedLogMessage",
    "DisputeResolvedLogMessage",
    "HederaAccountInfo",
    "HederaTransactionInfo",
    "HCSMessageInfo",
    "MirrorNodeQueryResponse",
    "SmartContractCallRequest",
    "SmartContractCallResponse",
]
