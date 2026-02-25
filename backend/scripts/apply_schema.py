#!/usr/bin/env python3
"""
Script to apply database schema to PostgreSQL
Usage: python scripts/apply_schema.py
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    import psycopg2
    from psycopg2 import sql
except ImportError:
    print("Error: psycopg2 not installed. Run: pip install psycopg2-binary")
    sys.exit(1)


def get_db_connection():
    """Get database connection from environment variables"""
    db_url = os.getenv('DATABASE_URL')
    
    if db_url:
        return psycopg2.connect(db_url)
    
    # Fallback to individual parameters
    return psycopg2.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        port=os.getenv('DB_PORT', '5432'),
        database=os.getenv('DB_NAME', 'hedera_flow'),
        user=os.getenv('DB_USER', 'postgres'),
        password=os.getenv('DB_PASSWORD', 'postgres')
    )


def apply_schema(migration_file='migrations/001_initial_schema.sql'):
    """Apply schema from migration file"""
    
    # Read migration file
    migration_path = Path(__file__).parent.parent / migration_file
    
    if not migration_path.exists():
        print(f"Error: Migration file not found: {migration_path}")
        sys.exit(1)
    
    with open(migration_path, 'r') as f:
        schema_sql = f.read()
    
    print(f"Applying schema from {migration_file}...")
    
    try:
        # Connect to database
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Execute schema
        cursor.execute(schema_sql)
        conn.commit()
        
        print("✅ Schema applied successfully!")
        
        # Verify tables were created
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name;
        """)
        
        tables = cursor.fetchall()
        print(f"\n📊 Created {len(tables)} tables:")
        for table in tables:
            print(f"  - {table[0]}")
        
        # Verify indexes
        cursor.execute("""
            SELECT indexname 
            FROM pg_indexes 
            WHERE schemaname = 'public' 
            ORDER BY indexname;
        """)
        
        indexes = cursor.fetchall()
        print(f"\n🔍 Created {len(indexes)} indexes:")
        for index in indexes[:10]:  # Show first 10
            print(f"  - {index[0]}")
        if len(indexes) > 10:
            print(f"  ... and {len(indexes) - 10} more")
        
        cursor.close()
        conn.close()
        
        print("\n✨ Database schema is ready!")
        
    except psycopg2.Error as e:
        print(f"❌ Database error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


def verify_schema():
    """Verify schema is correctly applied"""
    
    expected_tables = [
        'users', 'meters', 'tariffs', 'verifications', 
        'bills', 'disputes', 'exchange_rates', 'audit_logs'
    ]
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        print("\n🔍 Verifying schema...")
        
        # Check each table exists
        for table in expected_tables:
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = %s
                );
            """, (table,))
            
            exists = cursor.fetchone()[0]
            status = "✅" if exists else "❌"
            print(f"  {status} Table '{table}': {'exists' if exists else 'MISSING'}")
        
        cursor.close()
        conn.close()
        
        print("\n✅ Schema verification complete!")
        
    except Exception as e:
        print(f"❌ Verification error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Apply database schema')
    parser.add_argument('--verify', action='store_true', help='Verify schema only')
    parser.add_argument('--migration', default='migrations/001_initial_schema.sql', 
                       help='Migration file to apply')
    
    args = parser.parse_args()
    
    if args.verify:
        verify_schema()
    else:
        apply_schema(args.migration)
        verify_schema()
