"""
Password Reset Utility
Run this script to reset a user's password in the database.

Usage:
    python reset_password.py <email> <new_password>

Example:
    python reset_password.py user@example.com NewPassword1
"""
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.utils.auth import hash_password
from app.core.database import SessionLocal
from app.models.user import User


def reset_password(email: str, new_password: str):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            print(f"ERROR: User not found: {email}")
            return False

        user.password_hash = hash_password(new_password)
        db.commit()
        print(f"OK: Password reset for {email}")
        return True
    except Exception as e:
        db.rollback()
        print(f"ERROR: {e}")
        return False
    finally:
        db.close()


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python reset_password.py <email> <new_password>")
        sys.exit(1)

    email = sys.argv[1]
    password = sys.argv[2]

    if len(password) < 8 or not any(c.isupper() for c in password) or not any(c.isdigit() for c in password):
        print("ERROR: Password must be 8+ chars, 1 uppercase, 1 number")
        sys.exit(1)

    success = reset_password(email, password)
    sys.exit(0 if success else 1)
