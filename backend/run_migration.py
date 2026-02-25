"""
Run SQL migration script
"""
import psycopg2
from config import settings

# Parse DATABASE_URL
db_url = settings.database_url
# postgresql://hedera_user:hedera_dev_password@localhost:5432/hedera_flow

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

print("Running migration: 004_add_email_verification.sql")

# Read migration file
with open('migrations/004_add_email_verification.sql', 'r') as f:
    sql = f.read()

# Execute migration
try:
    cursor.execute(sql)
    print("✅ Migration completed successfully!")
    
    # Verify columns were added
    cursor.execute("""
        SELECT column_name, data_type, is_nullable, column_default
        FROM information_schema.columns
        WHERE table_name = 'users' 
        AND column_name IN ('is_email_verified', 'email_verification_token', 'email_verification_expires')
        ORDER BY column_name;
    """)
    
    print("\nVerification - New columns:")
    for row in cursor.fetchall():
        print(f"  - {row[0]}: {row[1]} (nullable: {row[2]}, default: {row[3]})")
    
except Exception as e:
    print(f"❌ Migration failed: {e}")
    raise
finally:
    cursor.close()
    conn.close()
    print("\nDatabase connection closed")
