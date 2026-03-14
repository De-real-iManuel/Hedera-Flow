"""Check if the token exists"""
from app.core.database import get_db
from sqlalchemy import text

db = next(get_db())

# Check recent tokens
print("Recent prepaid tokens:")
print("-" * 80)

result = db.execute(text("""
    SELECT token_id, status, amount_paid_hbar, hedera_tx_id, issued_at
    FROM prepaid_tokens
    ORDER BY issued_at DESC
    LIMIT 5
""")).fetchall()

for row in result:
    print(f"Token: {row[0]}")
    print(f"  Status: {row[1]}")
    print(f"  Amount: {row[2]} HBAR")
    print(f"  TX ID: {row[3]}")
    print(f"  Issued: {row[4]}")
    print()

# Check specifically for TOKEN-NG-2026-010
print("Checking TOKEN-NG-2026-010:")
print("-" * 80)

result = db.execute(text("""
    SELECT token_id, status, amount_paid_hbar, user_id, meter_id
    FROM prepaid_tokens
    WHERE token_id = 'TOKEN-NG-2026-010'
""")).fetchone()

if result:
    print(f"✓ Token found!")
    print(f"  Token ID: {result[0]}")
    print(f"  Status: {result[1]}")
    print(f"  Amount: {result[2]} HBAR")
    print(f"  User ID: {result[3]}")
    print(f"  Meter ID: {result[4]}")
else:
    print("✗ Token not found!")
    print("The token may not have been created yet.")
    print("Check if the /prepaid/buy endpoint was called successfully.")
