"""
Direct tariff seeding script — run via: railway run python seed_tariffs_direct.py
Inserts tariffs using WHERE NOT EXISTS, no unique constraint needed.
"""
import os
import sys

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text

DATABASE_URL = os.environ.get('DATABASE_URL', '')
if not DATABASE_URL:
    print("ERROR: DATABASE_URL not set")
    sys.exit(1)

# Fix postgres:// -> postgresql://
if DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)

engine = create_engine(DATABASE_URL)

NG_BANDS = '{"type":"band_based","bands":[{"name":"A","hours_min":20,"price":225},{"name":"B","hours_min":16,"price":63},{"name":"C","hours_min":12,"price":50},{"name":"D","hours_min":8,"price":43},{"name":"E","hours_min":0,"price":40}]}'
NG_TAXES = '{"vat":0.075}'

TARIFF_ROWS = [
    ('NG', 'Eko Electricity Distribution Company',    'NGN', NG_BANDS, NG_TAXES),
    ('NG', 'Ikeja Electric',                          'NGN', NG_BANDS, NG_TAXES),
    ('NG', 'Abuja Electricity Distribution Company',  'NGN', NG_BANDS, NG_TAXES),
    ('NG', 'Enugu Electricity Distribution Company',  'NGN', NG_BANDS, NG_TAXES),
    ('NG', 'Port Harcourt Electricity Distribution',  'NGN', NG_BANDS, NG_TAXES),
    ('NG', 'Ibadan Electricity Distribution Company', 'NGN', NG_BANDS, NG_TAXES),
    ('NG', 'Kano Electricity Distribution Company',   'NGN', NG_BANDS, NG_TAXES),
    ('NG', 'Kaduna Electricity Distribution Company', 'NGN', NG_BANDS, NG_TAXES),
    ('NG', 'Jos Electricity Distribution Company',    'NGN', NG_BANDS, NG_TAXES),
    ('NG', 'Benin Electricity Distribution Company',  'NGN', NG_BANDS, NG_TAXES),
    ('NG', 'Yola Electricity Distribution Company',   'NGN', NG_BANDS, NG_TAXES),
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
    ('BR', 'ENEL São Paulo', 'BRL', '{"type":"tiered","tiers":[{"limit":200,"price":0.65},{"limit":null,"price":0.85}]}', '{"icms":0.20}'),
    ('BR', 'COPEL',          'BRL', '{"type":"tiered","tiers":[{"limit":200,"price":0.65},{"limit":null,"price":0.85}]}', '{"icms":0.20}'),
    ('BR', 'CELPE',          'BRL', '{"type":"tiered","tiers":[{"limit":200,"price":0.65},{"limit":null,"price":0.85}]}', '{"icms":0.20}'),
]

print(f"Connecting to DB...")
inserted = 0
skipped = 0

with engine.connect() as conn:
    # First check current state
    count = conn.execute(text("SELECT COUNT(*) FROM tariffs WHERE is_active = true")).scalar()
    print(f"Current active tariffs in DB: {count}")

    for (cc, provider, currency, rate_json, taxes_json) in TARIFF_ROWS:
        # Check if exists
        exists = conn.execute(text(
            "SELECT 1 FROM tariffs WHERE country_code=:cc AND utility_provider=:p AND is_active=true"
        ), {'cc': cc, 'p': provider}).fetchone()

        if exists:
            skipped += 1
            continue

        conn.execute(text("""
            INSERT INTO tariffs (country_code, utility_provider, currency, rate_structure, taxes_and_fees, valid_from, is_active)
            VALUES (:cc, :provider, :currency, :rate::jsonb, :taxes::jsonb, '2024-01-01', true)
        """), {
            'cc': cc,
            'provider': provider,
            'currency': currency,
            'rate': rate_json,
            'taxes': taxes_json,
        })
        inserted += 1
        print(f"  [+] {cc} / {provider}")

    conn.commit()

print(f"\nDone: {inserted} inserted, {skipped} already existed")

# Verify
with engine.connect() as conn:
    rows = conn.execute(text(
        "SELECT country_code, utility_provider FROM tariffs WHERE is_active=true ORDER BY country_code, utility_provider"
    )).fetchall()
    print(f"\nAll active tariffs ({len(rows)}):")
    for r in rows:
        print(f"  {r[0]} / {r[1]}")
