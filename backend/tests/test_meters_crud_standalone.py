"""
Task 7.7: Test meter CRUD operations for all 5 regions
Standalone test without Hedera dependencies
"""
import pytest
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import uuid

# Import only what we need, avoiding Hedera
from app.core.database import Base
from app.models.user import User, CountryCodeEnum, WalletTypeEnum
from app.models.meter import Meter, MeterTypeEnum
from app.models.utility_provider import UtilityProvider
from config import settings

# Test database setup
TEST_DB_URL = "sqlite:///./test_meters_crud.db"

@pytest.fixture(scope="function")
def db_session():
    """Create a test database session"""
    engine = create_engine(TEST_DB_URL, echo=False)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    
    yield session
    
    session.close()
    Base.metadata.drop_all(engine)
    engine.dispose()

@pytest.fixture
def test_users(db_session):
    """Create test users for each region"""
    users = {}
    for country in ["ES", "US", "IN", "BR", "NG"]:
        user = User(
            email=f"test_{country.lower()}@example.com",
            password_hash="hashed_password",
            country_code=CountryCodeEnum[country],
            hedera_account_id=f"0.0.TEST_{country}",
            wallet_type=WalletTypeEnum.SYSTEM_GENERATED,
            is_active=True
        )
        db_session.add(user)
        users[country] = user
    
    db_session.commit()
    return users

@pytest.fixture
def test_providers(db_session):
    """Create test utility providers for each region"""
    providers = {}
    
    # Spain
    providers["ES"] = UtilityProvider(
        name="Iberdrola",
        country_code="ES",
        state_province="Madrid",
        hedera_account_id="0.0.IBERDROLA"
    )
    
    # USA
    providers["US"] = UtilityProvider(
        name="PG&E",
        country_code="US",
        state_province="California",
        hedera_account_id="0.0.PGE"
    )
    
    # India
    providers["IN"] = UtilityProvider(
        name="Tata Power",
        country_code="IN",
        state_province="Maharashtra",
        hedera_account_id="0.0.TATA"
    )
    
    # Brazil
    providers["BR"] = UtilityProvider(
        name="Enel",
        country_code="BR",
        state_province="São Paulo",
        hedera_account_id="0.0.ENEL"
    )
    
    # Nigeria
    providers["NG"] = UtilityProvider(
        name="EKEDC",
        country_code="NG",
        state_province="Lagos",
        hedera_account_id="0.0.EKEDC"
    )
    
    for provider in providers.values():
        db_session.add(provider)
    
    db_session.commit()
    return providers


class TestMeterCRUD_Spain:
    """Test meter CRUD operations for Spain"""
    
    def test_create_meter_spain(self, db_session, test_users, test_providers):
        """Test creating a meter in Spain"""
        user = test_users["ES"]
        provider = test_providers["ES"]
        
        meter = Meter(
            user_id=user.id,
            utility_provider_id=provider.id,
            meter_id="ES-12345678",
            meter_type=MeterTypeEnum.DIGITAL,
            is_prepaid=False
        )
        db_session.add(meter)
        db_session.commit()
        
        assert meter.id is not None
        assert meter.meter_id == "ES-12345678"
        assert meter.user_id == user.id
    
    def test_read_meter_spain(self, db_session, test_users, test_providers):
        """Test reading a meter in Spain"""
        user = test_users["ES"]
        provider = test_providers["ES"]
        
        meter = Meter(
            user_id=user.id,
            utility_provider_id=provider.id,
            meter_id="ES-READ-001",
            meter_type=MeterTypeEnum.SMART
        )
        db_session.add(meter)
        db_session.commit()
        
        found = db_session.query(Meter).filter_by(meter_id="ES-READ-001").first()
        assert found is not None
        assert found.meter_id == "ES-READ-001"
    
    def test_update_meter_spain(self, db_session, test_users, test_providers):
        """Test updating a meter in Spain"""
        user = test_users["ES"]
        provider = test_providers["ES"]
        
        meter = Meter(
            user_id=user.id,
            utility_provider_id=provider.id,
            meter_id="ES-UPDATE-001",
            meter_type=MeterTypeEnum.ANALOG
        )
        db_session.add(meter)
        db_session.commit()
        
        meter.meter_type = MeterTypeEnum.DIGITAL
        db_session.commit()
        
        updated = db_session.query(Meter).filter_by(id=meter.id).first()
        assert updated.meter_type == MeterTypeEnum.DIGITAL
    
    def test_delete_meter_spain(self, db_session, test_users, test_providers):
        """Test deleting a meter in Spain"""
        user = test_users["ES"]
        provider = test_providers["ES"]
        
        meter = Meter(
            user_id=user.id,
            utility_provider_id=provider.id,
            meter_id="ES-DELETE-001",
            meter_type=MeterTypeEnum.DIGITAL
        )
        db_session.add(meter)
        db_session.commit()
        meter_id = meter.id
        
        db_session.delete(meter)
        db_session.commit()
        
        deleted = db_session.query(Meter).filter_by(id=meter_id).first()
        assert deleted is None


class TestMeterCRUD_USA:
    """Test meter CRUD operations for USA"""
    
    def test_create_meter_usa(self, db_session, test_users, test_providers):
        user = test_users["US"]
        provider = test_providers["US"]
        
        meter = Meter(
            user_id=user.id,
            utility_provider_id=provider.id,
            meter_id="US-87654321",
            meter_type=MeterTypeEnum.SMART
        )
        db_session.add(meter)
        db_session.commit()
        
        assert meter.id is not None
        assert meter.meter_id == "US-87654321"


class TestMeterCRUD_India:
    """Test meter CRUD operations for India"""
    
    def test_create_meter_india(self, db_session, test_users, test_providers):
        user = test_users["IN"]
        provider = test_providers["IN"]
        
        meter = Meter(
            user_id=user.id,
            utility_provider_id=provider.id,
            meter_id="IN-11223344",
            meter_type=MeterTypeEnum.DIGITAL
        )
        db_session.add(meter)
        db_session.commit()
        
        assert meter.id is not None
        assert meter.meter_id == "IN-11223344"


class TestMeterCRUD_Brazil:
    """Test meter CRUD operations for Brazil"""
    
    def test_create_meter_brazil(self, db_session, test_users, test_providers):
        user = test_users["BR"]
        provider = test_providers["BR"]
        
        meter = Meter(
            user_id=user.id,
            utility_provider_id=provider.id,
            meter_id="BR-99887766",
            meter_type=MeterTypeEnum.DIGITAL
        )
        db_session.add(meter)
        db_session.commit()
        
        assert meter.id is not None
        assert meter.meter_id == "BR-99887766"


class TestMeterCRUD_Nigeria:
    """Test meter CRUD operations for Nigeria"""
    
    def test_create_meter_nigeria(self, db_session, test_users, test_providers):
        user = test_users["NG"]
        provider = test_providers["NG"]
        
        meter = Meter(
            user_id=user.id,
            utility_provider_id=provider.id,
            meter_id="NG-55443322",
            meter_type=MeterTypeEnum.PREPAID,
            is_prepaid=True,
            band_classification="A"
        )
        db_session.add(meter)
        db_session.commit()
        
        assert meter.id is not None
        assert meter.meter_id == "NG-55443322"
        assert meter.band_classification == "A"


class TestMeterCRUD_AllRegions:
    """Test meter operations across all regions"""
    
    def test_list_all_meters(self, db_session, test_users, test_providers):
        """Test listing meters from all regions"""
        # Create meters for each region
        for country in ["ES", "US", "IN", "BR", "NG"]:
            meter = Meter(
                user_id=test_users[country].id,
                utility_provider_id=test_providers[country].id,
                meter_id=f"{country}-LIST-001",
                meter_type=MeterTypeEnum.DIGITAL
            )
            db_session.add(meter)
        
        db_session.commit()
        
        all_meters = db_session.query(Meter).all()
        assert len(all_meters) == 5
    
    def test_filter_by_country(self, db_session, test_users, test_providers):
        """Test filtering meters by country"""
        # Create meters
        for country in ["ES", "US", "IN"]:
            meter = Meter(
                user_id=test_users[country].id,
                utility_provider_id=test_providers[country].id,
                meter_id=f"{country}-FILTER-001",
                meter_type=MeterTypeEnum.DIGITAL
            )
            db_session.add(meter)
        
        db_session.commit()
        
        # Filter Spain meters
        spain_user = test_users["ES"]
        spain_meters = db_session.query(Meter).filter_by(user_id=spain_user.id).all()
        assert len(spain_meters) == 1
        assert spain_meters[0].meter_id == "ES-FILTER-001"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
