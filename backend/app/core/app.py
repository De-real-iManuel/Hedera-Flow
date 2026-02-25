"""
FastAPI Application Factory
Creates and configures the FastAPI application instance
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

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
    print("🚀 Starting Hedera Flow API...")
    print(f"📍 Environment: {settings.environment}")
    print(f"🌐 Network: {settings.hedera_network}")
    
    # Initialize database connection pool
    print("💾 Initializing database connection pool...")
    db_healthy = check_db_connection()
    if db_healthy:
        print("✅ Database connection pool initialized successfully")
        stats = get_db_stats()
        print(f"   - Pool size: {stats['pool_size']}")
        print(f"   - Total connections: {stats['total_connections']}")
    else:
        print("❌ Database connection failed - check DATABASE_URL")
    
    # TODO: Initialize Redis connection
    # TODO: Verify Hedera network connectivity
    
    yield
    
    # Shutdown
    print("🛑 Shutting down Hedera Flow API...")
    
    # Close database connections
    print("💾 Closing database connection pool...")
    close_db()
    print("✅ Database connection pool closed")
    
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
    """
    Configure CORS middleware
    Allows cross-origin requests from frontend applications
    
    Security considerations:
    - Production: Only allow specific domains (hederaflow.com)
    - Development: Allow localhost for Next.js dev server
    - Credentials: Enabled for JWT cookie support
    - Methods: All HTTP methods allowed for REST API
    - Headers: All headers allowed for flexibility
    """
    # Parse allowed origins from environment variable (comma-separated)
    allowed_origins = [origin.strip() for origin in settings.cors_origins.split(",")]
    
    # Add production domains if in production environment
    if settings.environment == "production":
        production_origins = [
            "https://hederaflow.com",
            "https://www.hederaflow.com",
        ]
        # Merge with any custom origins from env
        allowed_origins = list(set(allowed_origins + production_origins))
    
    # Parse allowed methods
    if settings.cors_allow_methods == "*":
        allowed_methods = ["*"]
    else:
        allowed_methods = [method.strip() for method in settings.cors_allow_methods.split(",")]
    
    # Parse allowed headers
    if settings.cors_allow_headers == "*":
        allowed_headers = ["*"]
    else:
        allowed_headers = [header.strip() for header in settings.cors_allow_headers.split(",")]
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=settings.cors_allow_credentials,
        allow_methods=allowed_methods,
        allow_headers=allowed_headers,
        expose_headers=["Content-Length", "Content-Type", "Authorization"],
        max_age=600,  # Cache preflight requests for 10 minutes
    )
    
    # Log CORS configuration in debug mode
    if settings.debug:
        print(f"🔒 CORS configured:")
        print(f"   - Allowed origins: {allowed_origins}")
        print(f"   - Allow credentials: {settings.cors_allow_credentials}")
        print(f"   - Allowed methods: {allowed_methods}")
        print(f"   - Allowed headers: {allowed_headers}")

