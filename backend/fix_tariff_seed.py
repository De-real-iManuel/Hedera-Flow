"""
Rewrite tariff seeding in app/core/app.py to use per-row WHERE NOT EXISTS inserts.
This avoids needing any unique constraint on the tariffs table.
"""
import re

path = 'app/core/app.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# ── Find and replace the tariff_seed_sql f-string + Step 4 block ──────────────
# We'll replace from "# Seed tariffs for all providers" through the end of Step 4

OLD_MARKER_START = '    # Seed tariffs for all providers'
OLD_MARKER_END   = '        print("[OK] Tariffs seeded")\n    except Exception as e:\n        print(f"[WARN] Tariff seed skipped: {e}")'

start_idx = content.find(OLD_MARKER_START)
end_idx   = content.find(OLD_MARKER_END)

if start_idx == -1 or end_idx == -1:
    print(f'Markers not found: start={start_idx}, end={end_idx}')
    exit(1)

end_idx += len(OLD_MARKER_END)

NEW_BLOCK = '''    # Seed tariffs for all providers — per-row WHERE NOT EXISTS (no unique constraint needed)
    TARIFF_ROWS = [
        # (country_code, utility_provider, currency, rate_structure_json, taxes_json)
        # Nigeria DISCOs — band-based
        ('NG','Eko Electricity Distribution Company',   'NGN',
         '{"type":"band_based","bands":[{"name":"A","hours_min":20,"price":225},{"name":"B","hours_min":16,"price":63},{"name":"C","hours_min":12,"price":50},{"name":"D","hours_min":8,"price":43},{"name":"E","hours_min":0,"price":40}]}',
         '{"vat":0.075}'),
        ('NG','Ikeja Electric',                         'NGN',
         '{"type":"band_based","bands":[{"name":"A","hours_min":20,"price":225},{"name":"B","hours_min":16,"price":63},{"name":"C","hours_min":12,"price":50},{"name":"D","hours_min":8,"price":43},{"name":"E","hours_min":0,"price":40}]}',
         '{"vat":0.075}'),
        ('NG','Abuja Electricity Distribution Company', 'NGN',
         '{"type":"band_based","bands":[{"name":"A","hours_min":20,"price":225},{"name":"B","hours_min":16,"price":63},{"name":"C","hours_min":12,"price":50},{"name":"D","hours_min":8,"price":43},{"name":"E","hours_min":0,"price":40}]}',
         '{"vat":0.075}'),
        ('NG','Enugu Electricity Distribution Company', 'NGN',
         '{"type":"band_based","bands":[{"name":"A","hours_min":20,"price":225},{"name":"B","hours_min":16,"price":63},{"name":"C","hours_min":12,"price":50},{"name":"D","hours_min":8,"price":43},{"name":"E","hours_min":0,"price":40}]}',
         '{"vat":0.075}'),
        ('NG','Port Harcourt Electricity Distribution', 'NGN',
         '{"type":"band_based","bands":[{"name":"A","hours_min":20,"price":225},{"name":"B","hours_min":16,"price":63},{"name":"C","hours_min":12,"price":50},{"name":"D","hours_min":8,"price":43},{"name":"E","hours_min":0,"price":40}]}',
         '{"vat":0.075}'),
        ('NG','Ibadan Electricity Distribution Company','NGN',
         '{"type":"band_based","bands":[{"name":"A","hours_min":20,"price":225},{"name":"B","hours_min":16,"price":63},{"name":"C","hours_min":12,"price":50},{"name":"D","hours_min":8,"price":43},{"name":"E","hours_min":0,"price":40}]}',
         '{"vat":0.075}'),
        ('NG','Kano Electricity Distribution Company',  'NGN',
         '{"type":"band_based","bands":[{"name":"A","hours_min":20,"price":225},{"name":"B","hours_min":16,"price":63},{"name":"C","hours_min":12,"price":50},{"name":"D","hours_min":8,"price":43},{"name":"E","hours_min":0,"price":40}]}',
         '{"vat":0.075}'),
        ('NG','Kaduna Electricity Distribution Company','NGN',
         '{"type":"band_based","bands":[{"name":"A","hours_min":20,"price":225},{"name":"B","hours_min":16,"price":63},{"name":"C","hours_min":12,"price":50},{"name":"D","hours_min":8,"price":43},{"name":"E","hours_min":0,"price":40}]}',
         '{"vat":0.075}'),
        ('NG','Jos Electricity Distribution Company',   'NGN',
         '{"type":"band_based","bands":[{"name":"A","hours_min":20,"price":225},{"name":"B","hours_min":16,"price":63},{"name":"C","hours_min":12,"price":50},{"name":"D","hours_min":8,"price":43},{"name":"E","hours_min":0,"price":40}]}',
         '{"vat":0.075}'),
        ('NG','Benin Electricity Distribution Company', 'NGN',
         '{"type":"band_based","bands":[{"name":"A","hours_min":20,"price":225},{"name":"B","hours_min":16,"price":63},{"name":"C","hours_min":12,"price":50},{"name":"D","hours_min":8,"price":43},{"name":"E","hours_min":0,"price":40}]}',
         '{"vat":0.075}'),
        ('NG','Yola Electricity Distribution Company',  'NGN',
         '{"type":"band_based","bands":[{"name":"A","hours_min":20,"price":225},{"name":"B","hours_min":16,"price":63},{"name":"C","hours_min":12,"price":50},{"name":"D","hours_min":8,"price":43},{"name":"E","hours_min":0,"price":40}]}',
         '{"vat":0.075}'),
        # Spain — flat
        ('ES','Iberdrola','EUR','{"type":"flat","rate":0.18}','{"vat":0.21}'),
        ('ES','Endesa',   'EUR','{"type":"flat","rate":0.18}','{"vat":0.21}'),
        ('ES','Naturgy',  'EUR','{"type":"flat","rate":0.18}','{"vat":0.21}'),
        # USA — tiered
        ('US','Pacific Gas & Electric','USD','{"type":"tiered","tiers":[{"limit":500,"price":0.12},{"limit":null,"price":0.18}]}','{"tax":0.08}'),
        ('US','Con Edison',            'USD','{"type":"tiered","tiers":[{"limit":500,"price":0.12},{"limit":null,"price":0.18}]}','{"tax":0.08}'),
        ('US','ComEd',                 'USD','{"type":"tiered","tiers":[{"limit":500,"price":0.12},{"limit":null,"price":0.18}]}','{"tax":0.08}'),
        ('US','Florida Power & Light', 'USD','{"type":"tiered","tiers":[{"limit":500,"price":0.12},{"limit":null,"price":0.18}]}','{"tax":0.08}'),
        ('US','Texas Electric',        'USD','{"type":"tiered","tiers":[{"limit":500,"price":0.12},{"limit":null,"price":0.18}]}','{"tax":0.08}'),
        # India — tiered
        ('IN','Tata Power',   'INR','{"type":"tiered","tiers":[{"limit":100,"price":3.5},{"limit":300,"price":5.5},{"limit":null,"price":7.5}]}','{"tax":0.05}'),
        ('IN','BSES Rajdhani','INR','{"type":"tiered","tiers":[{"limit":100,"price":3.5},{"limit":300,"price":5.5},{"limit":null,"price":7.5}]}','{"tax":0.05}'),
        ('IN','BSES Yamuna',  'INR','{"type":"tiered","tiers":[{"limit":100,"price":3.5},{"limit":300,"price":5.5},{"limit":null,"price":7.5}]}','{"tax":0.05}'),
        ('IN','BESCOM',       'INR','{"type":"tiered","tiers":[{"limit":100,"price":3.5},{"limit":300,"price":5.5},{"limit":null,"price":7.5}]}','{"tax":0.05}'),
        ('IN','TNEB',         'INR','{"type":"tiered","tiers":[{"limit":100,"price":3.5},{"limit":300,"price":5.5},{"limit":null,"price":7.5}]}','{"tax":0.05}'),
        # Brazil — tiered
        ('BR','CEMIG',         'BRL','{"type":"tiered","tiers":[{"limit":200,"price":0.65},{"limit":null,"price":0.85}]}','{"icms":0.20}'),
        ('BR','ENEL São Paulo','BRL','{"type":"tiered","tiers":[{"limit":200,"price":0.65},{"limit":null,"price":0.85}]}','{"icms":0.20}'),
        ('BR','COPEL',         'BRL','{"type":"tiered","tiers":[{"limit":200,"price":0.65},{"limit":null,"price":0.85}]}','{"icms":0.20}'),
        ('BR','CELPE',         'BRL','{"type":"tiered","tiers":[{"limit":200,"price":0.65},{"limit":null,"price":0.85}]}','{"icms":0.20}'),
    ]

    # Step 4: seed tariffs using WHERE NOT EXISTS (no unique constraint required)
    try:
        inserted = 0
        with engine.connect() as conn:
            for (cc, provider, currency, rate_json, taxes_json) in TARIFF_ROWS:
                result = conn.execute(text("""
                    INSERT INTO tariffs (country_code, utility_provider, currency, rate_structure, taxes_and_fees, valid_from, is_active)
                    SELECT :cc, :provider, :currency, :rate_structure::jsonb, :taxes_and_fees::jsonb, '2024-01-01', true
                    WHERE NOT EXISTS (
                        SELECT 1 FROM tariffs
                        WHERE country_code = :cc
                          AND utility_provider = :provider
                          AND is_active = true
                    )
                """), {
                    'cc': cc,
                    'provider': provider,
                    'currency': currency,
                    'rate_structure': rate_json,
                    'taxes_and_fees': taxes_json,
                })
                inserted += result.rowcount
            conn.commit()
        print(f"[OK] Tariffs seeded ({inserted} new rows)")
    except Exception as e:
        print(f"[WARN] Tariff seed skipped: {e}")'''

content = content[:start_idx] + NEW_BLOCK + content[end_idx:]

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

print('SUCCESS: rewrote tariff seeding to use per-row WHERE NOT EXISTS')
