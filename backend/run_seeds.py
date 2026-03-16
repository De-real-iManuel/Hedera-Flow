#!/usr/bin/env python3
"""
Run database seed scripts
"""
import os
import sys
from pathlib import Path
from sqlalchemy import create_engine, text
from config import settings

def run_sql_file(engine, file_path):
    """Run a SQL file against the database"""
    print(f"Running {file_path}...")
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        # Split by semicolon and execute each statement
        statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]
        
        with engine.connect() as conn:
            for stmt in statements:
                if stmt:
                    conn.execute(text(stmt))
            conn.commit()
        
        print(f"✅ Successfully ran {file_path}")
        return True
    except Exception as e:
        print(f"❌ Error running {file_path}: {e}")
        return False

def main():
    """Run all seed scripts"""
    print("🌱 Running database seed scripts...")
    
    # Create database engine
    engine = create_engine(settings.database_url)
    
    # List of seed files to run in order
    seed_files = [
        "migrations/seed_nigeria_discos.sql",
        "migrations/seed_tariffs.sql"
    ]
    
    success_count = 0
    for seed_file in seed_files:
        file_path = Path(seed_file)
        if file_path.exists():
            if run_sql_file(engine, file_path):
                success_count += 1
        else:
            print(f"⚠️  Seed file not found: {seed_file}")
    
    print(f"\n🎉 Completed! {success_count}/{len(seed_files)} seed scripts ran successfully")

if __name__ == "__main__":
    main()