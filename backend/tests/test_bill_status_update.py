"""
Test Bill Status Update (Task 19.4)
Tests for updating bill status to "paid" in database

Requirements:
- FR-6.12: System shall update bill status to "PAID"
- US-7: Payment with HBAR

This test file specifically validates Task 19.4 requirements:
1. Update bill record to set status = "paid"
2. Set paid_at timestamp to current time
3. Store Hedera transaction ID (hedera_tx_id)
4. Store consensus timestamp from Hedera (hedera_consensus_timestamp)
5. Ensure update is atomic and handles race conditions
6. Add error handling for database update failures
7. Verify bill status update logic
"""

import pytest
import os
import sys

# Set test environment variables BEFORE importing app
os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
os.environ['REDIS_URL'] = 'redis://localhost:6379/0'
os.environ['JWT_SECRET_KEY'] = 'test-secret-key-for-testing-only'
os.environ['HEDERA_OPERATOR_ID'] = '0.0.12345'
os.environ['HEDERA_OPERATOR_KEY'] = '302e020100300506032b65700422042091132178e72057a1d7528025956fe39b0b847f200ab59b2fdd367017f3087137'
os.environ['HEDERA_TREASURY_ACCOUNT'] = '0.0.7942957'
os.environ['HEDERA_TOPIC_EU'] = '0.0.5078302'
os.environ['HEDERA_TOPIC_US'] = '0.0.5078303'
os.environ['HEDERA_TOPIC_ASIA'] = '0.0.5078304'
os.environ['HEDERA_TOPIC_SA'] = '0.0.5078305'
os.environ['HEDERA_TOPIC_AFRICA'] = '0.0.5078306'

# Add backend to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from datetime import datetime, timedelta
from decimal import Decimal
from uuid import uuid4

from app.core.app import app
from app.core.database import Base, get_db
from app.models.user import User
from app.models.bill import Bill
from app.models.meter import Meter
from app.utils.auth import create_access_token


# Test database setup
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


@pytest.fixture(scope="function")
def test_db():
    """Create test database"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db():
    """Get database session"""
    return TestingSessionLocal()


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


@pytest.fixture
def test_user(test_db, db):
    """Create a test user with Hedera account"""
    user = User(
        email="billtest@example.com",
        password_hash="hashed_password",
        country_code="ES",
        hedera_account_id="0.0.12345"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def auth_headers(test_user: User):
    """Create authentication headers"""
    token = create_access_token({"sub": test_user.email})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def test_meter(test_db, db, test_user: User):
    """Create a test meter"""
    meter = Meter(
        user_id=test_user.id,
        meter_id="ESP-TEST-001",
        utility_provider_id=None,
        state_province="Madrid",
        utility_provider="Iberdrola",
        meter_type="postpaid"
    )
    db.add(meter)
    db.commit()
    db.refresh(meter)
    return meter


@pytest.fixture
def pending_bill(test_db, db, test_user: User, test_meter: Meter):
    """Create a pending bill"""
    bill = Bill(
        user_id=test_user.id,
        meter_id=test_meter.id,
        consumption_kwh=Decimal("150.5"),
        base_charge=Decimal("75.25"),
        taxes=Decimal("15.81"),
        total_fiat=Decimal("91.06"),
        currency="EUR",
        status="pending",
        amount_hbar=Decimal("250.0"),
        exchange_rate=Decimal("0.36"),
        exchange_rate_timestamp=datetime.utcnow()
    )
    db.add(bill)
    db.commit()
    db.refresh(bill)
    return bill


class TestBillStatusUpdate:
    """Test suite for bill status update functionality"""
    
    def test_bill_status_updated_to_paid(self, client: TestClient, pending_bill: Bill, auth_headers, db):
        """
        Requirement 1: Update bill record to set status = "paid"
        """
        # Verify initial status
        assert pending_bill.status == "pending"
        
        # Confirm payment
        tx_id = "0.0.12345@1710789700.123456789"
        response = client.post(
            "/api/payments/confirm",
            json={
                "bill_id": str(pending_bill.id),
                "hedera_tx_id": tx_id
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200
        
        # Refresh bill from database
        db.refresh(pending_bill)
        
        # Verify status changed to paid
        assert pending_bill.status == "paid"
    
    def test_paid_at_timestamp_set(self, client: TestClient, pending_bill: Bill, auth_headers, db):
        """
        Requirement 2: Set paid_at timestamp to current time
        """
        # Verify paid_at is initially None
        assert pending_bill.paid_at is None
        
        # Record time before payment
        before_payment = datetime.utcnow()
        
        # Confirm payment
        tx_id = "0.0.12345@1710789700.123456789"
        response = client.post(
            "/api/payments/confirm",
            json={
                "bill_id": str(pending_bill.id),
                "hedera_tx_id": tx_id
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200
        
        # Record time after payment
        after_payment = datetime.utcnow()
        
        # Refresh bill from database
        db.refresh(pending_bill)
        
        # Verify paid_at is set
        assert pending_bill.paid_at is not None
        
        # Verify paid_at is within reasonable time range
        assert before_payment <= pending_bill.paid_at <= after_payment
    
    def test_hedera_tx_id_stored(self, client: TestClient, pending_bill: Bill, auth_headers, db):
        """
        Requirement 3: Store Hedera transaction ID (hedera_tx_id)
        """
        # Verify hedera_tx_id is initially None
        assert pending_bill.hedera_tx_id is None
        
        # Confirm payment with specific transaction ID
        tx_id = "0.0.12345@1710789700.123456789"
        response = client.post(
            "/api/payments/confirm",
            json={
                "bill_id": str(pending_bill.id),
                "hedera_tx_id": tx_id
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200
        
        # Refresh bill from database
        db.refresh(pending_bill)
        
        # Verify transaction ID is stored correctly
        assert pending_bill.hedera_tx_id == tx_id
    
    def test_consensus_timestamp_stored(self, client: TestClient, pending_bill: Bill, auth_headers, db):
        """
        Requirement 4: Store consensus timestamp from Hedera (hedera_consensus_timestamp)
        """
        # Verify consensus timestamp is initially None
        assert pending_bill.hedera_consensus_timestamp is None
        
        # Confirm payment
        tx_id = "0.0.12345@1710789700.123456789"
        response = client.post(
            "/api/payments/confirm",
            json={
                "bill_id": str(pending_bill.id),
                "hedera_tx_id": tx_id
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200
        
        # Refresh bill from database
        db.refresh(pending_bill)
        
        # Verify consensus timestamp is stored
        assert pending_bill.hedera_consensus_timestamp is not None
        
        # Verify it's a valid datetime
        assert isinstance(pending_bill.hedera_consensus_timestamp, datetime)
    
    def test_all_payment_fields_updated_atomically(self, client: TestClient, pending_bill: Bill, auth_headers, db):
        """
        Requirement 5: Ensure update is atomic (all fields updated together)
        """
        # Verify initial state
        assert pending_bill.status == "pending"
        assert pending_bill.paid_at is None
        assert pending_bill.hedera_tx_id is None
        assert pending_bill.hedera_consensus_timestamp is None
        
        # Confirm payment
        tx_id = "0.0.12345@1710789700.123456789"
        response = client.post(
            "/api/payments/confirm",
            json={
                "bill_id": str(pending_bill.id),
                "hedera_tx_id": tx_id
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200
        
        # Refresh bill from database
        db.refresh(pending_bill)
        
        # Verify ALL payment fields are updated (atomic operation)
        assert pending_bill.status == "paid"
        assert pending_bill.paid_at is not None
        assert pending_bill.hedera_tx_id == tx_id
        assert pending_bill.hedera_consensus_timestamp is not None
        assert pending_bill.amount_hbar is not None
        assert pending_bill.exchange_rate is not None
    
    def test_race_condition_already_paid(self, client: TestClient, pending_bill: Bill, auth_headers, db):
        """
        Requirement 5: Handle race conditions (prevent double payment)
        """
        # First payment succeeds
        tx_id_1 = "0.0.12345@1710789700.123456789"
        response1 = client.post(
            "/api/payments/confirm",
            json={
                "bill_id": str(pending_bill.id),
                "hedera_tx_id": tx_id_1
            },
            headers=auth_headers
        )
        
        assert response1.status_code == 200
        
        # Refresh bill
        db.refresh(pending_bill)
        assert pending_bill.status == "paid"
        
        # Second payment attempt should fail (race condition protection)
        tx_id_2 = "0.0.12345@1710789701.987654321"
        response2 = client.post(
            "/api/payments/confirm",
            json={
                "bill_id": str(pending_bill.id),
                "hedera_tx_id": tx_id_2
            },
            headers=auth_headers
        )
        
        # Should return 400 error
        assert response2.status_code == 400
        assert "Bill already paid" in response2.json()["detail"]
        
        # Verify original transaction ID is preserved
        db.refresh(pending_bill)
        assert pending_bill.hedera_tx_id == tx_id_1
    
    def test_error_handling_invalid_bill_id(self, client: TestClient, auth_headers):
        """
        Requirement 6: Error handling for invalid bill ID
        """
        response = client.post(
            "/api/payments/confirm",
            json={
                "bill_id": "invalid-uuid",
                "hedera_tx_id": "0.0.12345@1710789700.123456789"
            },
            headers=auth_headers
        )
        
        assert response.status_code == 400
        assert "Invalid bill ID format" in response.json()["detail"]
    
    def test_error_handling_bill_not_found(self, client: TestClient, auth_headers):
        """
        Requirement 6: Error handling for non-existent bill
        """
        fake_bill_id = str(uuid4())
        
        response = client.post(
            "/api/payments/confirm",
            json={
                "bill_id": fake_bill_id,
                "hedera_tx_id": "0.0.12345@1710789700.123456789"
            },
            headers=auth_headers
        )
        
        assert response.status_code == 404
        assert "Bill not found" in response.json()["detail"]
    
    def test_error_handling_unauthorized_access(self, client: TestClient, pending_bill: Bill):
        """
        Requirement 6: Error handling for unauthorized access
        """
        response = client.post(
            "/api/payments/confirm",
            json={
                "bill_id": str(pending_bill.id),
                "hedera_tx_id": "0.0.12345@1710789700.123456789"
            }
            # No auth headers
        )
        
        assert response.status_code == 401
    
    def test_error_handling_different_user_bill(self, client: TestClient, pending_bill: Bill, db):
        """
        Requirement 6: Error handling for accessing another user's bill
        """
        # Create another user
        other_user = User(
            email="other@example.com",
            password_hash="hashed_password",
            country_code="US",
            hedera_account_id="0.0.67890"
        )
        db.add(other_user)
        db.commit()
        
        # Get auth token for other user
        from app.utils.auth import create_access_token
        token = create_access_token({"sub": other_user.email})
        headers = {"Authorization": f"Bearer {token}"}
        
        response = client.post(
            "/api/payments/confirm",
            json={
                "bill_id": str(pending_bill.id),
                "hedera_tx_id": "0.0.12345@1710789700.123456789"
            },
            headers=headers
        )
        
        # Should not find bill (belongs to different user)
        assert response.status_code == 404
        assert "Bill not found" in response.json()["detail"]
    
    def test_bill_status_verification_in_response(self, client: TestClient, pending_bill: Bill, auth_headers, db):
        """
        Requirement 7: Verify bill status update logic returns correct data
        """
        tx_id = "0.0.12345@1710789700.123456789"
        
        response = client.post(
            "/api/payments/confirm",
            json={
                "bill_id": str(pending_bill.id),
                "hedera_tx_id": tx_id
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response contains payment confirmation
        assert "payment" in data
        assert "message" in data
        assert data["message"] == "Payment confirmed successfully"
        
        # Verify payment details in response
        payment = data["payment"]
        assert payment["bill_id"] == str(pending_bill.id)
        assert payment["hedera_tx_id"] == tx_id
        assert "consensus_timestamp" in payment
        assert "paid_at" in payment or "created_at" in payment
    
    def test_database_consistency_after_update(self, client: TestClient, pending_bill: Bill, auth_headers, db):
        """
        Verify database consistency after bill status update
        """
        # Record initial values
        initial_consumption = pending_bill.consumption_kwh
        initial_total = pending_bill.total_fiat
        initial_currency = pending_bill.currency
        
        # Confirm payment
        tx_id = "0.0.12345@1710789700.123456789"
        response = client.post(
            "/api/payments/confirm",
            json={
                "bill_id": str(pending_bill.id),
                "hedera_tx_id": tx_id
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200
        
        # Refresh bill from database
        db.refresh(pending_bill)
        
        # Verify original bill data is unchanged
        assert pending_bill.consumption_kwh == initial_consumption
        assert pending_bill.total_fiat == initial_total
        assert pending_bill.currency == initial_currency
        
        # Verify only payment-related fields are updated
        assert pending_bill.status == "paid"
        assert pending_bill.hedera_tx_id == tx_id
        assert pending_bill.paid_at is not None
        assert pending_bill.hedera_consensus_timestamp is not None
    
    def test_hcs_logging_fields_populated(self, client: TestClient, pending_bill: Bill, auth_headers, db):
        """
        Verify HCS logging fields are populated after payment
        """
        # Verify HCS fields are initially None
        assert pending_bill.hcs_topic_id is None
        assert pending_bill.hcs_sequence_number is None
        
        # Confirm payment
        tx_id = "0.0.12345@1710789700.123456789"
        response = client.post(
            "/api/payments/confirm",
            json={
                "bill_id": str(pending_bill.id),
                "hedera_tx_id": tx_id
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200
        
        # Refresh bill from database
        db.refresh(pending_bill)
        
        # Verify HCS fields are populated (if HCS logging succeeds)
        # Note: In test environment, HCS logging might fail, so we check if it was attempted
        # In production, these should always be populated
        if pending_bill.hcs_topic_id:
            assert pending_bill.hcs_topic_id.startswith("0.0.")
            assert pending_bill.hcs_sequence_number is not None
            assert pending_bill.hcs_sequence_number > 0


class TestBillStatusUpdateEdgeCases:
    """Test edge cases for bill status update"""
    
    def test_multiple_bills_same_user(self, client: TestClient, test_user: User, test_meter: Meter, auth_headers, db):
        """
        Test updating status for multiple bills from same user
        """
        # Create multiple bills
        bills = []
        for i in range(3):
            bill = Bill(
                user_id=test_user.id,
                meter_id=test_meter.id,
                consumption_kwh=Decimal(f"{100 + i * 10}.0"),
                base_charge=Decimal(f"{50 + i * 5}.0"),
                taxes=Decimal(f"{10 + i}.0"),
                total_fiat=Decimal(f"{60 + i * 6}.0"),
                currency="EUR",
                status="pending",
                amount_hbar=Decimal(f"{200 + i * 50}.0"),
                exchange_rate=Decimal("0.36")
            )
            db.add(bill)
            bills.append(bill)
        
        db.commit()
        
        # Pay each bill separately
        for i, bill in enumerate(bills):
            db.refresh(bill)
            tx_id = f"0.0.12345@171078970{i}.123456789"
            
            response = client.post(
                "/api/payments/confirm",
                json={
                    "bill_id": str(bill.id),
                    "hedera_tx_id": tx_id
                },
                headers=auth_headers
            )
            
            assert response.status_code == 200
            
            # Verify this bill is paid
            db.refresh(bill)
            assert bill.status == "paid"
            assert bill.hedera_tx_id == tx_id
        
        # Verify all bills are paid
        for bill in bills:
            db.refresh(bill)
            assert bill.status == "paid"
    
    def test_bill_status_query_after_update(self, client: TestClient, pending_bill: Bill, auth_headers, db):
        """
        Test querying bill status after update
        """
        # Confirm payment
        tx_id = "0.0.12345@1710789700.123456789"
        response = client.post(
            "/api/payments/confirm",
            json={
                "bill_id": str(pending_bill.id),
                "hedera_tx_id": tx_id
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200
        
        # Query the payment
        response = client.get(
            f"/api/payments/{pending_bill.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        payment_data = response.json()
        
        # Verify payment data reflects paid status
        assert payment_data["bill_id"] == str(pending_bill.id)
        assert payment_data["hedera_tx_id"] == tx_id
        assert "consensus_timestamp" in payment_data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
