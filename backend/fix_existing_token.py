"""
Fix existing token TOKEN-NG-2026-010 to be in pending state
so it can be confirmed with EVM transaction.
"""
from sqlalchemy import create_engine, text
from config import settings

def fix_token():
    engine = create_engine(settings.database_url)
    
    with engine.connect() as conn:
        # Check current state
        result = conn.execute(text("""
            SELECT token_id, status, amount_paid_hbar, hedera_tx_id
            FROM prepaid_tokens
            WHERE token_id = 'TOKEN-NG-2026-010'
        """)).fetchone()
        
        if result:
            print(f"Current state:")
            print(f"  Token: {result[0]}")
            print(f"  Status: {result[1]}")
            print(f"  Amount: {result[2]}")
            print(f"  TX ID: {result[3]}")
            print()
            
            # Update to pending state
            conn.execute(text("""
                UPDATE prepaid_tokens
                SET status = 'pending',
                    amount_paid_hbar = 0.29411764705882354,
                    hedera_tx_id = NULL,
                    hedera_consensus_timestamp = NULL
                WHERE token_id = 'TOKEN-NG-2026-010'
            """))
            conn.commit()
            
            # Verify update
            result = conn.execute(text("""
                SELECT token_id, status, amount_paid_hbar, hedera_tx_id
                FROM prepaid_tokens
                WHERE token_id = 'TOKEN-NG-2026-010'
            """)).fetchone()
            
            print(f"Updated state:")
            print(f"  Token: {result[0]}")
            print(f"  Status: {result[1]}")
            print(f"  Amount: {result[2]}")
            print(f"  TX ID: {result[3]}")
            print()
            print("✅ Token fixed! Now it can be confirmed with EVM transaction.")
        else:
            print("❌ Token not found")

if __name__ == "__main__":
    fix_token()
