"""
FastAPI Application Factory
Creates and configures the FastAPI application instance
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os

from config import settings
from app.core.exceptions import setup_exception_handlers
from app.core.middleware import setup_middleware
from app.core.rate_limit import setup_rate_limiting
from app.core.database import close_db, check_db_connection, get_db_stats
from app.api.routes import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan events
    Handles startup and shutdown tasks
    """
    # Startup
    print("Starting Hedera Flow API...")
    print(f"Environment: {settings.environment}")
    print(f"Network: {settings.hedera_network}")
    
    # Initialize database connection pool
    print("Initializing database connection pool...")
    db_healthy = check_db_connection()
    if db_healthy:
        print("[OK] Database connection pool initialized successfully")
        stats = get_db_stats()
        print(f"   - Pool size: {stats['pool_size']}")
        print(f"   - Total connections: {stats['total_connections']}")
    else:
        print("[ERROR] Database connection failed - check DATABASE_URL")
    
    # TODO: Initialize Redis connection
    # TODO: Verify Hedera network connectivity
    
    yield
    
    # Shutdown
    print("Shutting down Hedera Flow API...")
    
    # Close database connections
    print("Closing database connection pool...")
    close_db()
    print("Database connection pool closed")
    
    # TODO: Close Redis connections


def create_app() -> FastAPI:
    """
    Application factory
    Creates and configures the FastAPI application
    """
    app = FastAPI(
        title="Hedera Flow API",
        description="Blockchain-powered utility verification platform",
        version="1.0.0",
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
        lifespan=lifespan
    )
    
    # Setup exception handlers (must be first)
    setup_exception_handlers(app)
    
    # Configure CORS (must be before other middleware)
    configure_cors(app)
    
    # Setup custom middleware (error handling, security headers, request logging)
    setup_middleware(app)
    
    # Setup rate limiting
    setup_rate_limiting(app)
    
    # Include API routes
    app.include_router(api_router, prefix="/api")
    
    # Root health check
    @app.get("/")
    async def root():
        """Root endpoint - API status"""
        return {
            "status": "ok",
            "service": "Hedera Flow API",
            "version": "1.0.0",
            "environment": settings.environment
        }
    
    return app


def configure_cors(app: FastAPI) -> None:
    """Configure CORS middleware for cross-origin requests (Vercel → Railway)"""
    # Parse allowed origins from environment variable (comma-separated)
    allowed_origins = [origin.strip() for origin in settings.cors_origins.split(",") if origin.strip()]
    
    # Always include these Vercel origins explicitly
    vercel_origins = [
        "https://hedera-flow-ivory.vercel.app",
        "https://hederaflow.ai",
        "https://www.hederaflow.ai",
    ]
    allowed_origins = list(set(allowed_origins + vercel_origins))
    
    # Add production domains
    if settings.environment == "production" or os.getenv('RAILWAY_ENVIRONMENT'):
        production_origins = [
            "https://hederaflow.com",
            "https://www.hederaflow.com",
        ]
        allowed_origins = list(set(allowed_origins + production_origins))
    
    # In development, add localhost origins
    if settings.environment == "development" and not os.getenv('RAILWAY_ENVIRONMENT'):
        development_origins = [
            "http://localhost:3000",
            "http://localhost:5173",
            "http://localhost:8080",
            "http://localhost:8081",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:5173",
            "http://127.0.0.1:8080",
        ]
        allowed_origins = list(set(development_origins + allowed_origins))
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_origin_regex=r"https://.*\.vercel\.app",  # all Vercel preview URLs
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["Content-Length", "Content-Type", "Authorization"],
        max_age=600,
    )
    
    if settings.debug:
        print(f"CORS configured with origins: {allowed_origins}")


# Create the app instance
app = create_app()

