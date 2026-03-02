"""
Run SQL migration script - Add hedera_account_id to utility_providers
"""
import psycopg2
from config import settings

# Parse DATABASE_URL
db_url = settings.database_url

# Extract connection parameters
parts = db_url.replace('postgresql://', '').split('@')
user_pass = parts[0].split(':')
host_db = parts[1].split('/')
host_port = host_db[0].split(':')

conn_params = {
    'user': user_pass[0],
    'password': user_pass[1],
    'host': host_port[0],
    'port': host_port[1],
    'database': host_db[1]
}

print(f"Connecting to database: {conn_params['database']}@{conn_params['host']}")

# Connect and run migration
conn = psycopg2.connect(**conn_params)
conn.autocommit = True
cursor = conn.cursor()

print("Running migration: 004_add_hedera_account_to_utility_providers.sql")

# Read migration file
with open('migrations/004_add_hedera_account_to_utility_providers.sql', 'r') as f:
    sql = f.read()

# Execute migration
try:
    cursor.execute(sql)
    print("✅ Migration completed successfully!")
    
    # Verify column was added
    cursor.execute("""
        SELECT column_name, data_type, is_nullable, column_default
        FROM information_schema.columns
        WHERE table_name = 'utility_providers' 
        AND column_name = 'hedera_account_id'
        ORDER BY column_name;
    """)
    
    print("\nVerification - New column:")
    for row in cursor.fetchall():
        print(f"  - {row[0]}: {row[1]} (nullable: {row[2]}, default: {row[3]})")
    
    # Check how many providers have hedera_account_id set
    cursor.execute("""
        SELECT 
            COUNT(*) as total,
            COUNT(hedera_account_id) as with_hedera_account,
            COUNT(*) - COUNT(hedera_account_id) as without_hedera_account
        FROM utility_providers;
    """)
    
    result = cursor.fetchone()
    print(f"\nUtility Providers:")
    print(f"  - Total: {result[0]}")
    print(f"  - With Hedera Account: {result[1]}")
    print(f"  - Without Hedera Account: {result[2]}")
    
except Exception as e:
    print(f"❌ Migration failed: {e}")
    raise
finally:
    cursor.close()
    conn.close()
    print("\nDatabase connection closed")
