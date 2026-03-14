#!/usr/bin/env python3
"""
Check user password and reset if needed
"""
import sys
sys.path.append('.')

from app.core.database import get_db
from app.models.user import User
from app.utils.auth import hash_password, verify_password
from sqlalchemy.orm import Session

def check_and_reset_user():
    """Check user and reset password if needed"""
    
    db = next(get_db())
    
    try:
        # Find the user
        user = db.query(User).filter(User.email == "nicxbrown35@gmail.com").first()
        
        if not user:
            print("❌ User not found: nicxbrown35@gmail.com")
            return
        
        print(f"✅ Found user: {user.email}")
        print(f"   ID: {user.id}")
        print(f"   Name: {user.first_name} {user.last_name}")
        print(f"   Active: {user.is_active}")
        
        # Try different passwords
        test_passwords = [
            "password123",
            "Password123!",
            "TestPassword123!",
            "password",
            "123456"
        ]
        
        print(f"\n🔍 Testing passwords...")
        for pwd in test_passwords:
            if verify_password(pwd, user.password_hash):
                print(f"   ✅ Correct password: {pwd}")
                return pwd
        
        print(f"   ❌ None of the test passwords work")
        
        # Reset to known password
        new_password = "Password123!"
        user.password_hash = hash_password(new_password)
        db.commit()
        
        print(f"\n🔧 Password reset to: {new_password}")
        return new_password
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    password = check_and_reset_user()
    if password:
        print(f"\n💡 Use this for login:")
        print(f"   Email: nicxbrown35@gmail.com")
        print(f"   Password: {password}")