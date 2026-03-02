"""
Run SQL migration script for user preferences and security settings
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

print("Running migration: 005_add_user_preferences_and_security.sql")

# Read migration file
with open('migrations/005_add_user_preferences_and_security.sql', 'r') as f:
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
        AND column_name IN ('preferences', 'security_settings')
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
