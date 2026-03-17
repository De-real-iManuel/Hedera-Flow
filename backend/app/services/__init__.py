"""
Business Logic Services Package
Lazy imports to prevent SDK import failures from crashing the entire app.
"""

def get_hedera_service():
    from app.services.hedera_service import get_hedera_service as _get
    return _get()

def get_ocr_service():
    from app.services.ocr_service import get_ocr_service as _get
    return _get()

def get_fraud_detection_service():
    from app.services.fraud_detection_service import get_fraud_detection_service as _get
    return _get()

def get_hbar_price(*args, **kwargs):
    from app.services.exchange_rate_service import get_hbar_price as _get
    return _get(*args, **kwargs)

# Lazy class references
class HederaService:
    def __new__(cls, *args, **kwargs):
        from app.services.hedera_service import HederaService as _Real
        return _Real(*args, **kwargs)

class OCRService:
    def __new__(cls, *args, **kwargs):
        from app.services.ocr_service import OCRService as _Real
        return _Real(*args, **kwargs)

class FraudDetectionService:
    def __new__(cls, *args, **kwargs):
        from app.services.fraud_detection_service import FraudDetectionService as _Real
        return _Real(*args, **kwargs)

class ExchangeRateService:
    def __new__(cls, *args, **kwargs):
        from app.services.exchange_rate_service import ExchangeRateService as _Real
        return _Real(*args, **kwargs)

__all__ = [
    "HederaService", "get_hedera_service",
    "OCRService", "get_ocr_service",
    "FraudDetectionService", "get_fraud_detection_service",
    "ExchangeRateService", "get_hbar_price",
]
