"""
Test verification endpoint with billing calculation integration

Tests Task 13.9: Trigger billing calculation after verification
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from unittest.mock import Mock, patch, MagicMock
import io
from PIL import Image
from decimal import Decimal

from app.core.app import app
from app.core.database import get_db
from config import settings


# Test database setup
TEST_DATABASE_URL = "sqlite:///./test_verification_billing.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
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
    """Create test database tables"""
    # Create tables
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT,
                country_code TEXT NOT NULL,
                hedera_account_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS meters (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                meter_id TEXT NOT NULL,
                utility_provider TEXT NOT NULL,
                state_province TEXT NOT NULL,
                meter_type TEXT,
                band_classification TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """))
        
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS verifications (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                meter_id TEXT NOT NULL,
                reading_value REAL NOT NULL,
                previous_reading REAL,
                consumption_kwh REAL,
                image_ipfs_hash TEXT,
                ocr_engine TEXT,
                confidence REAL,
                raw_ocr_text TEXT,
                fraud_score REAL,
                fraud_flags TEXT,
                utility_reading REAL,
                utility_api_response TEXT,
                status TEXT,
                hcs_topic_id TEXT,
                hcs_sequence_number INTEGER,
                hcs_timestamp TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (meter_id) REFERENCES meters(id)
            )
        """))
        
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS bills (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                meter_id TEXT NOT NULL,
                verification_id TEXT,
                consumption_kwh REAL NOT NULL,
                base_charge REAL NOT NULL,
                taxes REAL NOT NULL,
                subsidies REAL DEFAULT 0,
                total_fiat REAL NOT NULL,
                currency TEXT NOT NULL,
                tariff_id TEXT,
                tariff_snapshot TEXT,
                amount_hbar REAL,
                exchange_rate REAL,
                exchange_rate_timestamp TIMESTAMP,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (meter_id) REFERENCES meters(id),
                FOREIGN KEY (verification_id) REFERENCES verifications(id)
            )
        """))
        
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS tariffs (
                id TEXT PRIMARY KEY,
                country_code TEXT NOT NULL,
                utility_provider TEXT NOT NULL,
                state_province TEXT NOT NULL,
                currency TEXT NOT NULL,
                rate_structure TEXT NOT NULL,
                taxes_and_fees TEXT,
                subsidies TEXT,
                valid_from DATE NOT NULL,
                valid_until DATE,
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        
        conn.commit()
    
    yield
    
    # Cleanup
    with engine.connect() as conn:
        conn.execute(text("DROP TABLE IF EXISTS bills"))
        conn.execute(text("DROP TABLE IF EXISTS verifications"))
        conn.execute(text("DROP TABLE IF EXISTS meters"))
        conn.execute(text("DROP TABLE IF EXISTS users"))
        conn.execute(text("DROP TABLE IF EXISTS tariffs"))
        conn.commit()


def create_test_image():
    """Create a test image file"""
    img = Image.new('RGB', (100, 100), color='white')
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='JPEG')
    img_bytes.seek(0)
    return img_bytes


def test_verification_triggers_billing_calculation(setup_database):
    """Test that verification endpoint triggers billing calculation when consumption is available"""
    
    # Setup: Create test user, meter, and previous verification
    db = TestingSessionLocal()
    
    user_id = "test-user-123"
    meter_id = "test-meter-456"
    
    # Insert test user
    db.execute(text("""
        INSERT INTO users (id, email, country_code, hedera_account_id)
        VALUES (:id, :email, :country, :hedera_account)
    """), {
        "id": user_id,
        "email": "test@example.com",
        "country": "ES",
        "hedera_account": "0.0.12345"
    })
    
    # Insert test meter
    db.execute(text("""
        INSERT INTO meters (id, user_id, meter_id, utility_provider, state_province, meter_type)
        VALUES (:id, :user_id, :meter_id, :utility, :state, :type)
    """), {
        "id": meter_id,
        "user_id": user_id,
        "meter_id": "ESP-12345678",
        "utility": "Iberdrola",
        "state": "Madrid",
        "type": "postpaid"
    })
    
    # Insert previous verification (reading: 5000 kWh)
    db.execute(text("""
        INSERT INTO verifications (
            id, user_id, meter_id, reading_value, confidence, 
            fraud_score, status, ocr_engine, image_ipfs_hash
        )
        VALUES (:id, :user_id, :meter_id, :reading, :confidence, :fraud, :status, :engine, :hash)
    """), {
        "id": "prev-verification-123",
        "user_id": user_id,
        "meter_id": meter_id,
        "reading": 5000.0,
        "confidence": 0.95,
        "fraud": 0.1,
        "status": "VERIFIED",
        "engine": "tesseract",
        "hash": "ipfs://prev-hash"
    })
    
    # Insert test tariff
    import json
    tariff_data = {
        "type": "time_of_use",
        "periods": [
            {"name": "peak", "hours": [10, 11, 12, 13], "price": 0.40},
            {"name": "off_peak", "hours": [0, 1, 2, 3, 4, 5, 6, 7], "price": 0.15}
        ]
    }
    
    taxes_fees = {
        "vat": 0.21,
        "distribution_charge": 0.045
    }
    
    db.execute(text("""
        INSERT INTO tariffs (
            id, country_code, utility_provider, state_province, currency,
            rate_structure, taxes_and_fees, valid_from, is_active
        )
        VALUES (:id, :country, :utility, :state, :currency, :rates, :taxes, :valid_from, :active)
    """), {
        "id": "tariff-123",
        "country": "ES",
        "utility": "Iberdrola",
        "state": "Madrid",
        "currency": "EUR",
        "rates": json.dumps(tariff_data),
        "taxes": json.dumps(taxes_fees),
        "valid_from": "2024-01-01",
        "active": 1
    })
    
    db.commit()
    db.close()
    
    # Mock external services
    with patch('app.services.ocr_service.get_ocr_service') as mock_ocr, \
         patch('app.services.fraud_detection_service.get_fraud_detection_service') as mock_fraud, \
         patch('app.services.ipfs_service.get_ipfs_service') as mock_ipfs, \
         patch('app.utils.hedera_client.hedera_client') as mock_hedera, \
         patch('app.services.exchange_rate_service.get_hbar_price') as mock_exchange, \
         patch('app.core.dependencies.get_current_user') as mock_auth:
        
        # Mock OCR service
        mock_ocr_service = Mock()
        mock_ocr_service.extract_reading.return_value = {
            'reading': 5150.0,  # 150 kWh consumption
            'confidence': 0.96,
            'raw_text': 'Reading: 5150 kWh'
        }
        mock_ocr.return_value = mock_ocr_service
        
        # Mock fraud detection
        mock_fraud_service = Mock()
        mock_fraud_service.calculate_fraud_score.return_value = {
            'fraud_score': 0.15,
            'flags': []
        }
        mock_fraud.return_value = mock_fraud_service
        
        # Mock IPFS service
        mock_ipfs_service = Mock()
        mock_ipfs_service.upload_image.return_value = {
            'ipfs_url': 'ipfs://test-hash-123',
            'gateway_url': 'https://gateway.pinata.cloud/ipfs/test-hash-123'
        }
        mock_ipfs.return_value = mock_ipfs_service
        
        # Mock Hedera HCS
        mock_hedera.submit_hcs_message = MagicMock(return_value={
            'sequence_number': 12345,
            'timestamp': '2024-02-18T10:00:00Z'
        })
        
        # Mock exchange rate service
        mock_exchange.return_value = 0.35  # 1 HBAR = 0.35 EUR
        
        # Mock authentication
        mock_auth.return_value = {'user_id': user_id}
        
        # Execute: Call verification endpoint
        test_image = create_test_image()
        
        response = client.post(
            "/api/verify",
            data={
                "meter_id": meter_id,
                "ocr_reading": None,
                "ocr_confidence": None
            },
            files={"image": ("test.jpg", test_image, "image/jpeg")}
        )
        
        # Assert: Verification succeeded
        assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"
        
        data = response.json()
        
        # Verify verification data
        assert data['reading_value'] == 5150.0
        assert data['previous_reading'] == 5000.0
        assert data['consumption_kwh'] == 150.0
        assert data['status'] == 'VERIFIED'
        
        # Verify bill was created
        assert data['bill'] is not None, "Bill should be created when consumption is available"
        assert 'id' in data['bill']
        assert 'total_fiat' in data['bill']
        assert 'currency' in data['bill']
        assert data['bill']['currency'] == 'EUR'
        assert 'amount_hbar' in data['bill']
        assert 'exchange_rate' in data['bill']
        
        # Verify bill was saved to database
        db = TestingSessionLocal()
        bill_result = db.execute(text("""
            SELECT id, consumption_kwh, total_fiat, currency, amount_hbar, exchange_rate, status
            FROM bills
            WHERE verification_id = :verification_id
        """), {"verification_id": data['id']}).fetchone()
        
        assert bill_result is not None, "Bill should be saved to database"
        assert bill_result[1] == 150.0  # consumption_kwh
        assert bill_result[3] == 'EUR'  # currency
        assert bill_result[6] == 'pending'  # status
        
        db.close()


def test_verification_skips_billing_for_first_reading(setup_database):
    """Test that billing is skipped when there's no previous reading (first verification)"""
    
    # Setup: Create test user and meter (no previous verification)
    db = TestingSessionLocal()
    
    user_id = "test-user-789"
    meter_id = "test-meter-101"
    
    db.execute(text("""
        INSERT INTO users (id, email, country_code, hedera_account_id)
        VALUES (:id, :email, :country, :hedera_account)
    """), {
        "id": user_id,
        "email": "test2@example.com",
        "country": "US",
        "hedera_account": "0.0.67890"
    })
    
    db.execute(text("""
        INSERT INTO meters (id, user_id, meter_id, utility_provider, state_province, meter_type)
        VALUES (:id, :user_id, :meter_id, :utility, :state, :type)
    """), {
        "id": meter_id,
        "user_id": user_id,
        "meter_id": "USA-98765432",
        "utility": "PG&E",
        "state": "California",
        "type": "postpaid"
    })
    
    db.commit()
    db.close()
    
    # Mock external services
    with patch('app.services.ocr_service.get_ocr_service') as mock_ocr, \
         patch('app.services.fraud_detection_service.get_fraud_detection_service') as mock_fraud, \
         patch('app.services.ipfs_service.get_ipfs_service') as mock_ipfs, \
         patch('app.utils.hedera_client.hedera_client') as mock_hedera, \
         patch('app.core.dependencies.get_current_user') as mock_auth:
        
        # Mock services (same as previous test)
        mock_ocr_service = Mock()
        mock_ocr_service.extract_reading.return_value = {
            'reading': 1000.0,
            'confidence': 0.95,
            'raw_text': 'Reading: 1000 kWh'
        }
        mock_ocr.return_value = mock_ocr_service
        
        mock_fraud_service = Mock()
        mock_fraud_service.calculate_fraud_score.return_value = {
            'fraud_score': 0.1,
            'flags': []
        }
        mock_fraud.return_value = mock_fraud_service
        
        mock_ipfs_service = Mock()
        mock_ipfs_service.upload_image.return_value = {
            'ipfs_url': 'ipfs://test-hash-456',
            'gateway_url': 'https://gateway.pinata.cloud/ipfs/test-hash-456'
        }
        mock_ipfs.return_value = mock_ipfs_service
        
        mock_hedera.submit_hcs_message = MagicMock(return_value={
            'sequence_number': 12346,
            'timestamp': '2024-02-18T10:05:00Z'
        })
        
        mock_auth.return_value = {'user_id': user_id}
        
        # Execute: Call verification endpoint
        test_image = create_test_image()
        
        response = client.post(
            "/api/verify",
            data={
                "meter_id": meter_id,
                "ocr_reading": None,
                "ocr_confidence": None
            },
            files={"image": ("test.jpg", test_image, "image/jpeg")}
        )
        
        # Assert: Verification succeeded
        assert response.status_code == 201
        
        data = response.json()
        
        # Verify verification data
        assert data['reading_value'] == 1000.0
        assert data['previous_reading'] is None
        assert data['consumption_kwh'] is None
        
        # Verify bill was NOT created (no consumption data)
        assert data['bill'] is None, "Bill should not be created for first reading"
        
        # Verify no bill in database
        db = TestingSessionLocal()
        bill_result = db.execute(text("""
            SELECT COUNT(*) FROM bills WHERE verification_id = :verification_id
        """), {"verification_id": data['id']}).fetchone()
        
        assert bill_result[0] == 0, "No bill should be saved for first reading"
        
        db.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
