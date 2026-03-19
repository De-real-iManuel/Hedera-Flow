"""
Configuration management using Pydantic Settings
"""
from pydantic_settings import BaseSettings
from typing import Optional
import logging
import os

# Suppress verbose Java/Jnius logging early
logging.getLogger('kivy.jnius.reflect').setLevel(logging.ERROR)
logging.getLogger('kivy.jnius').setLevel(logging.ERROR)
logging.getLogger('jnius').setLevel(logging.ERROR)

# Set environment variables to suppress Java logging
os.environ.setdefault('JNIUS_DEBUG', '0')
os.environ.setdefault('KIVY_LOG_LEVEL', 'error')


class Settings(BaseSettings):
    """Application settings"""
    
    # Application
    environment: str = "development"
    debug: bool = True
    
    # Database
    database_url: Optional[str] = None
    db_pool_size: int = 5
    db_max_overflow: int = 10
    db_pool_timeout: int = 30
    
    # Supabase (Optional - for future features)
    supabase_url: Optional[str] = None
    supabase_anon_key: Optional[str] = None
    supabase_service_role_key: Optional[str] = None
    
    # Redis (Upstash or local)
    redis_url: Optional[str] = None
    
    # JWT
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_expiration_days: int = 30
    
    # Hedera
    hedera_network: str = "testnet"
    hedera_operator_id: Optional[str] = None
    hedera_operator_key: Optional[str] = None
    hedera_treasury_id: Optional[str] = None
    hedera_treasury_key: Optional[str] = None
    
    # HCS Topics
    hcs_topic_eu: Optional[str] = None
    hcs_topic_us: Optional[str] = None
    hcs_topic_asia: Optional[str] = None
    hcs_topic_sa: Optional[str] = None
    hcs_topic_africa: Optional[str] = None
    
    # Google Cloud Vision
    google_application_credentials: Optional[str] = None
    
    # IPFS
    ipfs_api_url: str = "https://api.pinata.cloud"
    pinata_api_key: Optional[str] = None
    pinata_secret_key: Optional[str] = None
    
    # Exchange Rate APIs
    coingecko_api_key: Optional[str] = None
    coinmarketcap_api_key: Optional[str] = None
    
    # Email
    sendgrid_api_key: Optional[str] = None
    from_email: str = "noreply@hederaflow.com"
    
    # Rate Limiting
    rate_limit_per_minute: int = 100
    
    # Fraud Detection
    fraud_detection_enabled: bool = True
    fraud_score_threshold: float = 0.70
    
    # CORS Configuration
    # Includes localhost and common local network IPs for mobile testing
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173,http://127.0.0.1:5173,http://localhost:8080,http://127.0.0.1:8080,http://192.168.1.100:5173,http://192.168.1.100:8080,http://10.0.0.100:5173,http://10.0.0.100:8080,https://hederaflow.com,https://www.hederaflow.com,https://hedera-flow.vercel.app,https://hedera-flow-frontend.vercel.app,https://hedera-flow-git-main.vercel.app"
    cors_allow_credentials: bool = True
    cors_allow_methods: str = "*"
    cors_allow_headers: str = "*"
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "allow"  # Allow extra fields from .env


# Global settings instance
settings = Settings()

# Handle Railway's DATABASE_URL environment variable
# Railway provides DATABASE_URL directly; also fix postgres:// → postgresql://
_db_url = os.getenv('DATABASE_URL') or settings.database_url
if _db_url:
    if _db_url.startswith("postgres://"):
        _db_url = _db_url.replace("postgres://", "postgresql://", 1)
    settings.database_url = _db_url
    print(f"Database URL configured: {_db_url[:40]}...")
else:
    print("WARNING: DATABASE_URL not set — database operations will fail")

# Set Google Cloud credentials environment variable if configured
if settings.google_application_credentials:
    import os
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = settings.google_application_credentials
    print(f"Set GOOGLE_APPLICATION_CREDENTIALS to: {settings.google_application_credentials}")
else:
    print("Warning: GOOGLE_APPLICATION_CREDENTIALS not configured in .env file")
