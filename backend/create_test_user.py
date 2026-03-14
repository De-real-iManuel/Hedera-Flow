#!/usr/bin/env python3
"""
Create a test user for testing the verify endpoint
"""
from app.core.database import get_db
from app.models.user import User, CountryCodeEnum
from app.utils.auth import hash_password
from sqlalchemy.orm import Session
import uuid

def create_test_user():
    """Create a test user with known credentials"""
    
    db = next(get_db())
    
    # Check if test user already exists
    existing_user = db.query(User).filter(User.email == "testuser@hederaflow.com").first()
    if existing_user:
        print("Test user already exists")
        print(f"Email: testuser@hederaflow.com")
        print(f"Password: TestPassword123!")
        print(f"User ID: {existing_user.id}")
        return
    
    # Create new test user
    hashed_password = hash_password("TestPassword123!")
    
    test_user = User(
        id=uuid.uuid4(),
        email="testuser@hederaflow.com",
        password_hash=hashed_password,
        first_name="Test",
        last_name="User",
        country_code=CountryCodeEnum.ES,
        hedera_account_id="0.0.7942957",  # Use the operator account for testing
        is_active=True,
        is_email_verified=True
    )
    
    try:
        db.add(test_user)
        db.commit()
        print("Test user created successfully!")
        print(f"Email: testuser@hederaflow.com")
        print(f"Password: TestPassword123!")
        print(f"User ID: {test_user.id}")
        
    except Exception as e:
        db.rollback()
        print(f"Failed to create test user: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    create_test_user()