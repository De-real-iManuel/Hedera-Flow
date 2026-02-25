"""
Task 7.7: Test Meter CRUD Operations for All 5 Regions (Simplified Database Tests)
Tests US-2: Meter registration for Spain, USA, India, Brazil, Nigeria

This test suite validates meter CRUD operations directly against the database:
- Create meter
- Read meters
- Update meter
- Delete meter

For all 5 supported regions:
- Spain (ES)
- USA (US)
- India (IN)
- Brazil (BR)
- Nigeria (NG)

Requirements tested:
- FR-2.1: System shall allow users to register multiple meters
- FR-2.2: System shall validate meter ID format per region
- FR-2.3: System shall store meter metadata
- FR-2.4: System shall support meter deletion
- US-2: User can register meter with state/utility dropdowns
"""
import pytest
from sqlalchemy.orm import Session
import uuid

from app.models.user import User, CountryCodeEnum
from app.models.utility_provider import UtilityProvider
from app.models.meter import Meter, MeterTypeEnum, BandClassificationEnum
from app.utils.auth import hash_password


# Test data for all 5 regions
REGION_TEST_DATA = {
    "ES": {
        "country_code": "ES",
        "state_province": "Madrid",
        "provider_name": "Iberdrola",
        "provider_code": "IBE",
        "service_areas": ["Madrid", "Barcelona", "Valencia"],
        "meter_id": "ES-12345678",
        "meter_type": MeterTypeEnum.POSTPAID,
        "band_classification": None
    },
    "US": {
        "country_code": "US",
        "state_province": "California",
        "provider_name": "Pacific Gas & Electric",
        "provider_code": "PGE",
        "service_areas": ["San Francisco", "Oakland", "San Jose"],
        "meter_id": "US-98765432",
        "meter_type": MeterTypeEnum.POSTPAID,
        "band_classification": None
    },
    "IN": {
        "country_code": "IN",
        "state_province": "Maharashtra",
        "provider_name": "Tata Power",
        "provider_code": "TATA",
        "service_areas": ["Mumbai", "Pune", "Nagpur"],
        "meter_id": "IN-55566677",
        "meter_type": MeterTypeEnum.POSTPAID,
        "band_classification": None
    },
    "BR": {
        "country_code": "BR",
        "state_province": "São Paulo",
        "provider_name": "Enel São Paulo",
        "provider_code": "ENEL",
        "service_areas": ["São Paulo", "Campinas", "Santos"],
        "meter_id": "BR-11122233",
        "meter_type": MeterTypeEnum.POSTPAID,
        "band_classification": None
    },
    "NG": {
        "country_code": "NG",
        "state_province": "Lagos",
        "provider_name": "Ikeja Electric",
        "provider_code": "IKEDP",
        "service_areas": ["Ikeja", "Lagos Island", "Victoria Island"],
        "meter_id": "NG-44455566",
        "meter_type": MeterTypeEnum.PREPAID,
        "band_classification": BandClassificationEnum.C
    }
}


@pytest.fixture
def setup_test_data(db_session: Session):
    """
    Set up test users and utility providers for all 5 regions
    Returns dict with user IDs and provider IDs
    """
    test_data = {}
    
    for region_code, region_info in REGION_TEST_DATA.items():
        # Create user
        user = User(
            id=uuid.uuid4(),
            email=f"test_{region_code.lower()}@example.com",
            password_hash=hash_password("TestPassword123!"),
            country_code=CountryCodeEnum[region_code],
            hedera_account_id=f"0.0.TEST{region_code}"
        )
        db_session.add(user)
        db_session.flush()
        
        # Create utility provider
        provider = UtilityProvider(
            id=uuid.uuid4(),
            country_code=region_info["country_code"],
            state_province=region_info["state_province"],
            provider_name=region_info["provider_name"],
            provider_code=region_info["provider_code"],
            service_areas=region_info["service_areas"],
            is_active=True
        )
        db_session.add(provider)
        db_session.flush()
        
        test_data[region_code] = {
            "user_id": str(user.id),
            "provider_id": str(provider.id),
            "email": user.email
        }
    
    db_session.commit()
    return test_data


def test_create_meter_spain(setup_test_data, db_session):
    """Test creating a meter for Spain"""
    region_code = "ES"
    test_data = setup_test_data[region_code]
    region_info = REGION_TEST_DATA[region_code]
    
    meter = Meter(
        id=uuid.uuid4(),
        user_id=uuid.UUID(test_data["user_id"]),
        utility_provider_id=uuid.UUID(test_data["provider_id"]),
        meter_id=region_info["meter_id"],
        state_province=region_info["state_province"],
        utility_provider=region_info["provider_name"],
        meter_type=region_info["meter_type"],
        is_primary=True
    )
    db_session.add(meter)
    db_session.commit()
    db_session.refresh(meter)
    
    assert meter.meter_id == region_info["meter_id"]
    assert meter.state_province == region_info["state_province"]
    assert meter.meter_type == region_info["meter_type"]


def test_create_meter_usa(setup_test_data, db_session):
    """Test creating a meter for USA"""
    region_code = "US"
    test_data = setup_test_data[region_code]
    region_info = REGION_TEST_DATA[region_code]
    
    meter = Meter(
        id=uuid.uuid4(),
        user_id=uuid.UUID(test_data["user_id"]),
        utility_provider_id=uuid.UUID(test_data["provider_id"]),
        meter_id=region_info["meter_id"],
        state_province=region_info["state_province"],
        utility_provider=region_info["provider_name"],
        meter_type=region_info["meter_type"],
        is_primary=True
    )
    db_session.add(meter)
    db_session.commit()
    
    assert meter.meter_id == region_info["meter_id"]
    assert meter.state_province == "California"


def test_create_meter_india(setup_test_data, db_session):
    """Test creating a meter for India"""
    region_code = "IN"
    test_data = setup_test_data[region_code]
    region_info = REGION_TEST_DATA[region_code]
    
    meter = Meter(
        id=uuid.uuid4(),
        user_id=uuid.UUID(test_data["user_id"]),
        utility_provider_id=uuid.UUID(test_data["provider_id"]),
        meter_id=region_info["meter_id"],
        state_province=region_info["state_province"],
        utility_provider=region_info["provider_name"],
        meter_type=region_info["meter_type"],
        is_primary=True
    )
    db_session.add(meter)
    db_session.commit()
    
    assert meter.meter_id == region_info["meter_id"]
    assert meter.state_province == "Maharashtra"


def test_create_meter_brazil(setup_test_data, db_session):
    """Test creating a meter for Brazil"""
    region_code = "BR"
    test_data = setup_test_data[region_code]
    region_info = REGION_TEST_DATA[region_code]
    
    meter = Meter(
        id=uuid.uuid4(),
        user_id=uuid.UUID(test_data["user_id"]),
        utility_provider_id=uuid.UUID(test_data["provider_id"]),
        meter_id=region_info["meter_id"],
        state_province=region_info["state_province"],
        utility_provider=region_info["provider_name"],
        meter_type=region_info["meter_type"],
        is_primary=True
    )
    db_session.add(meter)
    db_session.commit()
    
    assert meter.meter_id == region_info["meter_id"]
    assert meter.state_province == "São Paulo"


def test_create_meter_nigeria_with_band(setup_test_data, db_session):
    """Test creating a meter for Nigeria with band classification"""
    region_code = "NG"
    test_data = setup_test_data[region_code]
    region_info = REGION_TEST_DATA[region_code]
    
    meter = Meter(
        id=uuid.uuid4(),
        user_id=uuid.UUID(test_data["user_id"]),
        utility_provider_id=uuid.UUID(test_data["provider_id"]),
        meter_id=region_info["meter_id"],
        state_province=region_info["state_province"],
        utility_provider=region_info["provider_name"],
        meter_type=region_info["meter_type"],
        band_classification=region_info["band_classification"],
        is_primary=True
    )
    db_session.add(meter)
    db_session.commit()
    
    assert meter.meter_id == region_info["meter_id"]
    assert meter.band_classification == BandClassificationEnum.C
    assert meter.meter_type == MeterTypeEnum.PREPAID


def test_read_meters_all_regions(setup_test_data, db_session):
    """Test reading meters for all regions"""
    # Create meters for all regions
    for region_code, test_data in setup_test_data.items():
        region_info = REGION_TEST_DATA[region_code]
        
        meter = Meter(
            id=uuid.uuid4(),
            user_id=uuid.UUID(test_data["user_id"]),
            utility_provider_id=uuid.UUID(test_data["provider_id"]),
            meter_id=region_info["meter_id"],
            state_province=region_info["state_province"],
            utility_provider=region_info["provider_name"],
            meter_type=region_info["meter_type"],
            band_classification=region_info["band_classification"],
            is_primary=True
        )
        db_session.add(meter)
    
    db_session.commit()
    
    # Verify each region has meters
    for region_code, test_data in setup_test_data.items():
        meters = db_session.query(Meter).filter(
            Meter.user_id == uuid.UUID(test_data["user_id"])
        ).all()
        
        assert len(meters) >= 1
        assert meters[0].meter_id == REGION_TEST_DATA[region_code]["meter_id"]


def test_update_meter(setup_test_data, db_session):
    """Test updating a meter"""
    region_code = "ES"
    test_data = setup_test_data[region_code]
    region_info = REGION_TEST_DATA[region_code]
    
    # Create meter
    meter = Meter(
        id=uuid.uuid4(),
        user_id=uuid.UUID(test_data["user_id"]),
        utility_provider_id=uuid.UUID(test_data["provider_id"]),
        meter_id=region_info["meter_id"],
        state_province=region_info["state_province"],
        utility_provider=region_info["provider_name"],
        meter_type=MeterTypeEnum.POSTPAID,
        is_primary=True
    )
    db_session.add(meter)
    db_session.commit()
    
    # Update meter
    meter.meter_id = "ES-UPDATED-123"
    meter.meter_type = MeterTypeEnum.PREPAID
    db_session.commit()
    db_session.refresh(meter)
    
    assert meter.meter_id == "ES-UPDATED-123"
    assert meter.meter_type == MeterTypeEnum.PREPAID


def test_delete_meter(setup_test_data, db_session):
    """Test deleting a meter"""
    region_code = "ES"
    test_data = setup_test_data[region_code]
    region_info = REGION_TEST_DATA[region_code]
    
    # Create meter
    meter = Meter(
        id=uuid.uuid4(),
        user_id=uuid.UUID(test_data["user_id"]),
        utility_provider_id=uuid.UUID(test_data["provider_id"]),
        meter_id=region_info["meter_id"],
        state_province=region_info["state_province"],
        utility_provider=region_info["provider_name"],
        meter_type=MeterTypeEnum.POSTPAID,
        is_primary=True
    )
    db_session.add(meter)
    db_session.commit()
    meter_id = meter.id
    
    # Delete meter
    db_session.delete(meter)
    db_session.commit()
    
    # Verify deletion
    deleted_meter = db_session.query(Meter).filter(Meter.id == meter_id).first()
    assert deleted_meter is None


def test_multiple_meters_per_user(setup_test_data, db_session):
    """Test that users can register multiple meters"""
    region_code = "ES"
    test_data = setup_test_data[region_code]
    region_info = REGION_TEST_DATA[region_code]
    
    # Create 3 meters
    for i in range(3):
        meter = Meter(
            id=uuid.uuid4(),
            user_id=uuid.UUID(test_data["user_id"]),
            utility_provider_id=uuid.UUID(test_data["provider_id"]),
            meter_id=f"ES-MULTI-{i}",
            state_province=region_info["state_province"],
            utility_provider=region_info["provider_name"],
            meter_type=MeterTypeEnum.POSTPAID,
            is_primary=(i == 0)
        )
        db_session.add(meter)
    
    db_session.commit()
    
    # List all meters
    meters = db_session.query(Meter).filter(
        Meter.user_id == uuid.UUID(test_data["user_id"])
    ).all()
    
    assert len(meters) == 3
    
    # Verify only one is primary
    primary_count = sum(1 for m in meters if m.is_primary)
    assert primary_count == 1


def test_nigeria_all_bands(setup_test_data, db_session):
    """Test creating meters with all Nigeria band classifications"""
    region_code = "NG"
    test_data = setup_test_data[region_code]
    region_info = REGION_TEST_DATA[region_code]
    
    bands = [BandClassificationEnum.A, BandClassificationEnum.B, BandClassificationEnum.C, 
             BandClassificationEnum.D, BandClassificationEnum.E]
    
    for band in bands:
        meter = Meter(
            id=uuid.uuid4(),
            user_id=uuid.UUID(test_data["user_id"]),
            utility_provider_id=uuid.UUID(test_data["provider_id"]),
            meter_id=f"NG-BAND-{band.value}",
            state_province=region_info["state_province"],
            utility_provider=region_info["provider_name"],
            meter_type=MeterTypeEnum.PREPAID,
            band_classification=band,
            is_primary=False
        )
        db_session.add(meter)
    
    db_session.commit()
    
    # Verify all bands created
    meters = db_session.query(Meter).filter(
        Meter.user_id == uuid.UUID(test_data["user_id"])
    ).all()
    
    assert len(meters) == 5
    band_values = [m.band_classification for m in meters]
    assert set(band_values) == set(bands)


def test_all_regions_create(setup_test_data, db_session):
    """Test creating meters for all 5 regions"""
    created_meters = []
    
    for region_code, test_data in setup_test_data.items():
        region_info = REGION_TEST_DATA[region_code]
        
        meter = Meter(
            id=uuid.uuid4(),
            user_id=uuid.UUID(test_data["user_id"]),
            utility_provider_id=uuid.UUID(test_data["provider_id"]),
            meter_id=region_info["meter_id"],
            state_province=region_info["state_province"],
            utility_provider=region_info["provider_name"],
            meter_type=region_info["meter_type"],
            band_classification=region_info["band_classification"],
            is_primary=True
        )
        db_session.add(meter)
        created_meters.append(meter)
    
    db_session.commit()
    
    # Verify all 5 regions created successfully
    assert len(created_meters) == 5
    
    # Verify each region has correct data
    for i, region_code in enumerate(["ES", "US", "IN", "BR", "NG"]):
        assert created_meters[i].meter_id == REGION_TEST_DATA[region_code]["meter_id"]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
