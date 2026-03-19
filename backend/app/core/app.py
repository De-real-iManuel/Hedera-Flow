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


def run_schema_migrations():
    """Run any missing schema migrations on startup."""
    from sqlalchemy import text
    from app.core.database import engine

    schema_sql = """
    ALTER TABLE users
        ADD COLUMN IF NOT EXISTS first_name VARCHAR(100),
        ADD COLUMN IF NOT EXISTS last_name VARCHAR(100),
        ADD COLUMN IF NOT EXISTS is_email_verified BOOLEAN NOT NULL DEFAULT FALSE,
        ADD COLUMN IF NOT EXISTS email_verification_token VARCHAR(255),
        ADD COLUMN IF NOT EXISTS email_verification_expires TIMESTAMP WITH TIME ZONE,
        ADD COLUMN IF NOT EXISTS subsidy_eligible BOOLEAN NOT NULL DEFAULT FALSE,
        ADD COLUMN IF NOT EXISTS subsidy_type VARCHAR(50),
        ADD COLUMN IF NOT EXISTS subsidy_verified_at TIMESTAMP WITH TIME ZONE,
        ADD COLUMN IF NOT EXISTS subsidy_expires_at TIMESTAMP WITH TIME ZONE,
        ADD COLUMN IF NOT EXISTS preferences JSONB,
        ADD COLUMN IF NOT EXISTS security_settings JSONB;

    -- Add unique constraint on provider_code so ON CONFLICT works
    DO $$ BEGIN
        IF NOT EXISTS (
            SELECT 1 FROM pg_constraint WHERE conname = 'utility_providers_provider_code_key'
        ) THEN
            ALTER TABLE utility_providers ADD CONSTRAINT utility_providers_provider_code_key UNIQUE (provider_code);
        END IF;
    END $$;
    """

    seed_sql = """
    INSERT INTO utility_providers (provider_name, provider_code, country_code, state_province, service_areas, is_active, created_at)
    VALUES
      -- Nigeria DISCOs
      ('Eko Electricity Distribution Company',       'EKEDC',  'NG', 'Lagos',          ARRAY['Lagos Island','Victoria Island','Ikoyi','Lekki'], true, NOW()),
      ('Ikeja Electric',                             'IKEDC',  'NG', 'Lagos',          ARRAY['Ikeja','Agege','Ikorodu','Shomolu'], true, NOW()),
      ('Abuja Electricity Distribution Company',     'AEDC',   'NG', 'Abuja',          ARRAY['Abuja','Kogi','Niger','Nassarawa'], true, NOW()),
      ('Enugu Electricity Distribution Company',     'EEDC',   'NG', 'Enugu',          ARRAY['Enugu','Anambra','Imo','Abia','Ebonyi'], true, NOW()),
      ('Port Harcourt Electricity Distribution',     'PHED',   'NG', 'Rivers',         ARRAY['Port Harcourt','Bayelsa','Cross River','Akwa Ibom'], true, NOW()),
      ('Ibadan Electricity Distribution Company',    'IBEDC',  'NG', 'Oyo',            ARRAY['Ibadan','Ogun','Osun','Kwara','Oyo'], true, NOW()),
      ('Kano Electricity Distribution Company',      'KEDCO',  'NG', 'Kano',           ARRAY['Kano','Jigawa','Katsina'], true, NOW()),
      ('Kaduna Electricity Distribution Company',    'KAEDCO', 'NG', 'Kaduna',         ARRAY['Kaduna','Kebbi','Sokoto','Zamfara'], true, NOW()),
      ('Jos Electricity Distribution Company',       'JEDC',   'NG', 'Plateau',        ARRAY['Jos','Bauchi','Benue','Gombe'], true, NOW()),
      ('Benin Electricity Distribution Company',     'BEDC',   'NG', 'Edo',            ARRAY['Benin City','Delta','Ondo','Ekiti'], true, NOW()),
      ('Yola Electricity Distribution Company',      'YEDC',   'NG', 'Adamawa',        ARRAY['Yola','Taraba','Borno','Yobe'], true, NOW()),
      -- Spain
      ('Iberdrola',                                  'IBE',    'ES', 'Madrid',         ARRAY['Madrid','Toledo','Guadalajara'], true, NOW()),
      ('Endesa',                                     'ENDESA', 'ES', 'Catalonia',      ARRAY['Barcelona','Tarragona','Lleida'], true, NOW()),
      ('Naturgy',                                    'NGAS',   'ES', 'Andalusia',      ARRAY['Seville','Malaga','Granada'], true, NOW()),
      -- USA
      ('Pacific Gas & Electric',                     'PGE',    'US', 'California',     ARRAY['San Francisco','Oakland','San Jose'], true, NOW()),
      ('Con Edison',                                 'CONED',  'US', 'New York',       ARRAY['New York City','Westchester'], true, NOW()),
      ('ComEd',                                      'COMED',  'US', 'Illinois',       ARRAY['Chicago','Rockford','Aurora'], true, NOW()),
      ('Florida Power & Light',                      'FPL',    'US', 'Florida',        ARRAY['Miami','Orlando','Tampa'], true, NOW()),
      ('Texas Electric',                             'TXELEC', 'US', 'Texas',          ARRAY['Houston','Dallas','Austin','San Antonio'], true, NOW()),
      -- India
      ('Tata Power',                                 'TATA',   'IN', 'Maharashtra',    ARRAY['Mumbai','Pune','Nashik'], true, NOW()),
      ('BSES Rajdhani',                              'BSESR',  'IN', 'Delhi',          ARRAY['South Delhi','West Delhi'], true, NOW()),
      ('BSES Yamuna',                                'BSESY',  'IN', 'Delhi',          ARRAY['East Delhi','Central Delhi'], true, NOW()),
      ('BESCOM',                                     'BESCOM', 'IN', 'Karnataka',      ARRAY['Bangalore','Mysore','Tumkur'], true, NOW()),
      ('TNEB',                                       'TNEB',   'IN', 'Tamil Nadu',     ARRAY['Chennai','Coimbatore','Madurai'], true, NOW()),
      -- Brazil
      ('CEMIG',                                      'CEMIG',  'BR', 'Minas Gerais',   ARRAY['Belo Horizonte','Uberlandia','Contagem'], true, NOW()),
      ('ENEL São Paulo',                             'ENEL',   'BR', 'São Paulo',      ARRAY['São Paulo','Guarulhos','Campinas'], true, NOW()),
      ('COPEL',                                      'COPEL',  'BR', 'Paraná',         ARRAY['Curitiba','Londrina','Maringá'], true, NOW()),
      ('CELPE',                                      'CELPE',  'BR', 'Pernambuco',     ARRAY['Recife','Caruaru','Petrolina'], true, NOW())
    ON CONFLICT DO NOTHING;
    """

    try:
        with engine.connect() as conn:
            conn.execute(text(schema_sql))
            conn.execute(text(seed_sql))
            conn.commit()
        print("[OK] Schema migrations and seed data applied")
    except Exception as e:
        print(f"[WARN] Migration/seed skipped: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    print("Starting Hedera Flow API...")
    print(f"Environment: {settings.environment}")
    print(f"Network: {settings.hedera_network}")

    # Run schema migrations before anything else
    run_schema_migrations()

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

    yield

    # Shutdown
    print("Shutting down Hedera Flow API...")
    close_db()
    print("Database connection pool closed")


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

