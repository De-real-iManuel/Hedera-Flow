"""Check for tariff mismatches between meters and tariffs"""
from app.core.database import get_db
from sqlalchemy import text

db = next(get_db())

print("=" * 60)
print("Checking Tariff Mismatches")
print("=" * 60)
print()

# Get all meters with their utility providers
print("Meters and their utility providers:")
print("-" * 60)
meters = db.execute(text("""
    SELECT m.id, m.meter_id, m.utility_provider, u.country_code, u.email
    FROM meters m
    JOIN users u ON m.user_id = u.id
""")).fetchall()

for meter in meters:
    print(f"Meter: {meter[1]}")
    print(f"  Provider: {meter[2]}")
    print(f"  Country: {meter[3]}")
    print(f"  User: {meter[4]}")
    
    # Check if tariff exists
    tariff = db.execute(text("""
        SELECT id FROM tariffs
        WHERE country_code = :country
        AND utility_provider = :provider
        AND is_active = true
    """), {
        'country': meter[3],
        'provider': meter[2]
    }).fetchone()
    
    if tariff:
        print(f"  ✓ Tariff exists")
    else:
        print(f"  ✗ NO TARIFF FOUND!")
        
        # Show available tariffs for this country
        available = db.execute(text("""
            SELECT utility_provider FROM tariffs
            WHERE country_code = :country
            AND is_active = true
        """), {'country': meter[3]}).fetchall()
        
        print(f"  Available tariffs for {meter[3]}:")
        for t in available:
            print(f"    - {t[0]}")
    
    print()

print("=" * 60)
print("Spain (ES) Tariffs:")
print("-" * 60)
es_tariffs = db.execute(text("""
    SELECT utility_provider FROM tariffs
    WHERE country_code = 'ES'
    AND is_active = true
""")).fetchall()

for t in es_tariffs:
    print(f"  - {t[0]}")
