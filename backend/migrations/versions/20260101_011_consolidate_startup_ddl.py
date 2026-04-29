"""Consolidate all inline startup DDL and seed data into Alembic

Revision ID: 011_consolidate_startup_ddl
Revises: 010_smart_meter_kms
Create Date: 2026-01-01 00:00:00.000000

Replaces the run_schema_migrations() function that was embedded in app.py.
After this migration runs, that function is removed from app.py entirely.
"""
from alembic import op
import sqlalchemy as sa

revision = '011_consolidate_startup_ddl'
down_revision = '010_smart_meter_kms'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ------------------------------------------------------------------ #
    # 1. User columns added post-initial-schema                           #
    # ------------------------------------------------------------------ #
    user_columns = [
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
    for stmt in user_columns:
        op.execute(stmt)

    # ------------------------------------------------------------------ #
    # 2. Unique constraint on utility_providers.provider_code             #
    # ------------------------------------------------------------------ #
    op.execute("""
        DO $$ BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint
                WHERE conname = 'utility_providers_provider_code_key'
            ) THEN
                ALTER TABLE utility_providers
                    ADD CONSTRAINT utility_providers_provider_code_key UNIQUE (provider_code);
            END IF;
        END $$;
    """)

    # ------------------------------------------------------------------ #
    # 3. Seed utility providers (idempotent via ON CONFLICT DO NOTHING)   #
    # ------------------------------------------------------------------ #
    op.execute("""
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
    """)

    # ------------------------------------------------------------------ #
    # 4. Seed tariffs (idempotent — skip if already present)              #
    # ------------------------------------------------------------------ #
    tariff_rows = [
        ('NG', 'Eko Electricity Distribution Company',    'NGN', '{"type":"band_based","bands":[{"name":"A","hours_min":20,"price":225},{"name":"B","hours_min":16,"price":63},{"name":"C","hours_min":12,"price":50},{"name":"D","hours_min":8,"price":43},{"name":"E","hours_min":0,"price":40}]}', '{"vat":0.075}'),
        ('NG', 'Ikeja Electric',                          'NGN', '{"type":"band_based","bands":[{"name":"A","hours_min":20,"price":225},{"name":"B","hours_min":16,"price":63},{"name":"C","hours_min":12,"price":50},{"name":"D","hours_min":8,"price":43},{"name":"E","hours_min":0,"price":40}]}', '{"vat":0.075}'),
        ('NG', 'Abuja Electricity Distribution Company',  'NGN', '{"type":"band_based","bands":[{"name":"A","hours_min":20,"price":225},{"name":"B","hours_min":16,"price":63},{"name":"C","hours_min":12,"price":50},{"name":"D","hours_min":8,"price":43},{"name":"E","hours_min":0,"price":40}]}', '{"vat":0.075}'),
        ('NG', 'Enugu Electricity Distribution Company',  'NGN', '{"type":"band_based","bands":[{"name":"A","hours_min":20,"price":225},{"name":"B","hours_min":16,"price":63},{"name":"C","hours_min":12,"price":50},{"name":"D","hours_min":8,"price":43},{"name":"E","hours_min":0,"price":40}]}', '{"vat":0.075}'),
        ('NG', 'Port Harcourt Electricity Distribution',  'NGN', '{"type":"band_based","bands":[{"name":"A","hours_min":20,"price":225},{"name":"B","hours_min":16,"price":63},{"name":"C","hours_min":12,"price":50},{"name":"D","hours_min":8,"price":43},{"name":"E","hours_min":0,"price":40}]}', '{"vat":0.075}'),
        ('NG', 'Ibadan Electricity Distribution Company', 'NGN', '{"type":"band_based","bands":[{"name":"A","hours_min":20,"price":225},{"name":"B","hours_min":16,"price":63},{"name":"C","hours_min":12,"price":50},{"name":"D","hours_min":8,"price":43},{"name":"E","hours_min":0,"price":40}]}', '{"vat":0.075}'),
        ('NG', 'Kano Electricity Distribution Company',   'NGN', '{"type":"band_based","bands":[{"name":"A","hours_min":20,"price":225},{"name":"B","hours_min":16,"price":63},{"name":"C","hours_min":12,"price":50},{"name":"D","hours_min":8,"price":43},{"name":"E","hours_min":0,"price":40}]}', '{"vat":0.075}'),
        ('NG', 'Kaduna Electricity Distribution Company', 'NGN', '{"type":"band_based","bands":[{"name":"A","hours_min":20,"price":225},{"name":"B","hours_min":16,"price":63},{"name":"C","hours_min":12,"price":50},{"name":"D","hours_min":8,"price":43},{"name":"E","hours_min":0,"price":40}]}', '{"vat":0.075}'),
        ('NG', 'Jos Electricity Distribution Company',    'NGN', '{"type":"band_based","bands":[{"name":"A","hours_min":20,"price":225},{"name":"B","hours_min":16,"price":63},{"name":"C","hours_min":12,"price":50},{"name":"D","hours_min":8,"price":43},{"name":"E","hours_min":0,"price":40}]}', '{"vat":0.075}'),
        ('NG', 'Benin Electricity Distribution Company',  'NGN', '{"type":"band_based","bands":[{"name":"A","hours_min":20,"price":225},{"name":"B","hours_min":16,"price":63},{"name":"C","hours_min":12,"price":50},{"name":"D","hours_min":8,"price":43},{"name":"E","hours_min":0,"price":40}]}', '{"vat":0.075}'),
        ('NG', 'Yola Electricity Distribution Company',   'NGN', '{"type":"band_based","bands":[{"name":"A","hours_min":20,"price":225},{"name":"B","hours_min":16,"price":63},{"name":"C","hours_min":12,"price":50},{"name":"D","hours_min":8,"price":43},{"name":"E","hours_min":0,"price":40}]}', '{"vat":0.075}'),
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
    conn = op.get_bind()
    for (cc, provider, currency, rate_json, taxes_json) in tariff_rows:
        exists = conn.execute(
            sa.text(
                "SELECT 1 FROM tariffs WHERE country_code=:cc AND utility_provider=:p AND is_active=true"
            ),
            {"cc": cc, "p": provider}
        ).fetchone()
        if not exists:
            conn.execute(
                sa.text(
                    "INSERT INTO tariffs (country_code, utility_provider, currency, rate_structure, "
                    "taxes_and_fees, valid_from, is_active) "
                    "VALUES (:cc, :provider, :currency, cast(:rate AS jsonb), cast(:taxes AS jsonb), '2024-01-01', true)"
                ),
                {"cc": cc, "provider": provider, "currency": currency,
                 "rate": rate_json, "taxes": taxes_json}
            )

    # ------------------------------------------------------------------ #
    # 5. Backfill meter utility_provider name from utility_providers table #
    # ------------------------------------------------------------------ #
    op.execute("""
        UPDATE meters m
        SET utility_provider = up.provider_name
        FROM utility_providers up
        WHERE m.utility_provider_id = up.id
          AND m.utility_provider IS DISTINCT FROM up.provider_name
    """)


def downgrade() -> None:
    # Seed data and column additions are intentionally not reversed —
    # dropping columns with data is destructive and should be a deliberate
    # manual operation, not an automatic downgrade.
    pass
