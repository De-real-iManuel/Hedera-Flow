"""
Configuration management using Pydantic Settings
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings"""
    
    # Application
    environment: str = "development"
    debug: bool = True
    
    # Database (Supabase PostgreSQL)
    database_url: str
    db_pool_size: int = 20
    db_max_overflow: int = 10
    db_pool_timeout: int = 30
    
    # Supabase (Optional - for future features)
    supabase_url: Optional[str] = None
    supabase_anon_key: Optional[str] = None
    supabase_service_role_key: Optional[str] = None
    
    # Redis (Upstash or local)
    redis_url: str
    
    # JWT
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_expiration_days: int = 30
    
    # Hedera
    hedera_network: str = "testnet"
    hedera_operator_id: str
    hedera_operator_key: str
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
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173,http://127.0.0.1:5173,http://localhost:8080,http://127.0.0.1:8080"
    cors_allow_credentials: bool = True
    cors_allow_methods: str = "*"
    cors_allow_headers: str = "*"
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "allow"  # Allow extra fields from .env


# Global settings instance
settings = Settings()
