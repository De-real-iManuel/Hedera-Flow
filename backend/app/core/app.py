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
    """Run any missing schema migrations on startup.
    Each ALTER TABLE runs in its own transaction so one failure does not block others.
    psycopg2 aborts the whole transaction on any error, so batching DDL is unsafe.
    """
    from sqlalchemy import text
    from app.core.database import engine

    user_column_stmts = [
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS first_name VARCHAR(100)",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS last_name VARCHAR(100)",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS is_email_verified BOOLEAN NOT NULL DEFAULT FALSE",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS email_verification_token VARCHAR(255)",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS email_verification_expires TIMESTAMP WITH TIME ZONE",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS subsidy_eligible BOOLEAN NOT NULL DEFAULT FALSE",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS subsidy_type VARCHAR(50)",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS subsidy_verified_at TIMESTAMP WITH TIME ZONE",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS subsidy_expires_at TIMESTAMP WITH TIME ZONE",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS preferences JSONB",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS security_settings JSONB",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS evm_address VARCHAR(42)",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS kms_key_id VARCHAR(255)",
    ]
    for stmt in user_column_stmts:
        try:
            with engine.connect() as conn:
                conn.execute(text(stmt))
                conn.commit()
        except Exception as e:
            print(f"[WARN] Migration skipped ({stmt[:60]}): {e}")
    print("[OK] User schema migrations applied")

    # Unique constraint on utility_providers.provider_code
    try:
        with engine.connect() as conn:
            conn.execute(text("""
                DO $$ BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM pg_constraint
                        WHERE conname = 'utility_providers_provider_code_key'
                    ) THEN
                        ALTER TABLE utility_providers
                            ADD CONSTRAINT utility_providers_provider_code_key UNIQUE (provider_code);
                    END IF;
                END $$;
            """))
            conn.commit()
    except Exception as e:
        print(f"[WARN] Constraint migration skipped: {e}")

    seed_sql = """
    INSERT INTO utility_providers (provider_name, provider_code, country_code, state_province, service_areas, is_active, created_at)
    VALUES
      ('Eko Electricity Distribution Company',       'EKEDC',  'NG', 'Lagos',       ARRAY['Lagos Island','Victoria Island','Ikoyi','Lekki'], true, NOW()),
      ('Ikeja Electric',                             'IKEDC',  'NG', 'Lagos',       ARRAY['Ikeja','Agege','Ikorodu','Shomolu'], true, NOW()),
      ('Abuja Electricity Distribution Company',     'AEDC',   'NG', 'Abuja',       ARRAY['Abuja','Kogi','Niger','Nassarawa'], true, NOW()),
      ('Enugu Electricity Distribution Company',     'EEDC',   'NG', 'Enugu',       ARRAY['Enugu','Anambra','Imo','Abia','Ebonyi'], true, NOW()),
      ('Port Harcourt Electricity Distribution',     'PHED',   'NG', 'Rivers',      ARRAY['Port Harcourt','Bayelsa','Cross River','Akwa Ibom'], true, NOW()),
      ('Ibadan Electricity Distribution Company',    'IBEDC',  'NG', 'Oyo',         ARRAY['Ibadan','Ogun','Osun','Kwara','Oyo'], true, NOW()),
      ('Kano Electricity Distribution Company',      'KEDCO',  'NG', 'Kano',        ARRAY['Kano','Jigawa','Katsina'], true, NOW()),
      ('Kaduna Electricity Distribution Company',    'KAEDCO', 'NG', 'Kaduna',      ARRAY['Kaduna','Kebbi','Sokoto','Zamfara'], true, NOW()),
      ('Jos Electricity Distribution Company',       'JEDC',   'NG', 'Plateau',     ARRAY['Jos','Bauchi','Benue','Gombe'], true, NOW()),
      ('Benin Electricity Distribution Company',     'BEDC',   'NG', 'Edo',         ARRAY['Benin City','Delta','Ondo','Ekiti'], true, NOW()),
      ('Yola Electricity Distribution Company',      'YEDC',   'NG', 'Adamawa',     ARRAY['Yola','Taraba','Borno','Yobe'], true, NOW()),
      ('Iberdrola',                                  'IBE',    'ES', 'Madrid',      ARRAY['Madrid','Toledo','Guadalajara'], true, NOW()),
      ('Endesa',                                     'ENDESA', 'ES', 'Catalonia',   ARRAY['Barcelona','Tarragona','Lleida'], true, NOW()),
      ('Naturgy',                                    'NGAS',   'ES', 'Andalusia',   ARRAY['Seville','Malaga','Granada'], true, NOW()),
      ('Pacific Gas & Electric',                     'PGE',    'US', 'California',  ARRAY['San Francisco','Oakland','San Jose'], true, NOW()),
      ('Con Edison',                                 'CONED',  'US', 'New York',    ARRAY['New York City','Westchester'], true, NOW()),
      ('ComEd',                                      'COMED',  'US', 'Illinois',    ARRAY['Chicago','Rockford','Aurora'], true, NOW()),
      ('Florida Power & Light',                      'FPL',    'US', 'Florida',     ARRAY['Miami','Orlando','Tampa'], true, NOW()),
      ('Texas Electric',                             'TXELEC', 'US', 'Texas',       ARRAY['Houston','Dallas','Austin','San Antonio'], true, NOW()),
      ('Tata Power',                                 'TATA',   'IN', 'Maharashtra', ARRAY['Mumbai','Pune','Nashik'], true, NOW()),
      ('BSES Rajdhani',                              'BSESR',  'IN', 'Delhi',       ARRAY['South Delhi','West Delhi'], true, NOW()),
      ('BSES Yamuna',                                'BSESY',  'IN', 'Delhi',       ARRAY['East Delhi','Central Delhi'], true, NOW()),
      ('BESCOM',                                     'BESCOM', 'IN', 'Karnataka',   ARRAY['Bangalore','Mysore','Tumkur'], true, NOW()),
      ('TNEB',                                       'TNEB',   'IN', 'Tamil Nadu',  ARRAY['Chennai','Coimbatore','Madurai'], true, NOW()),
      ('CEMIG',                                      'CEMIG',  'BR', 'Minas Gerais',ARRAY['Belo Horizonte','Uberlandia','Contagem'], true, NOW()),
      ('ENEL Sao Paulo',                             'ENEL',   'BR', 'Sao Paulo',   ARRAY['Sao Paulo','Guarulhos','Campinas'], true, NOW()),
      ('COPEL',                                      'COPEL',  'BR', 'Parana',      ARRAY['Curitiba','Londrina','Maringa'], true, NOW()),
      ('CELPE',                                      'CELPE',  'BR', 'Pernambuco',  ARRAY['Recife','Caruaru','Petrolina'], true, NOW())
    ON CONFLICT DO NOTHING;
    """
    try:
        with engine.connect() as conn:
            conn.execute(text(seed_sql))
            conn.commit()
        print("[OK] Utility providers seeded")
    except Exception as e:
        print(f"[WARN] Provider seed skipped: {e}")

    TARIFF_ROWS = [
        ('NG', 'Eko Electricity Distribution Company',    'NGN',
         '{"type":"band_based","bands":[{"name":"A","hours_min":20,"price":225},{"name":"B","hours_min":16,"price":63},{"name":"C","hours_min":12,"price":50},{"name":"D","hours_min":8,"price":43},{"name":"E","hours_min":0,"price":40}]}',
         '{"vat":0.075}'),
        ('NG', 'Ikeja Electric',                          'NGN',
         '{"type":"band_based","bands":[{"name":"A","hours_min":20,"price":225},{"name":"B","hours_min":16,"price":63},{"name":"C","hours_min":12,"price":50},{"name":"D","hours_min":8,"price":43},{"name":"E","hours_min":0,"price":40}]}',
         '{"vat":0.075}'),
        ('NG', 'Abuja Electricity Distribution Company',  'NGN',
         '{"type":"band_based","bands":[{"name":"A","hours_min":20,"price":225},{"name":"B","hours_min":16,"price":63},{"name":"C","hours_min":12,"price":50},{"name":"D","hours_min":8,"price":43},{"name":"E","hours_min":0,"price":40}]}',
         '{"vat":0.075}'),
        ('NG', 'Enugu Electricity Distribution Company',  'NGN',
         '{"type":"band_based","bands":[{"name":"A","hours_min":20,"price":225},{"name":"B","hours_min":16,"price":63},{"name":"C","hours_min":12,"price":50},{"name":"D","hours_min":8,"price":43},{"name":"E","hours_min":0,"price":40}]}',
         '{"vat":0.075}'),
        ('NG', 'Port Harcourt Electricity Distribution',  'NGN',
         '{"type":"band_based","bands":[{"name":"A","hours_min":20,"price":225},{"name":"B","hours_min":16,"price":63},{"name":"C","hours_min":12,"price":50},{"name":"D","hours_min":8,"price":43},{"name":"E","hours_min":0,"price":40}]}',
         '{"vat":0.075}'),
        ('NG', 'Port Harcourt Electricity Distribution Company', 'NGN',
         '{"type":"band_based","bands":[{"name":"A","hours_min":20,"price":225},{"name":"B","hours_min":16,"price":63},{"name":"C","hours_min":12,"price":50},{"name":"D","hours_min":8,"price":43},{"name":"E","hours_min":0,"price":40}]}',
         '{"vat":0.075}'),
        ('NG', 'Ibadan Electricity Distribution Company', 'NGN',
         '{"type":"band_based","bands":[{"name":"A","hours_min":20,"price":225},{"name":"B","hours_min":16,"price":63},{"name":"C","hours_min":12,"price":50},{"name":"D","hours_min":8,"price":43},{"name":"E","hours_min":0,"price":40}]}',
         '{"vat":0.075}'),
        ('NG', 'Kano Electricity Distribution Company',   'NGN',
         '{"type":"band_based","bands":[{"name":"A","hours_min":20,"price":225},{"name":"B","hours_min":16,"price":63},{"name":"C","hours_min":12,"price":50},{"name":"D","hours_min":8,"price":43},{"name":"E","hours_min":0,"price":40}]}',
         '{"vat":0.075}'),
        ('NG', 'Kaduna Electricity Distribution Company', 'NGN',
         '{"type":"band_based","bands":[{"name":"A","hours_min":20,"price":225},{"name":"B","hours_min":16,"price":63},{"name":"C","hours_min":12,"price":50},{"name":"D","hours_min":8,"price":43},{"name":"E","hours_min":0,"price":40}]}',
         '{"vat":0.075}'),
        ('NG', 'Jos Electricity Distribution Company',    'NGN',
         '{"type":"band_based","bands":[{"name":"A","hours_min":20,"price":225},{"name":"B","hours_min":16,"price":63},{"name":"C","hours_min":12,"price":50},{"name":"D","hours_min":8,"price":43},{"name":"E","hours_min":0,"price":40}]}',
         '{"vat":0.075}'),
        ('NG', 'Benin Electricity Distribution Company',  'NGN',
         '{"type":"band_based","bands":[{"name":"A","hours_min":20,"price":225},{"name":"B","hours_min":16,"price":63},{"name":"C","hours_min":12,"price":50},{"name":"D","hours_min":8,"price":43},{"name":"E","hours_min":0,"price":40}]}',
         '{"vat":0.075}'),
        ('NG', 'Yola Electricity Distribution Company',   'NGN',
         '{"type":"band_based","bands":[{"name":"A","hours_min":20,"price":225},{"name":"B","hours_min":16,"price":63},{"name":"C","hours_min":12,"price":50},{"name":"D","hours_min":8,"price":43},{"name":"E","hours_min":0,"price":40}]}',
         '{"vat":0.075}'),
        ('ES', 'Iberdrola', 'EUR', '{"type":"flat","rate":0.18}', '{"vat":0.21}'),
        ('ES', 'Endesa',    'EUR', '{"type":"flat","rate":0.18}', '{"vat":0.21}'),
        ('ES', 'Naturgy',   'EUR', '{"type":"flat","rate":0.18}', '{"vat":0.21}'),
        ('US', 'Pacific Gas & Electric', 'USD', '{"type":"tiered","tiers":[{"limit":500,"price":0.12},{"limit":null,"price":0.18}]}', '{"tax":0.08}'),
        ('US', 'Con Edison',             'USD', '{"type":"tiered","tiers":[{"limit":500,"price":0.12},{"limit":null,"price":0.18}]}', '{"tax":0.08}'),
        ('US', 'ComEd',                  'USD', '{"type":"tiered","tiers":[{"limit":500,"price":0.12},{"limit":null,"price":0.18}]}', '{"tax":0.08}'),
        ('US', 'Florida Power & Light',  'USD', '{"type":"tiered","tiers":[{"limit":500,"price":0.12},{"limit":null,"price":0.18}]}', '{"tax":0.08}'),
        ('US', 'Texas Electric',         'USD', '{"type":"tiered","tiers":[{"limit":500,"price":0.12},{"limit":null,"price":0.18}]}', '{"tax":0.08}'),
        ('IN', 'Tata Power',    'INR', '{"type":"tiered","tiers":[{"limit":100,"price":3.5},{"limit":300,"price":5.5},{"limit":null,"price":7.5}]}', '{"tax":0.05}'),
        ('IN', 'BSES Rajdhani', 'INR', '{"type":"tiered","tiers":[{"limit":100,"price":3.5},{"limit":300,"price":5.5},{"limit":null,"price":7.5}]}', '{"tax":0.05}'),
        ('IN', 'BSES Yamuna',   'INR', '{"type":"tiered","tiers":[{"limit":100,"price":3.5},{"limit":300,"price":5.5},{"limit":null,"price":7.5}]}', '{"tax":0.05}'),
        ('IN', 'BESCOM',        'INR', '{"type":"tiered","tiers":[{"limit":100,"price":3.5},{"limit":300,"price":5.5},{"limit":null,"price":7.5}]}', '{"tax":0.05}'),
        ('IN', 'TNEB',          'INR', '{"type":"tiered","tiers":[{"limit":100,"price":3.5},{"limit":300,"price":5.5},{"limit":null,"price":7.5}]}', '{"tax":0.05}'),
        ('BR', 'CEMIG',          'BRL', '{"type":"tiered","tiers":[{"limit":200,"price":0.65},{"limit":null,"price":0.85}]}', '{"icms":0.20}'),
        ('BR', 'ENEL Sao Paulo', 'BRL', '{"type":"tiered","tiers":[{"limit":200,"price":0.65},{"limit":null,"price":0.85}]}', '{"icms":0.20}'),
        ('BR', 'COPEL',          'BRL', '{"type":"tiered","tiers":[{"limit":200,"price":0.65},{"limit":null,"price":0.85}]}', '{"icms":0.20}'),
        ('BR', 'CELPE',          'BRL', '{"type":"tiered","tiers":[{"limit":200,"price":0.65},{"limit":null,"price":0.85}]}', '{"icms":0.20}'),
    ]

    try:
        inserted = 0
        with engine.connect() as conn:
            for (cc, provider, currency, rate_json, taxes_json) in TARIFF_ROWS:
                exists = conn.execute(text(
                    "SELECT 1 FROM tariffs WHERE country_code=:cc AND utility_provider=:p AND is_active=true"
                ), {"cc": cc, "p": provider}).fetchone()
                if exists:
                    continue
                conn.execute(text(
                    "INSERT INTO tariffs (country_code, utility_provider, currency, rate_structure, taxes_and_fees, valid_from, is_active) "
                    "VALUES (:cc, :provider, :currency, cast(:rate AS jsonb), cast(:taxes AS jsonb), '2024-01-01', true)"
                ), {"cc": cc, "provider": provider, "currency": currency, "rate": rate_json, "taxes": taxes_json})
                inserted += 1
            conn.commit()
        print(f"[OK] Tariffs seeded ({inserted} new rows)")
    except Exception as e:
        print(f"[WARN] Tariff seed skipped: {e}")

    try:
        with engine.connect() as conn:
            conn.execute(text("""
                UPDATE meters m
                SET utility_provider = up.provider_name
                FROM utility_providers up
                WHERE m.utility_provider_id = up.id
                  AND m.utility_provider IS DISTINCT FROM up.provider_name
            """))
            conn.commit()
        print("[OK] Meter utility_provider names backfilled")
    except Exception as e:
        print(f"[WARN] Meter backfill skipped: {e}")


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
    """Application factory"""
    app = FastAPI(
        title="Hedera Flow API",
        description="Blockchain-powered utility verification platform",
        version="1.0.0",
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
        lifespan=lifespan
    )

    setup_exception_handlers(app)
    configure_cors(app)
    setup_middleware(app)
    setup_rate_limiting(app)
    app.include_router(api_router, prefix="/api")

    @app.get("/")
    async def root():
        return {
            "status": "ok",
            "service": "Hedera Flow API",
            "version": "1.0.0",
            "environment": settings.environment
        }

    return app


def configure_cors(app: FastAPI) -> None:
    """Configure CORS middleware for cross-origin requests (Vercel -> Railway)"""
    allowed_origins = [origin.strip() for origin in settings.cors_origins.split(",") if origin.strip()]

    vercel_origins = [
        "https://hedera-flow-ivory.vercel.app",
        "https://hederaflow.ai",
        "https://www.hederaflow.ai",
    ]
    allowed_origins = list(set(allowed_origins + vercel_origins))

    if settings.environment == "production" or os.getenv('RAILWAY_ENVIRONMENT'):
        production_origins = [
            "https://hederaflow.com",
            "https://www.hederaflow.com",
        ]
        allowed_origins = list(set(allowed_origins + production_origins))

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
        allow_origin_regex=r"https://.*\.vercel\.app",
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
