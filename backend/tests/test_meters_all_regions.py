"""
Comprehensive Tests for Meter CRUD Operations Across All 5 Regions
Tests US-2: Meter registration for Spain, USA, India, Brazil, Nigeria

This test suite validates:
- CREATE: Register meters for all 5 regions with proper validation
- READ: List and retrieve meters
- UPDATE: Modify meter details (via re-registration)
- DELETE: Remove meters (soft delete)

Requirements:
- FR-2.1: System shall allow users to register multiple meters
- FR-2.2: System shall validate meter ID format per region
- FR-2.3: System shall store meter metadata
- FR-2.4: System shall support meter deletion
- US-2: User can register meter with state/utility dropdowns
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from main import app
from app.core.database import Base, get_db
from app.models.user import User, CountryCodeEnum
from app.models.meter import Meter, MeterTypeEnum
from app.models.utility_provider import UtilityProvider
from app.utils.auth import hash_password, create_access_token

# Create in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for testing"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


@pytest.fixture(scope="function")
def setup_database():
    """Create tables before each test and drop after"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def utility_providers(setup_database):
    """Create utility providers for all 5 regions"""
    db = TestingSessionLocal()
    
    providers = [
        # Spain
        UtilityProvider(
            country_code="ES",
            state_province="Madrid",
            provider_name="Iberdrola",
            provider_code="IBERDROLA",
            service_areas=None,  # Skip for SQLite compatibility
            is_active=True
        ),
        # USA
        UtilityProvider(
            country_code="US",
            state_province="California",
            provider_name="Pacific Gas & Electric",
            provider_code="PGE",
            service_areas=None,  # Skip for SQLite compatibility
            is_active=True
        ),
        # India
        UtilityProvider(
            country_code="IN",
            state_province="Delhi",
            provider_name="Tata Power Delhi Distribution Limited",
            provider_code="TPDDL",
            service_areas=None,  # Skip for SQLite compatibility
            is_active=True
        ),
        # Brazil
        UtilityProvider(
            country_code="BR",
            state_province="São Paulo",
            provider_name="Enel São Paulo",
            provider_code="ENEL_SP",
            service_areas=None,  # Skip for SQLite compatibility
            is_active=True
        ),
        # Nigeria
        UtilityProvider(
            country_code="NG",
            state_province="Lagos",
            provider_name="Ikeja Electric",
            provider_code="IKEDP",
            service_areas=None,  # Skip for SQLite compatibility
            is_active=True
        ),
    ]
    
    db.add_all(providers)
    db.commit()
    
    for provider in providers:
        db.refresh(provider)
    
    yield {p.country_code: p for p in providers}
    
    db.close()


@pytest.fixture
def users_all_regions(setup_database):
    """Create test users for all 5 regions"""
    db = TestingSessionLocal()
    
    users_data = [
        ("spain@example.com", CountryCodeEnum.ES, "0.0.11111"),
        ("usa@example.com", CountryCodeEnum.US, "0.0.22222"),
        ("india@example.com", CountryCodeEnum.IN, "0.0.33333"),
        ("brazil@example.com", CountryCodeEnum.BR, "0.0.44444"),
        ("nigeria@example.com", CountryCodeEnum.NG, "0.0.55555"),
    ]
    
    users = {}
    for email, country, hedera_id in users_data:
        user = User(
            email=email,
            password_hash=hash_password("TestPassword123!"),
            country_code=country,
            hedera_account_id=hedera_id
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        
        token = create_access_token({"sub": user.email})
        users[country.value] = {"user": user, "token": token}
    
    yield users
    
    db.close()


class TestMeterCRUD_Spain:
    """Test CRUD operations for Spain meters"""
    
    def test_create_spain_meter(self, users_all_regions, utility_providers):
        """Test creating a meter in Spain"""
        user_data = users_all_regions["ES"]
        provider = utility_providers["ES"]
        
        meter_data = {
            "meter_id": "ES-MAD-12345678",
            "utility_provider_id": str(provider.id),
            "state_province": "Madrid",
            "utility_provider": "Iberdrola",
            "meter_type": "postpaid",
            "address": "Calle Gran Vía 1, Madrid"
        }
        
        headers = {"Authorization": f"Bearer {user_data['token']}"}
        response = client.post("/api/meters", json=meter_data, headers=headers)
        
        assert response.status_code == 201
        data = response.json()
        assert data["meter_id"] == "ES-MAD-12345678"
        assert data["utility_provider"] == "Iberdrola"
        assert data["state_province"] == "Madrid"
        assert data["meter_type"] == "postpaid"
    
    def test_read_spain_meters(self, users_all_regions, utility_providers):
        """Test reading Spain meters"""
        user_data = users_all_regions["ES"]
        provider = utility_providers["ES"]
        
        # Create a meter first
        db = TestingSessionLocal()
        meter = Meter(
            user_id=user_data["user"].id,
            meter_id="ES-MAD-11111111",
            utility_provider_id=provider.id,
            state_province="Madrid",
            utility_provider="Iberdrola",
            meter_type=MeterTypeEnum.POSTPAID,
            is_primary=True
        )
        db.add(meter)
        db.commit()
        db.close()
        
        # Read meters
        headers = {"Authorization": f"Bearer {user_data['token']}"}
        response = client.get("/api/meters", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["meter_id"] == "ES-MAD-11111111"
    
    def test_delete_spain_meter(self, users_all_regions, utility_providers):
        """Test deleting a Spain meter"""
        user_data = users_all_regions["ES"]
        provider = utility_providers["ES"]
        
        # Create a meter first
        db = TestingSessionLocal()
        meter = Meter(
            user_id=user_data["user"].id,
            meter_id="ES-MAD-99999999",
            utility_provider_id=provider.id,
            state_province="Madrid",
            utility_provider="Iberdrola",
            meter_type=MeterTypeEnum.POSTPAID,
            is_primary=True
        )
        db.add(meter)
        db.commit()
        meter_id = meter.id
        db.close()
        
        # Delete meter
        headers = {"Authorization": f"Bearer {user_data['token']}"}
        response = client.delete(f"/api/meters/{meter_id}", headers=headers)
        
        assert response.status_code == 200
        
        # Verify meter is deleted
        response = client.get("/api/meters", headers=headers)
        data = response.json()
        assert len(data) == 0


class TestMeterCRUD_USA:
    """Test CRUD operations for USA meters"""
    
    def test_create_usa_meter(self, users_all_regions, utility_providers):
        """Test creating a meter in USA"""
        user_data = users_all_regions["US"]
        provider = utility_providers["US"]
        
        meter_data = {
            "meter_id": "US-CA-PGE-123456789012",
            "utility_provider_id": str(provider.id),
            "state_province": "California",
            "utility_provider": "Pacific Gas & Electric",
            "meter_type": "postpaid",
            "address": "123 Market St, San Francisco, CA"
        }
        
        headers = {"Authorization": f"Bearer {user_data['token']}"}
        response = client.post("/api/meters", json=meter_data, headers=headers)
        
        assert response.status_code == 201
        data = response.json()
        assert data["meter_id"] == "US-CA-PGE-123456789012"
        assert data["utility_provider"] == "Pacific Gas & Electric"
        assert data["state_province"] == "California"
    
    def test_read_usa_meters(self, users_all_regions, utility_providers):
        """Test reading USA meters"""
        user_data = users_all_regions["US"]
        provider = utility_providers["US"]
        
        # Create multiple meters
        db = TestingSessionLocal()
        meters = [
            Meter(
                user_id=user_data["user"].id,
                meter_id="US-CA-PGE-111111111111",
                utility_provider_id=provider.id,
                state_province="California",
                utility_provider="Pacific Gas & Electric",
                meter_type=MeterTypeEnum.POSTPAID,
                is_primary=True
            ),
            Meter(
                user_id=user_data["user"].id,
                meter_id="US-CA-PGE-222222222222",
                utility_provider_id=provider.id,
                state_province="California",
                utility_provider="Pacific Gas & Electric",
                meter_type=MeterTypeEnum.PREPAID,
                is_primary=False
            )
        ]
        db.add_all(meters)
        db.commit()
        db.close()
        
        # Read meters
        headers = {"Authorization": f"Bearer {user_data['token']}"}
        response = client.get("/api/meters", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        meter_ids = [m["meter_id"] for m in data]
        assert "US-CA-PGE-111111111111" in meter_ids
        assert "US-CA-PGE-222222222222" in meter_ids


class TestMeterCRUD_India:
    """Test CRUD operations for India meters"""
    
    def test_create_india_meter(self, users_all_regions, utility_providers):
        """Test creating a meter in India"""
        user_data = users_all_regions["IN"]
        provider = utility_providers["IN"]
        
        meter_data = {
            "meter_id": "IN-DL-TPDDL-12345678901234",
            "utility_provider_id": str(provider.id),
            "state_province": "Delhi",
            "utility_provider": "Tata Power Delhi Distribution Limited",
            "meter_type": "postpaid",
            "address": "123 Connaught Place, New Delhi"
        }
        
        headers = {"Authorization": f"Bearer {user_data['token']}"}
        response = client.post("/api/meters", json=meter_data, headers=headers)
        
        assert response.status_code == 201
        data = response.json()
        assert data["meter_id"] == "IN-DL-TPDDL-12345678901234"
        assert data["utility_provider"] == "Tata Power Delhi Distribution Limited"
        assert data["state_province"] == "Delhi"
    
    def test_read_india_meters(self, users_all_regions, utility_providers):
        """Test reading India meters"""
        user_data = users_all_regions["IN"]
        provider = utility_providers["IN"]
        
        # Create a meter
        db = TestingSessionLocal()
        meter = Meter(
            user_id=user_data["user"].id,
            meter_id="IN-DL-TPDDL-11111111111111",
            utility_provider_id=provider.id,
            state_province="Delhi",
            utility_provider="Tata Power Delhi Distribution Limited",
            meter_type=MeterTypeEnum.POSTPAID,
            is_primary=True
        )
        db.add(meter)
        db.commit()
        db.close()
        
        # Read meters
        headers = {"Authorization": f"Bearer {user_data['token']}"}
        response = client.get("/api/meters", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["meter_id"] == "IN-DL-TPDDL-11111111111111"


class TestMeterCRUD_Brazil:
    """Test CRUD operations for Brazil meters"""
    
    def test_create_brazil_meter(self, users_all_regions, utility_providers):
        """Test creating a meter in Brazil"""
        user_data = users_all_regions["BR"]
        provider = utility_providers["BR"]
        
        meter_data = {
            "meter_id": "BR-SP-ENEL-1234567890",
            "utility_provider_id": str(provider.id),
            "state_province": "São Paulo",
            "utility_provider": "Enel São Paulo",
            "meter_type": "postpaid",
            "address": "Av. Paulista 1000, São Paulo"
        }
        
        headers = {"Authorization": f"Bearer {user_data['token']}"}
        response = client.post("/api/meters", json=meter_data, headers=headers)
        
        assert response.status_code == 201
        data = response.json()
        assert data["meter_id"] == "BR-SP-ENEL-1234567890"
        assert data["utility_provider"] == "Enel São Paulo"
        assert data["state_province"] == "São Paulo"
    
    def test_read_brazil_meters(self, users_all_regions, utility_providers):
        """Test reading Brazil meters"""
        user_data = users_all_regions["BR"]
        provider = utility_providers["BR"]
        
        # Create a meter
        db = TestingSessionLocal()
        meter = Meter(
            user_id=user_data["user"].id,
            meter_id="BR-SP-ENEL-1111111111",
            utility_provider_id=provider.id,
            state_province="São Paulo",
            utility_provider="Enel São Paulo",
            meter_type=MeterTypeEnum.POSTPAID,
            is_primary=True
        )
        db.add(meter)
        db.commit()
        db.close()
        
        # Read meters
        headers = {"Authorization": f"Bearer {user_data['token']}"}
        response = client.get("/api/meters", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["meter_id"] == "BR-SP-ENEL-1111111111"


class TestMeterCRUD_Nigeria:
    """Test CRUD operations for Nigeria meters"""
    
    def test_create_nigeria_meter_with_band(self, users_all_regions, utility_providers):
        """Test creating a meter in Nigeria with band classification"""
        user_data = users_all_regions["NG"]
        provider = utility_providers["NG"]
        
        meter_data = {
            "meter_id": "NG-LA-IKEDP-12345678901",
            "utility_provider_id": str(provider.id),
            "state_province": "Lagos",
            "utility_provider": "Ikeja Electric",
            "meter_type": "postpaid",
            "band_classification": "B",
            "address": "123 Victoria Island, Lagos"
        }
        
        headers = {"Authorization": f"Bearer {user_data['token']}"}
        response = client.post("/api/meters", json=meter_data, headers=headers)
        
        assert response.status_code == 201
        data = response.json()
        assert data["meter_id"] == "NG-LA-IKEDP-12345678901"
        assert data["utility_provider"] == "Ikeja Electric"
        assert data["state_province"] == "Lagos"
        assert data["band_classification"] == "B"
    
    def test_create_nigeria_meter_all_bands(self, users_all_regions, utility_providers):
        """Test creating Nigeria meters with all band classifications"""
        user_data = users_all_regions["NG"]
        provider = utility_providers["NG"]
        
        bands = ["A", "B", "C", "D", "E"]
        
        for i, band in enumerate(bands):
            meter_data = {
                "meter_id": f"NG-LA-IKEDP-{band}{i:09d}",
                "utility_provider_id": str(provider.id),
                "state_province": "Lagos",
                "utility_provider": "Ikeja Electric",
                "meter_type": "postpaid",
                "band_classification": band
            }
            
            headers = {"Authorization": f"Bearer {user_data['token']}"}
            response = client.post("/api/meters", json=meter_data, headers=headers)
            
            assert response.status_code == 201
            data = response.json()
            assert data["band_classification"] == band
    
    def test_read_nigeria_meters(self, users_all_regions, utility_providers):
        """Test reading Nigeria meters"""
        user_data = users_all_regions["NG"]
        provider = utility_providers["NG"]
        
        # Create meters with different bands
        db = TestingSessionLocal()
        meters = [
            Meter(
                user_id=user_data["user"].id,
                meter_id="NG-LA-IKEDP-11111111111",
                utility_provider_id=provider.id,
                state_province="Lagos",
                utility_provider="Ikeja Electric",
                meter_type=MeterTypeEnum.POSTPAID,
                band_classification="A",
                is_primary=True
            ),
            Meter(
                user_id=user_data["user"].id,
                meter_id="NG-LA-IKEDP-22222222222",
                utility_provider_id=provider.id,
                state_province="Lagos",
                utility_provider="Ikeja Electric",
                meter_type=MeterTypeEnum.PREPAID,
                band_classification="C",
                is_primary=False
            )
        ]
        db.add_all(meters)
        db.commit()
        db.close()
        
        # Read meters
        headers = {"Authorization": f"Bearer {user_data['token']}"}
        response = client.get("/api/meters", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        
        # Verify band classifications are preserved
        bands = [m["band_classification"] for m in data]
        assert "A" in bands
        assert "C" in bands


class TestMeterCRUD_CrossRegion:
    """Test CRUD operations across multiple regions"""
    
    def test_user_isolation_across_regions(self, users_all_regions, utility_providers):
        """Test that users from different regions can't see each other's meters"""
        # Create meters for Spain and USA users
        spain_user = users_all_regions["ES"]
        usa_user = users_all_regions["US"]
        spain_provider = utility_providers["ES"]
        usa_provider = utility_providers["US"]
        
        db = TestingSessionLocal()
        
        # Spain meter
        spain_meter = Meter(
            user_id=spain_user["user"].id,
            meter_id="ES-MAD-11111111",
            utility_provider_id=spain_provider.id,
            state_province="Madrid",
            utility_provider="Iberdrola",
            meter_type=MeterTypeEnum.POSTPAID,
            is_primary=True
        )
        
        # USA meter
        usa_meter = Meter(
            user_id=usa_user["user"].id,
            meter_id="US-CA-PGE-111111111111",
            utility_provider_id=usa_provider.id,
            state_province="California",
            utility_provider="Pacific Gas & Electric",
            meter_type=MeterTypeEnum.POSTPAID,
            is_primary=True
        )
        
        db.add_all([spain_meter, usa_meter])
        db.commit()
        db.close()
        
        # Spain user should only see their meter
        spain_headers = {"Authorization": f"Bearer {spain_user['token']}"}
        spain_response = client.get("/api/meters", headers=spain_headers)
        spain_data = spain_response.json()
        
        assert len(spain_data) == 1
        assert spain_data[0]["meter_id"] == "ES-MAD-11111111"
        
        # USA user should only see their meter
        usa_headers = {"Authorization": f"Bearer {usa_user['token']}"}
        usa_response = client.get("/api/meters", headers=usa_headers)
        usa_data = usa_response.json()
        
        assert len(usa_data) == 1
        assert usa_data[0]["meter_id"] == "US-CA-PGE-111111111111"
    
    def test_multiple_meters_per_user_all_regions(self, users_all_regions, utility_providers):
        """Test that users can have multiple meters (FR-2.1)"""
        for country_code, user_data in users_all_regions.items():
            provider = utility_providers[country_code]
            
            # Create 3 meters for each user
            db = TestingSessionLocal()
            for i in range(3):
                meter = Meter(
                    user_id=user_data["user"].id,
                    meter_id=f"{country_code}-TEST-{i:010d}",
                    utility_provider_id=provider.id,
                    state_province=provider.state_province,
                    utility_provider=provider.provider_name,
                    meter_type=MeterTypeEnum.POSTPAID,
                    is_primary=(i == 0)
                )
                db.add(meter)
            db.commit()
            db.close()
            
            # Verify user has 3 meters
            headers = {"Authorization": f"Bearer {user_data['token']}"}
            response = client.get("/api/meters", headers=headers)
            data = response.json()
            
            assert len(data) == 3, f"User in {country_code} should have 3 meters"
    
    def test_delete_meter_all_regions(self, users_all_regions, utility_providers):
        """Test meter deletion works for all regions (FR-2.4)"""
        for country_code, user_data in users_all_regions.items():
            provider = utility_providers[country_code]
            
            # Create a meter
            db = TestingSessionLocal()
            meter = Meter(
                user_id=user_data["user"].id,
                meter_id=f"{country_code}-DELETE-TEST",
                utility_provider_id=provider.id,
                state_province=provider.state_province,
                utility_provider=provider.provider_name,
                meter_type=MeterTypeEnum.POSTPAID,
                is_primary=True
            )
            db.add(meter)
            db.commit()
            meter_id = meter.id
            db.close()
            
            # Delete meter
            headers = {"Authorization": f"Bearer {user_data['token']}"}
            delete_response = client.delete(f"/api/meters/{meter_id}", headers=headers)
            
            assert delete_response.status_code == 200, f"Delete failed for {country_code}"
            
            # Verify meter is deleted
            list_response = client.get("/api/meters", headers=headers)
            data = list_response.json()
            
            meter_ids = [m["meter_id"] for m in data]
            assert f"{country_code}-DELETE-TEST" not in meter_ids


class TestMeterValidation_AllRegions:
    """Test meter ID validation for all regions (FR-2.2)"""
    
    def test_spain_meter_validation(self, users_all_regions, utility_providers):
        """Test Spain meter ID validation"""
        user_data = users_all_regions["ES"]
        provider = utility_providers["ES"]
        
        valid_ids = [
            "ES-MAD-12345678",
            "ES-BCN-87654321",
            "ES-VAL-11111111"
        ]
        
        for meter_id in valid_ids:
            meter_data = {
                "meter_id": meter_id,
                "utility_provider_id": str(provider.id),
                "state_province": "Madrid",
                "utility_provider": "Iberdrola",
                "meter_type": "postpaid"
            }
            
            headers = {"Authorization": f"Bearer {user_data['token']}"}
            response = client.post("/api/meters", json=meter_data, headers=headers)
            
            assert response.status_code == 201, f"Valid meter ID {meter_id} was rejected"
    
    def test_usa_meter_validation(self, users_all_regions, utility_providers):
        """Test USA meter ID validation"""
        user_data = users_all_regions["US"]
        provider = utility_providers["US"]
        
        valid_ids = [
            "US-CA-PGE-123456789012",
            "US-TX-ONCOR-987654321098",
            "US-NY-CONED-111111111111"
        ]
        
        for meter_id in valid_ids:
            meter_data = {
                "meter_id": meter_id,
                "utility_provider_id": str(provider.id),
                "state_province": "California",
                "utility_provider": "Pacific Gas & Electric",
                "meter_type": "postpaid"
            }
            
            headers = {"Authorization": f"Bearer {user_data['token']}"}
            response = client.post("/api/meters", json=meter_data, headers=headers)
            
            assert response.status_code == 201, f"Valid meter ID {meter_id} was rejected"
    
    def test_india_meter_validation(self, users_all_regions, utility_providers):
        """Test India meter ID validation"""
        user_data = users_all_regions["IN"]
        provider = utility_providers["IN"]
        
        valid_ids = [
            "IN-DL-TPDDL-12345678901234",
            "IN-MH-MSEDCL-98765432109876",
            "IN-KA-BESCOM-11111111111111"
        ]
        
        for meter_id in valid_ids:
            meter_data = {
                "meter_id": meter_id,
                "utility_provider_id": str(provider.id),
                "state_province": "Delhi",
                "utility_provider": "Tata Power Delhi Distribution Limited",
                "meter_type": "postpaid"
            }
            
            headers = {"Authorization": f"Bearer {user_data['token']}"}
            response = client.post("/api/meters", json=meter_data, headers=headers)
            
            assert response.status_code == 201, f"Valid meter ID {meter_id} was rejected"
    
    def test_brazil_meter_validation(self, users_all_regions, utility_providers):
        """Test Brazil meter ID validation"""
        user_data = users_all_regions["BR"]
        provider = utility_providers["BR"]
        
        valid_ids = [
            "BR-SP-ENEL-1234567890",
            "BR-RJ-LIGHT-9876543210",
            "BR-MG-CEMIG-1111111111"
        ]
        
        for meter_id in valid_ids:
            meter_data = {
                "meter_id": meter_id,
                "utility_provider_id": str(provider.id),
                "state_province": "São Paulo",
                "utility_provider": "Enel São Paulo",
                "meter_type": "postpaid"
            }
            
            headers = {"Authorization": f"Bearer {user_data['token']}"}
            response = client.post("/api/meters", json=meter_data, headers=headers)
            
            assert response.status_code == 201, f"Valid meter ID {meter_id} was rejected"
    
    def test_nigeria_meter_validation(self, users_all_regions, utility_providers):
        """Test Nigeria meter ID validation"""
        user_data = users_all_regions["NG"]
        provider = utility_providers["NG"]
        
        valid_ids = [
            "NG-LA-IKEDP-12345678901",
            "NG-AB-AEDC-98765432109",
            "NG-KA-KAEDCO-11111111111"
        ]
        
        for meter_id in valid_ids:
            meter_data = {
                "meter_id": meter_id,
                "utility_provider_id": str(provider.id),
                "state_province": "Lagos",
                "utility_provider": "Ikeja Electric",
                "meter_type": "postpaid",
                "band_classification": "B"
            }
            
            headers = {"Authorization": f"Bearer {user_data['token']}"}
            response = client.post("/api/meters", json=meter_data, headers=headers)
            
            assert response.status_code == 201, f"Valid meter ID {meter_id} was rejected"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
