"""
Tests for Subsidy Eligibility Service

Tests subsidy eligibility checking, setting, and revocation.

Requirements: FR-4.5 (System shall apply subsidies if user eligible)
"""
import pytest
from datetime import datetime, timezone, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from uuid import uuid4

from app.models.user import User, Base, CountryCodeEnum
from app.services.subsidy_service import (
    check_user_eligibility,
    set_user_eligibility,
    revoke_user_eligibility,
    SubsidyServiceError
)
from config import settings


# Test database setup
@pytest.fixture(scope="function")
def db_session():
    """Create a test database session"""
    engine = create_engine(settings.database_url)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    yield session
    
    session.close()


@pytest.fixture(scope="function")
def test_user(db_session):
    """Create a test user"""
    user = User(
        email=f"test_{uuid4()}@example.com",
        password_hash="hashed_password",
        country_code=CountryCodeEnum.ES,
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    
    yield user
    
    # Cleanup
    db_session.delete(user)
    db_session.commit()


class TestCheckUserEligibility:
    """Tests for check_user_eligibility function"""
    
    def test_check_ineligible_user(self, db_session, test_user):
        """Test checking eligibility for user not marked as eligible"""
        result = check_user_eligibility(db_session, str(test_user.id))
        
        assert result['eligible'] is False
        assert result['subsidy_type'] is None
        assert result['verified_at'] is None
        assert result['expires_at'] is None
        assert result['expired'] is False
        assert 'not marked as subsidy eligible' in result['reason']
    
    def test_check_eligible_user(self, db_session, test_user):
        """Test checking eligibility for eligible user"""
        # Set user as eligible
        test_user.subsidy_eligible = True
        test_user.subsidy_type = 'low_income'
        test_user.subsidy_verified_at = datetime.now(timezone.utc)
        test_user.subsidy_expires_at = datetime.now(timezone.utc) + timedelta(days=365)
        db_session.commit()
        
        result = check_user_eligibility(db_session, str(test_user.id))
        
        assert result['eligible'] is True
        assert result['subsidy_type'] == 'low_income'
        assert result['verified_at'] is not None
        assert result['expires_at'] is not None
        assert result['expired'] is False
        assert result['reason'] is None
    
    def test_check_expired_eligibility(self, db_session, test_user):
        """Test checking eligibility for user with expired eligibility"""
        # Set user as eligible but expired
        test_user.subsidy_eligible = True
        test_user.subsidy_type = 'senior_citizen'
        test_user.subsidy_verified_at = datetime.now(timezone.utc) - timedelta(days=400)
        test_user.subsidy_expires_at = datetime.now(timezone.utc) - timedelta(days=1)
        db_session.commit()
        
        result = check_user_eligibility(db_session, str(test_user.id))
        
        assert result['eligible'] is False
        assert result['subsidy_type'] == 'senior_citizen'
        assert result['expired'] is True
        assert 'expired' in result['reason'].lower()
    
    def test_check_nonexistent_user(self, db_session):
        """Test checking eligibility for non-existent user"""
        fake_user_id = str(uuid4())
        
        with pytest.raises(SubsidyServiceError) as exc_info:
            check_user_eligibility(db_session, fake_user_id)
        
        assert "not found" in str(exc_info.value).lower()


class TestSetUserEligibility:
    """Tests for set_user_eligibility function"""
    
    def test_set_user_eligible(self, db_session, test_user):
        """Test setting user as eligible for subsidies"""
        expires_at = datetime.now(timezone.utc) + timedelta(days=365)
        
        result = set_user_eligibility(
            db_session,
            str(test_user.id),
            eligible=True,
            subsidy_type='low_income',
            expires_at=expires_at
        )
        
        assert result['eligible'] is True
        assert result['subsidy_type'] == 'low_income'
        assert result['verified_at'] is not None
        assert result['expires_at'] == expires_at
        
        # Verify in database
        db_session.refresh(test_user)
        assert test_user.subsidy_eligible is True
        assert test_user.subsidy_type == 'low_income'
    
    def test_set_user_ineligible(self, db_session, test_user):
        """Test setting user as ineligible (revoke)"""
        # First set as eligible
        test_user.subsidy_eligible = True
        test_user.subsidy_type = 'disability'
        db_session.commit()
        
        # Now revoke
        result = set_user_eligibility(
            db_session,
            str(test_user.id),
            eligible=False
        )
        
        assert result['eligible'] is False
        assert result['subsidy_type'] is None
        assert result['verified_at'] is None
        
        # Verify in database
        db_session.refresh(test_user)
        assert test_user.subsidy_eligible is False
        assert test_user.subsidy_type is None
    
    def test_set_invalid_subsidy_type(self, db_session, test_user):
        """Test setting eligibility with invalid subsidy type"""
        with pytest.raises(SubsidyServiceError) as exc_info:
            set_user_eligibility(
                db_session,
                str(test_user.id),
                eligible=True,
                subsidy_type='invalid_type'
            )
        
        assert "invalid subsidy type" in str(exc_info.value).lower()
    
    def test_set_eligibility_nonexistent_user(self, db_session):
        """Test setting eligibility for non-existent user"""
        fake_user_id = str(uuid4())
        
        with pytest.raises(SubsidyServiceError) as exc_info:
            set_user_eligibility(
                db_session,
                fake_user_id,
                eligible=True,
                subsidy_type='low_income'
            )
        
        assert "not found" in str(exc_info.value).lower()


class TestRevokeUserEligibility:
    """Tests for revoke_user_eligibility function"""
    
    def test_revoke_eligibility(self, db_session, test_user):
        """Test revoking user eligibility"""
        # First set as eligible
        test_user.subsidy_eligible = True
        test_user.subsidy_type = 'energy_efficiency'
        test_user.subsidy_verified_at = datetime.now(timezone.utc)
        db_session.commit()
        
        # Revoke
        result = revoke_user_eligibility(
            db_session,
            str(test_user.id),
            reason="Test revocation"
        )
        
        assert result['eligible'] is False
        assert result['subsidy_type'] is None
        
        # Verify in database
        db_session.refresh(test_user)
        assert test_user.subsidy_eligible is False
    
    def test_revoke_already_ineligible(self, db_session, test_user):
        """Test revoking eligibility for already ineligible user"""
        # User is already ineligible by default
        result = revoke_user_eligibility(
            db_session,
            str(test_user.id)
        )
        
        assert result['eligible'] is False


class TestSubsidyTypes:
    """Tests for different subsidy types"""
    
    @pytest.mark.parametrize("subsidy_type", [
        'low_income',
        'senior_citizen',
        'disability',
        'energy_efficiency'
    ])
    def test_valid_subsidy_types(self, db_session, test_user, subsidy_type):
        """Test all valid subsidy types"""
        result = set_user_eligibility(
            db_session,
            str(test_user.id),
            eligible=True,
            subsidy_type=subsidy_type
        )
        
        assert result['eligible'] is True
        assert result['subsidy_type'] == subsidy_type


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
