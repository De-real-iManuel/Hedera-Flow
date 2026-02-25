"""
Task 7.7: Test Meter CRUD Operations for All 5 Regions
Tests US-2: Meter registration for Spain, USA, India, Brazil, Nigeria

This test suite validates:
- Create meter (POST /api/meters)
- Read meters (GET /api/meters)
- Read single meter (GET /api/meters/{id})
- Update meter (PUT /api/meters/{id})
- Delete meter (DELETE /api/meters/{id})

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
- FR-2.4: System shall support meter deletion (soft delete)
- US-2: User can register meter with state/utility dropdowns
"""
import pytest
from sqlalchemy.orm import Session
import uuid

from app.models.user import User, CountryCodeEnum
from app.models.utility_provider import UtilityProvider
from app.models.meter import Meter, MeterTypeEnum, BandClassificationEnum
from app.utils.auth import hash_password, create_jwt_token


# Test data for all 5 regions
REGION_TEST_DATA = {
    "ES": {
        "country_code": "ES",
        "state_province": "Madrid",
        "provider_name": "Iberdrola",
        "provider_code": "IBE",
        "service_areas": ["Madrid", "Barcelona", "Valencia"],
        "meter_id": "ES-12345678",
        "meter_type": "postpaid",
        "band_classification": None
    },
    "US": {
        "country_code": "US",
        "state_province": "California",
        "provider_name": "Pacific Gas & Electric",
        "provider_code": "PGE",
        "service_areas": ["San Francisco", "Oakland", "San Jose"],
        "meter_id": "US-98765432",
        "meter_type": "postpaid",
        "band_classification": None
    },
    "IN": {
        "country_code": "IN",
        "state_province": "Maharashtra",
        "provider_name": "Tata Power",
        "provider_code": "TATA",
        "service_areas": ["Mumbai", "Pune", "Nagpur"],
        "meter_id": "IN-55566677",
        "meter_type": "postpaid",
        "band_classification": None
    },
    "BR": {
        "country_code": "BR",
        "state_province": "São Paulo",
        "provider_name": "Enel São Paulo",
        "provider_code": "ENEL",
        "service_areas": ["São Paulo", "Campinas", "Santos"],
        "meter_id": "BR-11122233",
        "meter_type": "postpaid",
        "band_classification": None
    },
    "NG": {
        "country_code": "NG",
        "state_province": "Lagos",
        "provider_name": "Ikeja Electric",
        "provider_code": "IKEDP",
        "service_areas": ["Ikeja", "Lagos Island", "Victoria Island"],
        "meter_id": "NG-44455566",
        "meter_type": "prepaid",
        "band_classification": "C"  # Nigeria requires band classification
    }
}


@pytest.fixture
def setup_test_data(db_session: Session):
    """
    Set up test users and utility providers for all 5 regions
    Returns dict with user tokens and provider IDs
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
        
        # Generate JWT token
        token = create_jwt_token(user.id, user.email)
        
        test_data[region_code] = {
            "user_id": str(user.id),
            "token": token,
            "provider_id": str(provider.id),
            "email": user.email
        }
    
    db_session.commit()
    return test_data


class TestMeterCRUDSpain:
    """Test meter CRUD operations for Spain (ES)"""
    
    def test_create_meter_spain(self, setup_test_data, db_session):
        """Test creating a meter for Spain"""
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
        db_session.refresh(meter)
        
        # Verify
        assert meter.meter_id == region_info["meter_id"]
        assert meter.state_province == region_info["state_province"]
        assert meter.meter_type == MeterTypeEnum.POSTPAID
        assert meter.is_primary is True
    
    def test_read_meters_spain(self, setup_test_data, db_session):
        """Test reading meters for Spain"""
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
        
        # Read meters
        meters = db_session.query(Meter).filter(
            Meter.user_id == uuid.UUID(test_data["user_id"])
        ).all()
        
        assert len(meters) >= 1
        assert meters[0].meter_id == region_info["meter_id"]
    
    def test_update_meter_spain(self, setup_test_data, db_session):
        """Test updating a meter for Spain"""
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
    
    def test_delete_meter_spain(self, setup_test_data, db_session):
        """Test deleting a meter for Spain"""
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


class TestMeterCRUDUSA:
    """Test meter CRUD operations for USA (US)"""
    
    def test_create_meter_usa(self, setup_test_data):
        """Test creating a meter for USA"""
        region_code = "US"
        test_data = setup_test_data[region_code]
        region_info = REGION_TEST_DATA[region_code]
        
        meter_data = {
            "meter_id": region_info["meter_id"],
            "utility_provider_id": test_data["provider_id"],
            "state_province": region_info["state_province"],
            "utility_provider": region_info["provider_name"],
            "meter_type": region_info["meter_type"],
            "is_primary": True
        }
        
        response = client.post(
            "/api/meters",
            json=meter_data,
            headers={"Authorization": f"Bearer {test_data['token']}"}
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["meter_id"] == region_info["meter_id"]
        assert data["state_province"] == "California"
    
    def test_crud_full_cycle_usa(self, setup_test_data):
        """Test full CRUD cycle for USA"""
        region_code = "US"
        test_data = setup_test_data[region_code]
        region_info = REGION_TEST_DATA[region_code]
        
        # CREATE
        create_response = client.post(
            "/api/meters",
            json={
                "meter_id": region_info["meter_id"],
                "utility_provider_id": test_data["provider_id"],
                "state_province": region_info["state_province"],
                "utility_provider": region_info["provider_name"],
                "meter_type": "postpaid",
                "is_primary": True
            },
            headers={"Authorization": f"Bearer {test_data['token']}"}
        )
        assert create_response.status_code == 201
        meter_id = create_response.json()["id"]
        
        # READ
        read_response = client.get(
            f"/api/meters/{meter_id}",
            headers={"Authorization": f"Bearer {test_data['token']}"}
        )
        assert read_response.status_code == 200
        assert read_response.json()["meter_id"] == region_info["meter_id"]
        
        # UPDATE
        update_response = client.put(
            f"/api/meters/{meter_id}",
            json={
                "meter_id": "US-UPDATED",
                "utility_provider_id": test_data["provider_id"],
                "state_province": region_info["state_province"],
                "utility_provider": region_info["provider_name"],
                "meter_type": "prepaid",
                "is_primary": False
            },
            headers={"Authorization": f"Bearer {test_data['token']}"}
        )
        assert update_response.status_code == 200
        assert update_response.json()["meter_id"] == "US-UPDATED"
        
        # DELETE
        delete_response = client.delete(
            f"/api/meters/{meter_id}",
            headers={"Authorization": f"Bearer {test_data['token']}"}
        )
        assert delete_response.status_code == 204


class TestMeterCRUDIndia:
    """Test meter CRUD operations for India (IN)"""
    
    def test_create_meter_india(self, setup_test_data):
        """Test creating a meter for India"""
        region_code = "IN"
        test_data = setup_test_data[region_code]
        region_info = REGION_TEST_DATA[region_code]
        
        meter_data = {
            "meter_id": region_info["meter_id"],
            "utility_provider_id": test_data["provider_id"],
            "state_province": region_info["state_province"],
            "utility_provider": region_info["provider_name"],
            "meter_type": region_info["meter_type"],
            "is_primary": True
        }
        
        response = client.post(
            "/api/meters",
            json=meter_data,
            headers={"Authorization": f"Bearer {test_data['token']}"}
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["meter_id"] == region_info["meter_id"]
        assert data["state_province"] == "Maharashtra"
    
    def test_list_meters_india(self, setup_test_data):
        """Test listing meters for India"""
        region_code = "IN"
        test_data = setup_test_data[region_code]
        
        # Create multiple meters
        for i in range(3):
            client.post(
                "/api/meters",
                json={
                    "meter_id": f"IN-METER-{i}",
                    "utility_provider_id": test_data["provider_id"],
                    "state_province": REGION_TEST_DATA[region_code]["state_province"],
                    "utility_provider": REGION_TEST_DATA[region_code]["provider_name"],
                    "meter_type": "postpaid",
                    "is_primary": (i == 0)
                },
                headers={"Authorization": f"Bearer {test_data['token']}"}
            )
        
        # List all meters
        response = client.get(
            "/api/meters",
            headers={"Authorization": f"Bearer {test_data['token']}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        # Primary meter should be first
        assert data[0]["is_primary"] is True


class TestMeterCRUDBrazil:
    """Test meter CRUD operations for Brazil (BR)"""
    
    def test_create_meter_brazil(self, setup_test_data):
        """Test creating a meter for Brazil"""
        region_code = "BR"
        test_data = setup_test_data[region_code]
        region_info = REGION_TEST_DATA[region_code]
        
        meter_data = {
            "meter_id": region_info["meter_id"],
            "utility_provider_id": test_data["provider_id"],
            "state_province": region_info["state_province"],
            "utility_provider": region_info["provider_name"],
            "meter_type": region_info["meter_type"],
            "is_primary": True
        }
        
        response = client.post(
            "/api/meters",
            json=meter_data,
            headers={"Authorization": f"Bearer {test_data['token']}"}
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["meter_id"] == region_info["meter_id"]
        assert data["state_province"] == "São Paulo"
    
    def test_update_and_verify_brazil(self, setup_test_data):
        """Test update and verify for Brazil"""
        region_code = "BR"
        test_data = setup_test_data[region_code]
        region_info = REGION_TEST_DATA[region_code]
        
        # Create
        create_response = client.post(
            "/api/meters",
            json={
                "meter_id": region_info["meter_id"],
                "utility_provider_id": test_data["provider_id"],
                "state_province": region_info["state_province"],
                "utility_provider": region_info["provider_name"],
                "meter_type": "postpaid",
                "address": "Rua Example, 123",
                "is_primary": True
            },
            headers={"Authorization": f"Bearer {test_data['token']}"}
        )
        meter_id = create_response.json()["id"]
        
        # Update address
        update_response = client.put(
            f"/api/meters/{meter_id}",
            json={
                "meter_id": region_info["meter_id"],
                "utility_provider_id": test_data["provider_id"],
                "state_province": region_info["state_province"],
                "utility_provider": region_info["provider_name"],
                "meter_type": "postpaid",
                "address": "Avenida Updated, 456",
                "is_primary": True
            },
            headers={"Authorization": f"Bearer {test_data['token']}"}
        )
        
        assert update_response.status_code == 200
        assert update_response.json()["address"] == "Avenida Updated, 456"


class TestMeterCRUDNigeria:
    """Test meter CRUD operations for Nigeria (NG)"""
    
    def test_create_meter_nigeria_with_band(self, setup_test_data):
        """Test creating a meter for Nigeria with band classification"""
        region_code = "NG"
        test_data = setup_test_data[region_code]
        region_info = REGION_TEST_DATA[region_code]
        
        meter_data = {
            "meter_id": region_info["meter_id"],
            "utility_provider_id": test_data["provider_id"],
            "state_province": region_info["state_province"],
            "utility_provider": region_info["provider_name"],
            "meter_type": region_info["meter_type"],
            "band_classification": region_info["band_classification"],
            "is_primary": True
        }
        
        response = client.post(
            "/api/meters",
            json=meter_data,
            headers={"Authorization": f"Bearer {test_data['token']}"}
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["meter_id"] == region_info["meter_id"]
        assert data["band_classification"] == "C"
        assert data["meter_type"] == "prepaid"
    
    def test_nigeria_band_classification_required(self, setup_test_data):
        """Test that Nigeria requires band classification"""
        region_code = "NG"
        test_data = setup_test_data[region_code]
        region_info = REGION_TEST_DATA[region_code]
        
        # Try to create without band classification
        meter_data = {
            "meter_id": region_info["meter_id"],
            "utility_provider_id": test_data["provider_id"],
            "state_province": region_info["state_province"],
            "utility_provider": region_info["provider_name"],
            "meter_type": "prepaid",
            "is_primary": True
            # Missing band_classification
        }
        
        response = client.post(
            "/api/meters",
            json=meter_data,
            headers={"Authorization": f"Bearer {test_data['token']}"}
        )
        
        # Should fail validation
        assert response.status_code == 400
        assert "band classification" in response.json()["detail"].lower()
    
    def test_nigeria_all_bands(self, setup_test_data):
        """Test creating meters with all Nigeria band classifications"""
        region_code = "NG"
        test_data = setup_test_data[region_code]
        region_info = REGION_TEST_DATA[region_code]
        
        bands = ["A", "B", "C", "D", "E"]
        
        for band in bands:
            meter_data = {
                "meter_id": f"NG-BAND-{band}",
                "utility_provider_id": test_data["provider_id"],
                "state_province": region_info["state_province"],
                "utility_provider": region_info["provider_name"],
                "meter_type": "prepaid",
                "band_classification": band,
                "is_primary": False
            }
            
            response = client.post(
                "/api/meters",
                json=meter_data,
                headers={"Authorization": f"Bearer {test_data['token']}"}
            )
            
            assert response.status_code == 201
            assert response.json()["band_classification"] == band


class TestMeterCRUDCrossRegion:
    """Test cross-region meter operations"""
    
    def test_all_regions_create(self, setup_test_data):
        """Test creating meters for all 5 regions"""
        created_meters = []
        
        for region_code, test_data in setup_test_data.items():
            region_info = REGION_TEST_DATA[region_code]
            
            meter_data = {
                "meter_id": region_info["meter_id"],
                "utility_provider_id": test_data["provider_id"],
                "state_province": region_info["state_province"],
                "utility_provider": region_info["provider_name"],
                "meter_type": region_info["meter_type"],
                "is_primary": True
            }
            
            # Add band classification for Nigeria
            if region_code == "NG":
                meter_data["band_classification"] = region_info["band_classification"]
            
            response = client.post(
                "/api/meters",
                json=meter_data,
                headers={"Authorization": f"Bearer {test_data['token']}"}
            )
            
            assert response.status_code == 201
            created_meters.append(response.json())
        
        # Verify all 5 regions created successfully
        assert len(created_meters) == 5
        
        # Verify each region has correct data
        for i, region_code in enumerate(["ES", "US", "IN", "BR", "NG"]):
            assert created_meters[i]["meter_id"] == REGION_TEST_DATA[region_code]["meter_id"]
    
    def test_user_cannot_access_other_user_meters(self, setup_test_data):
        """Test that users can only access their own meters"""
        # Create meter for Spain user
        es_data = setup_test_data["ES"]
        es_info = REGION_TEST_DATA["ES"]
        
        create_response = client.post(
            "/api/meters",
            json={
                "meter_id": es_info["meter_id"],
                "utility_provider_id": es_data["provider_id"],
                "state_province": es_info["state_province"],
                "utility_provider": es_info["provider_name"],
                "meter_type": "postpaid",
                "is_primary": True
            },
            headers={"Authorization": f"Bearer {es_data['token']}"}
        )
        meter_id = create_response.json()["id"]
        
        # Try to access with USA user token
        us_data = setup_test_data["US"]
        response = client.get(
            f"/api/meters/{meter_id}",
            headers={"Authorization": f"Bearer {us_data['token']}"}
        )
        
        # Should return 404 (not found for this user)
        assert response.status_code == 404
    
    def test_multiple_meters_per_user(self, setup_test_data):
        """Test that users can register multiple meters"""
        region_code = "ES"
        test_data = setup_test_data[region_code]
        region_info = REGION_TEST_DATA[region_code]
        
        # Create 3 meters
        for i in range(3):
            meter_data = {
                "meter_id": f"ES-MULTI-{i}",
                "utility_provider_id": test_data["provider_id"],
                "state_province": region_info["state_province"],
                "utility_provider": region_info["provider_name"],
                "meter_type": "postpaid",
                "is_primary": (i == 0)
            }
            
            response = client.post(
                "/api/meters",
                json=meter_data,
                headers={"Authorization": f"Bearer {test_data['token']}"}
            )
            assert response.status_code == 201
        
        # List all meters
        list_response = client.get(
            "/api/meters",
            headers={"Authorization": f"Bearer {test_data['token']}"}
        )
        
        assert list_response.status_code == 200
        meters = list_response.json()
        assert len(meters) == 3
        
        # Verify only one is primary
        primary_count = sum(1 for m in meters if m["is_primary"])
        assert primary_count == 1


class TestMeterValidation:
    """Test meter validation rules"""
    
    def test_duplicate_meter_id_rejected(self, setup_test_data):
        """Test that duplicate meter IDs are rejected"""
        region_code = "ES"
        test_data = setup_test_data[region_code]
        region_info = REGION_TEST_DATA[region_code]
        
        meter_data = {
            "meter_id": region_info["meter_id"],
            "utility_provider_id": test_data["provider_id"],
            "state_province": region_info["state_province"],
            "utility_provider": region_info["provider_name"],
            "meter_type": "postpaid",
            "is_primary": True
        }
        
        # Create first meter
        response1 = client.post(
            "/api/meters",
            json=meter_data,
            headers={"Authorization": f"Bearer {test_data['token']}"}
        )
        assert response1.status_code == 201
        
        # Try to create duplicate
        response2 = client.post(
            "/api/meters",
            json=meter_data,
            headers={"Authorization": f"Bearer {test_data['token']}"}
        )
        assert response2.status_code == 409  # Conflict
    
    def test_invalid_utility_provider_rejected(self, setup_test_data):
        """Test that invalid utility provider ID is rejected"""
        region_code = "ES"
        test_data = setup_test_data[region_code]
        region_info = REGION_TEST_DATA[region_code]
        
        meter_data = {
            "meter_id": region_info["meter_id"],
            "utility_provider_id": "00000000-0000-0000-0000-000000000000",  # Invalid
            "state_province": region_info["state_province"],
            "utility_provider": region_info["provider_name"],
            "meter_type": "postpaid",
            "is_primary": True
        }
        
        response = client.post(
            "/api/meters",
            json=meter_data,
            headers={"Authorization": f"Bearer {test_data['token']}"}
        )
        
        assert response.status_code == 404  # Provider not found


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
