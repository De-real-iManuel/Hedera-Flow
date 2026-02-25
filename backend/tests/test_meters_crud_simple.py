"""
CRUD Tests for Meter Operations Across All 5 Regions
Tests US-2: Meter registration for Spain, USA, India, Brazil, Nigeria

Uses Docker PostgreSQL for testing (configured in conftest.py)
"""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.models.user import User, CountryCodeEnum
from app.models.meter import Meter, MeterTypeEnum
from app.models.utility_provider import UtilityProvider
from app.utils.auth import hash_password
import uuid


# Test data for all 5 regions
REGIONS = {
    "spain": {
        "country": CountryCodeEnum.ES,
        "provider_name": "Iberdrola",
        "provider_code": "IBE",
        "state_province": "Madrid",
        "meter_number": "ES123456789",
        "service_areas": ["Madrid", "Barcelona"]
    },
    "usa": {
        "country": CountryCodeEnum.US,
        "provider_name": "Pacific Gas & Electric",
        "provider_code": "PGE",
        "state_province": "California",
        "meter_number": "US987654321",
        "service_areas": ["California", "San Francisco"]
    },
    "india": {
        "country": CountryCodeEnum.IN,
        "provider_name": "Tata Power",
        "provider_code": "TATA",
        "state_province": "Maharashtra",
        "meter_number": "IN555666777",
        "service_areas": ["Mumbai", "Delhi"]
    },
    "brazil": {
        "country": CountryCodeEnum.BR,
        "provider_name": "Eletrobras",
        "provider_code": "ELE",
        "state_province": "São Paulo",
        "meter_number": "BR111222333",
        "service_areas": ["São Paulo", "Rio de Janeiro"]
    },
    "nigeria": {
        "country": CountryCodeEnum.NG,
        "provider_name": "Ikeja Electric",
        "provider_code": "IKEDP",
        "state_province": "Lagos",
        "meter_number": "NG444555666",
        "service_areas": ["Lagos", "Abuja"]
    }
}


def test_create_meters_all_regions(db_session):
    """Test creating meters for all 5 regions"""
    counter = 0
    for region_name, region_data in REGIONS.items():
        # Create user with unique hedera_account_id
        user = User(
            id=uuid.uuid4(),
            email=f"test_{region_name}@example.com",
            password_hash=hash_password("password123"),
            country_code=region_data["country"],
            hedera_account_id=f"0.0.TEST{counter}"
        )
        db_session.add(user)
        db_session.flush()
        
        # Create provider
        provider = UtilityProvider(
            id=uuid.uuid4(),
            provider_name=region_data["provider_name"],
            provider_code=region_data["provider_code"],
            country_code=region_data["country"].value,
            state_province=region_data["state_province"],
            service_areas=region_data["service_areas"],
            is_active=True
        )
        db_session.add(provider)
        db_session.flush()
        
        # Create meter
        meter = Meter(
            id=uuid.uuid4(),
            user_id=user.id,
            utility_provider_id=provider.id,
            meter_id=region_data["meter_number"],
            utility_provider=region_data["provider_name"],
            state_province=region_data["state_province"],
            meter_type=MeterTypeEnum.POSTPAID,
            is_primary=True
        )
        db_session.add(meter)
        counter += 1
    
    db_session.commit()
    
    # Verify all meters created
    meters = db_session.query(Meter).all()
    assert len(meters) == 5


def test_read_meters_by_region(db_session):
    """Test reading meters filtered by country"""
    # Create test data
    test_create_meters_all_regions(db_session)
    
    for region_name, region_data in REGIONS.items():
        users = db_session.query(User).filter(User.country_code == region_data["country"]).all()
        assert len(users) >= 1
        
        meters = db_session.query(Meter).filter(Meter.user_id.in_([u.id for u in users])).all()
        assert len(meters) >= 1


def test_update_meter(db_session):
    """Test updating meter information"""
    test_create_meters_all_regions(db_session)
    
    meter = db_session.query(Meter).first()
    original_id = meter.meter_id
    
    meter.meter_id = "UPDATED123"
    db_session.commit()
    
    updated_meter = db_session.query(Meter).filter(Meter.id == meter.id).first()
    assert updated_meter.meter_id == "UPDATED123"
    assert updated_meter.meter_id != original_id


def test_delete_meter(db_session):
    """Test deleting a meter"""
    test_create_meters_all_regions(db_session)
    
    initial_count = db_session.query(Meter).count()
    meter = db_session.query(Meter).first()
    
    db_session.delete(meter)
    db_session.commit()
    
    final_count = db_session.query(Meter).count()
    assert final_count == initial_count - 1
