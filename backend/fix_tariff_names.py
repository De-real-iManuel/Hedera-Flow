"""Add tariffs with exact meter utility provider names"""
from app.core.database import get_db
from sqlalchemy import text
from datetime import date
import json

db = next(get_db())

# Tariffs to add with exact meter names
tariffs_to_add = [
    {
        'country_code': 'ES',
        'utility_provider': 'i-DE (Iberdrola)',
        'currency': 'EUR',
        'rate_structure': {
            'type': 'flat',
            'rate': 0.15
        },
        'taxes_and_fees': {
            'vat': 0.21,
            'fixed_charge': 5.0
        }
    },
    {
        'country_code': 'ES',
        'utility_provider': 'UFD (Naturgy)',
        'currency': 'EUR',
        'rate_structure': {
            'type': 'flat',
            'rate': 0.14
        },
        'taxes_and_fees': {
            'vat': 0.21,
            'fixed_charge': 5.0
        }
    }
]

print("=" * 60)
print("Adding Tariffs with Exact Meter Names")
print("=" * 60)
print()

for tariff in tariffs_to_add:
    print(f"Adding: {tariff['country_code']}/{tariff['utility_provider']}")
    
    # Check if exists
    check = db.execute(text("""
        SELECT id FROM tariffs
        WHERE country_code = :country
        AND utility_provider = :provider
        AND is_active = true
    """), {
        'country': tariff['country_code'],
        'provider': tariff['utility_provider']
    }).fetchone()
    
    if check:
        print("  Already exists, skipping")
    else:
        # Insert
        db.execute(text("""
            INSERT INTO tariffs (
                id,
                country_code,
                utility_provider,
                currency,
                rate_structure,
                taxes_and_fees,
                subsidies,
                valid_from,
                valid_until,
                is_active,
                created_at,
                updated_at
            ) VALUES (
                gen_random_uuid(),
                :country_code,
                :utility_provider,
                :currency,
                CAST(:rate_structure AS jsonb),
                CAST(:taxes_and_fees AS jsonb),
                '{}'::jsonb,
                :valid_from,
                NULL,
                true,
                NOW(),
                NOW()
            )
        """), {
            'country_code': tariff['country_code'],
            'utility_provider': tariff['utility_provider'],
            'currency': tariff['currency'],
            'rate_structure': json.dumps(tariff['rate_structure']),
            'taxes_and_fees': json.dumps(tariff['taxes_and_fees']),
            'valid_from': date.today()
        })
        
        print("  ✓ Added successfully")
    
    print()

db.commit()

print("=" * 60)
print("✓ Done!")
print("=" * 60)
print()

# Verify
print("Verifying meters now have tariffs:")
print("-" * 60)

meters = db.execute(text("""
    SELECT m.meter_id, m.utility_provider, u.country_code
    FROM meters m
    JOIN users u ON m.user_id = u.id
""")).fetchall()

for meter in meters:
    tariff = db.execute(text("""
        SELECT id FROM tariffs
        WHERE country_code = :country
        AND utility_provider = :provider
        AND is_active = true
    """), {
        'country': meter[2],
        'provider': meter[1]
    }).fetchone()
    
    status = "✓" if tariff else "✗"
    print(f"{status} {meter[0]} | {meter[1]} | {meter[2]}")
