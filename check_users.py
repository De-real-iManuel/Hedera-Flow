#!/usr/bin/env python3
"""
Check existing users in the database
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.models.user import User

def check_users():
    """Check what users exist in the database"""
    print("👥 Checking existing users in database...")
    
    # Get database session
    db_gen = get_db()
    db: Session = next(db_gen)
    
    try:
        # Query all users
        users = db.query(User).all()
        
        print(f"\nFound {len(users)} users:")
        for user in users:
            print(f"  - ID: {user.id}")
            print(f"    Email: {user.email}")
            print(f"    Name: {user.first_name} {user.last_name}")
            print(f"    Country: {user.country_code}")
            print(f"    Hedera Account: {user.hedera_account_id}")
            print(f"    Wallet Type: {user.wallet_type}")
            print(f"    Active: {user.is_active}")
            print(f"    Has Password: {'Yes' if user.password_hash else 'No'}")
            print(f"    Created: {user.created_at}")
            print()
            
    except Exception as e:
        print(f"❌ Error checking users: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    check_users()