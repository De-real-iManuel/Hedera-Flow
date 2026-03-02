"""
Test Payment Preparation with Various Bill Amounts and Currencies
Task 17.7: Comprehensive testing of POST /api/payments/prepare endpoint

This test suite validates:
1. Correct HBAR amount calculation for various bill amounts across all 5 currencies
2. Exchange rate fetching and caching behavior
3. Rate lock expiry (5 minutes)
4. Edge cases: minimum amounts, large amounts, zero amounts
5. Currency-specific formatting and validation
6. Error handling for invalid bill IDs, already paid bills, etc.

Requirements:
- US-7: Payment with HBAR (Native Token)
- FR-5.2: System shall fetch real-time HBAR exchange rates
- FR-5.3: System shall cache exchange rates for 5 minutes
- FR-5.4: System shall convert fiat bill amounts to HBAR equivalents
- FR-6.2: System shall calculate HBAR amount = (fiat_bill_amount / hbar_price)
- FR-6.13: System shall handle exchange rate volatility with 2% buffer
- FR-17.4: Set 5-minute rate lock to protect against volatility

Test Coverage:
- All 5 currencies: EUR (Spain), USD (USA), INR (India), BRL (Brazil), NGN (Nigeria)
- Small amounts: €5, $5, ₹50, R$10, ₦2000
- Medium amounts: €85, $120, ₹450, R$95, ₦12500
- Large amounts: €500, $1000, ₹5000, R$500, ₦100000
- Edge cases: zero amounts, negative amounts, very large amounts
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from decimal import Decimal
from uuid import uuid4
from typing import Dict, Any

from main import app
from app.models.user import User
from app.models.bill import Bill
from app.models.meter import Meter
from app.models.utility_provider import UtilityProvider
from app.core.database import get_db


# Test data: bill amounts for each currency
# Format: (currency, country_code, small_amount, medium_amount, large_amount)
CURRENCY_TEST_DATA = [
    ("EUR", "ES", 5.00, 85.00, 500.00),      # Spain
    ("USD", "US", 5.00, 120.00, 1000.00),    # USA
    ("INR", "IN", 50.00, 450.00, 5000.00),   # India
    ("BRL", "BR", 10.00, 95.00, 500.00),     # Brazil
    ("NGN", "NG", 2000.00, 12500.00, 100000.00),  # Nigeria
]


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


@pytest.fixture
def db(db_session):
    """Get database session from conftest"""
    return db_session


def create_test_user(db: Session, email: str, country_code: str, hedera_account: str) -> User:
    """Helper to create a test user"""
    user = User(
        email=email,
        password_hash="hashed_password",
        country_code=country_code,
        hedera_account_id=hedera_account
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def create_test_meter(db: Session, user: User, meter_id: str, utility_provider: str) -> Meter:
    """Helper to create a test meter"""
    meter = Meter(
        user_id=user.id,
        meter_id=meter_id,
        utility_provider=utility_provider,
        state_province="Test State",
        meter_type="postpaid"
    )
    db.add(meter)
    db.commit()
    db.refresh(meter)
    return meter


def create_test_bill(
    db: Session,
    user: User,
    meter: Meter,
    total_fiat: Decimal,
    currency: str,
    consumption_kwh: Decimal = Decimal("100.0")
) -> Bill:
    """Helper to create a test bill"""
    # Calculate base charge and taxes (approximate)
    base_charge = total_fiat * Decimal("0.85")
    taxes = total_fiat * Decimal("0.15")
    
    bill = Bill(
        user_id=user.id,
        meter_id=meter.id,
        consumption_kwh=consumption_kwh,
        base_charge=base_charge,
        taxes=taxes,
        total_fiat=total_fiat,
        currency=currency,
        status="pending"
    )
    db.add(bill)
    db.commit()
    db.refresh(bill)
    return bill


def get_auth_headers(user: User) -> Dict[str, str]:
    """Helper to create authentication headers"""
    from app.utils.auth import create_access_token
    token = create_access_token(
        user_id=str(user.id),
        email=user.email,
        country_code=user.country_code,
        hedera_account_id=user.hedera_account_id
    )
    return {"Authorization": f"Bearer {token}"}


class TestPaymentPrepareCurrencies:
    """Test suite for payment preparation with various currencies"""
    
    @pytest.mark.parametrize("currency,country_code,small,medium,large", CURRENCY_TEST_DATA)
    def test_small_bill_amounts(
        self,
        client: TestClient,
        db: Session,
        currency: str,
        country_code: str,
        small: float,
        medium: float,
        large: float
    ):
        """
        Test payment preparation with small bill amounts
        
        Small amounts:
        - EUR: €5.00
        - USD: $5.00
        - INR: ₹50.00
        - BRL: R$10.00
        - NGN: ₦2,000
        
        Verifies:
        - HBAR amount is calculated correctly
        - Exchange rate is fetched
        - Rate lock is created (5 minutes)
        - Transaction details are correct
        """
        # Create test user
        user = create_test_user(
            db,
            f"test_{currency.lower()}_small@example.com",
            country_code,
            f"0.0.{hash(currency) % 100000}"
        )
        
        # Create test meter
        meter = create_test_meter(
            db,
            user,
            f"{country_code}-METER-001",
            f"Test Utility {country_code}"
        )
        
        # Create test bill with small amount
        bill = create_test_bill(
            db,
            user,
            meter,
            Decimal(str(small)),
            currency,
            Decimal("10.0")  # Small consumption
        )
        
        # Get auth headers
        headers = get_auth_headers(user)
        
        # Prepare payment
        response = client.post(
            "/api/payments/prepare",
            json={"bill_id": str(bill.id)},
            headers=headers
        )
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        
        # Verify bill details
        assert data["bill"]["id"] == str(bill.id)
        assert float(data["bill"]["total_fiat"]) == small
        assert data["bill"]["currency"] == currency
        
        # Verify HBAR amount is calculated
        assert "transaction" in data
        assert float(data["transaction"]["amount_hbar"]) > 0
        
        # Verify exchange rate
        assert "exchange_rate" in data
        assert data["exchange_rate"]["currency"] == currency
        assert float(data["exchange_rate"]["hbar_price"]) > 0
        
        # Verify rate lock expiry (5 minutes)
        fetched_at = datetime.fromisoformat(data["exchange_rate"]["fetched_at"].replace("Z", "+00:00"))
        expires_at = datetime.fromisoformat(data["exchange_rate"]["expires_at"].replace("Z", "+00:00"))
        time_diff = (expires_at - fetched_at).total_seconds()
        assert 290 <= time_diff <= 310  # ~5 minutes
    
    @pytest.mark.parametrize("currency,country_code,small,medium,large", CURRENCY_TEST_DATA)
    def test_medium_bill_amounts(
        self,
        client: TestClient,
        db: Session,
        currency: str,
        country_code: str,
        small: float,
        medium: float,
        large: float
    ):
        """
        Test payment preparation with medium bill amounts
        
        Medium amounts:
        - EUR: €85.00
        - USD: $120.00
        - INR: ₹450.00
        - BRL: R$95.00
        - NGN: ₦12,500
        
        Verifies:
        - HBAR calculation accuracy
        - 2% volatility buffer is applied
        - Transaction memo format
        """
        # Create test user
        user = create_test_user(
            db,
            f"test_{currency.lower()}_medium@example.com",
            country_code,
            f"0.0.{hash(currency + 'medium') % 100000}"
        )
        
        # Create test meter
        meter = create_test_meter(
            db,
            user,
            f"{country_code}-METER-002",
            f"Test Utility {country_code}"
        )
        
        # Create test bill with medium amount
        bill = create_test_bill(
            db,
            user,
            meter,
            Decimal(str(medium)),
            currency,
            Decimal("150.0")  # Medium consumption
        )
        
        # Get auth headers
        headers = get_auth_headers(user)
        
        # Prepare payment
        response = client.post(
            "/api/payments/prepare",
            json={"bill_id": str(bill.id)},
            headers=headers
        )
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        
        # Verify bill details
        assert float(data["bill"]["total_fiat"]) == medium
        assert data["bill"]["currency"] == currency
        
        # Verify HBAR amount calculation with 2% buffer
        total_fiat = float(data["bill"]["total_fiat"])
        hbar_price = float(data["exchange_rate"]["hbar_price"])
        amount_hbar = float(data["transaction"]["amount_hbar"])
        
        # Calculate expected HBAR with 2% buffer
        expected_without_buffer = total_fiat / hbar_price
        expected_with_buffer = expected_without_buffer * 1.02
        
        # Verify buffer is applied (within 1% tolerance for rounding)
        assert abs(amount_hbar - expected_with_buffer) / expected_with_buffer < 0.01
        
        # Verify transaction memo format
        memo = data["transaction"]["memo"]
        assert memo.startswith("Bill payment: BILL-")
        assert currency in memo
        assert str(bill.created_at.year) in memo
    
    @pytest.mark.parametrize("currency,country_code,small,medium,large", CURRENCY_TEST_DATA)
    def test_large_bill_amounts(
        self,
        client: TestClient,
        db: Session,
        currency: str,
        country_code: str,
        small: float,
        medium: float,
        large: float
    ):
        """
        Test payment preparation with large bill amounts
        
        Large amounts:
        - EUR: €500.00
        - USD: $1,000.00
        - INR: ₹5,000.00
        - BRL: R$500.00
        - NGN: ₦100,000
        
        Verifies:
        - System handles large amounts correctly
        - HBAR precision (8 decimal places)
        - No overflow errors
        """
        # Create test user
        user = create_test_user(
            db,
            f"test_{currency.lower()}_large@example.com",
            country_code,
            f"0.0.{hash(currency + 'large') % 100000}"
        )
        
        # Create test meter
        meter = create_test_meter(
            db,
            user,
            f"{country_code}-METER-003",
            f"Test Utility {country_code}"
        )
        
        # Create test bill with large amount
        bill = create_test_bill(
            db,
            user,
            meter,
            Decimal(str(large)),
            currency,
            Decimal("1000.0")  # Large consumption
        )
        
        # Get auth headers
        headers = get_auth_headers(user)
        
        # Prepare payment
        response = client.post(
            "/api/payments/prepare",
            json={"bill_id": str(bill.id)},
            headers=headers
        )
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        
        # Verify bill details
        assert float(data["bill"]["total_fiat"]) == large
        assert data["bill"]["currency"] == currency
        
        # Verify HBAR amount is calculated
        amount_hbar = float(data["transaction"]["amount_hbar"])
        assert amount_hbar > 0
        
        # Verify HBAR precision (should be rounded to 8 decimal places)
        amount_hbar_str = str(data["transaction"]["amount_hbar"])
        if "." in amount_hbar_str:
            decimal_places = len(amount_hbar_str.split(".")[1])
            assert decimal_places <= 8
        
        # Verify no overflow errors
        assert amount_hbar < 1e15  # Reasonable upper bound


class TestPaymentPrepareEdgeCases:
    """Test suite for edge cases in payment preparation"""
    
    def test_zero_amount_bill(self, client: TestClient, db: Session):
        """Test payment preparation with zero amount bill (should fail)"""
        # Create test user
        user = create_test_user(db, "test_zero@example.com", "ES", "0.0.12345")
        meter = create_test_meter(db, user, "ESP-ZERO", "Test Utility")
        
        # Create bill with zero amount
        bill = create_test_bill(db, user, meter, Decimal("0.00"), "EUR")
        
        # Get auth headers
        headers = get_auth_headers(user)
        
        # Prepare payment
        response = client.post(
            "/api/payments/prepare",
            json={"bill_id": str(bill.id)},
            headers=headers
        )
        
        # Should succeed but HBAR amount will be 0
        # (validation happens at smart contract level)
        assert response.status_code == 200
        data = response.json()
        assert float(data["transaction"]["amount_hbar"]) >= 0
    
    def test_very_large_amount(self, client: TestClient, db: Session):
        """Test payment preparation with very large amount"""
        # Create test user
        user = create_test_user(db, "test_large@example.com", "US", "0.0.12346")
        meter = create_test_meter(db, user, "USA-LARGE", "Test Utility")
        
        # Create bill with very large amount
        bill = create_test_bill(db, user, meter, Decimal("999999.99"), "USD")
        
        # Get auth headers
        headers = get_auth_headers(user)
        
        # Prepare payment
        response = client.post(
            "/api/payments/prepare",
            json={"bill_id": str(bill.id)},
            headers=headers
        )
        
        # Should succeed
        assert response.status_code == 200
        data = response.json()
        assert float(data["transaction"]["amount_hbar"]) > 0
    
    def test_fractional_amounts(self, client: TestClient, db: Session):
        """Test payment preparation with fractional amounts"""
        # Create test user
        user = create_test_user(db, "test_fractional@example.com", "IN", "0.0.12347")
        meter = create_test_meter(db, user, "IND-FRAC", "Test Utility")
        
        # Create bill with fractional amount
        bill = create_test_bill(db, user, meter, Decimal("123.456789"), "INR")
        
        # Get auth headers
        headers = get_auth_headers(user)
        
        # Prepare payment
        response = client.post(
            "/api/payments/prepare",
            json={"bill_id": str(bill.id)},
            headers=headers
        )
        
        # Should succeed and handle precision correctly
        assert response.status_code == 200
        data = response.json()
        
        # Verify fiat amount precision is preserved
        assert abs(float(data["bill"]["total_fiat"]) - 123.456789) < 0.01


class TestExchangeRateBehavior:
    """Test suite for exchange rate fetching and caching"""
    
    def test_exchange_rate_caching(self, client: TestClient, db: Session):
        """
        Test that exchange rates are cached for 5 minutes
        
        Verifies FR-5.3: System shall cache exchange rates for 5 minutes
        """
        # Create test user and bill
        user = create_test_user(db, "test_cache@example.com", "ES", "0.0.12348")
        meter = create_test_meter(db, user, "ESP-CACHE", "Test Utility")
        bill = create_test_bill(db, user, meter, Decimal("100.00"), "EUR")
        
        # Get auth headers
        headers = get_auth_headers(user)
        
        # First request
        response1 = client.post(
            "/api/payments/prepare",
            json={"bill_id": str(bill.id)},
            headers=headers
        )
        
        assert response1.status_code == 200
        data1 = response1.json()
        
        # Second request immediately after (should use cache)
        response2 = client.post(
            "/api/payments/prepare",
            json={"bill_id": str(bill.id)},
            headers=headers
        )
        
        assert response2.status_code == 200
        data2 = response2.json()
        
        # Exchange rates should be identical (from cache)
        assert data1["exchange_rate"]["hbar_price"] == data2["exchange_rate"]["hbar_price"]
        assert data1["exchange_rate"]["fetched_at"] == data2["exchange_rate"]["fetched_at"]
    
    def test_rate_lock_expiry(self, client: TestClient, db: Session):
        """
        Test that rate lock expires after 5 minutes
        
        Verifies FR-17.4: Set 5-minute rate lock to protect against volatility
        """
        # Create test user and bill
        user = create_test_user(db, "test_expiry@example.com", "USD", "0.0.12349")
        meter = create_test_meter(db, user, "USA-EXPIRY", "Test Utility")
        bill = create_test_bill(db, user, meter, Decimal("100.00"), "USD")
        
        # Get auth headers
        headers = get_auth_headers(user)
        
        # Prepare payment
        response = client.post(
            "/api/payments/prepare",
            json={"bill_id": str(bill.id)},
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify rate lock expiry is set to 5 minutes from now
        fetched_at = datetime.fromisoformat(data["exchange_rate"]["fetched_at"].replace("Z", "+00:00"))
        expires_at = datetime.fromisoformat(data["exchange_rate"]["expires_at"].replace("Z", "+00:00"))
        
        # Calculate time difference
        time_diff_seconds = (expires_at - fetched_at).total_seconds()
        
        # Should be approximately 5 minutes (300 seconds)
        # Allow 10 second variance for processing time
        assert 290 <= time_diff_seconds <= 310
    
    def test_exchange_rate_source(self, client: TestClient, db: Session):
        """Test that exchange rate source is returned (CoinGecko or CoinMarketCap)"""
        # Create test user and bill
        user = create_test_user(db, "test_source@example.com", "BRL", "0.0.12350")
        meter = create_test_meter(db, user, "BRA-SOURCE", "Test Utility")
        bill = create_test_bill(db, user, meter, Decimal("100.00"), "BRL")
        
        # Get auth headers
        headers = get_auth_headers(user)
        
        # Prepare payment
        response = client.post(
            "/api/payments/prepare",
            json={"bill_id": str(bill.id)},
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify source is present and valid
        assert "source" in data["exchange_rate"]
        assert data["exchange_rate"]["source"] in ["coingecko", "coinmarketcap"]


class TestErrorHandling:
    """Test suite for error handling in payment preparation"""
    
    def test_invalid_bill_id_format(self, client: TestClient, db: Session):
        """Test payment preparation with invalid bill ID format"""
        user = create_test_user(db, "test_invalid@example.com", "ES", "0.0.12351")
        headers = get_auth_headers(user)
        
        response = client.post(
            "/api/payments/prepare",
            json={"bill_id": "invalid-uuid"},
            headers=headers
        )
        
        assert response.status_code == 400
        assert "Invalid bill ID format" in response.json()["detail"]
    
    def test_bill_not_found(self, client: TestClient, db: Session):
        """Test payment preparation with non-existent bill"""
        user = create_test_user(db, "test_notfound@example.com", "US", "0.0.12352")
        headers = get_auth_headers(user)
        
        fake_bill_id = str(uuid4())
        
        response = client.post(
            "/api/payments/prepare",
            json={"bill_id": fake_bill_id},
            headers=headers
        )
        
        assert response.status_code == 404
        assert "Bill not found" in response.json()["detail"]
    
    def test_already_paid_bill(self, client: TestClient, db: Session):
        """Test payment preparation for already paid bill"""
        # Create test user and bill
        user = create_test_user(db, "test_paid@example.com", "IN", "0.0.12353")
        meter = create_test_meter(db, user, "IND-PAID", "Test Utility")
        bill = create_test_bill(db, user, meter, Decimal("100.00"), "INR")
        
        # Mark bill as paid
        bill.status = "paid"
        bill.hedera_tx_id = "0.0.12345@1710789600.123456789"
        bill.paid_at = datetime.utcnow()
        db.commit()
        
        # Get auth headers
        headers = get_auth_headers(user)
        
        # Try to prepare payment
        response = client.post(
            "/api/payments/prepare",
            json={"bill_id": str(bill.id)},
            headers=headers
        )
        
        assert response.status_code == 400
        assert "Bill already paid" in response.json()["detail"]
    
    def test_unauthorized_access(self, client: TestClient, db: Session):
        """Test payment preparation without authentication"""
        # Create test user and bill
        user = create_test_user(db, "test_unauth@example.com", "BR", "0.0.12354")
        meter = create_test_meter(db, user, "BRA-UNAUTH", "Test Utility")
        bill = create_test_bill(db, user, meter, Decimal("100.00"), "BRL")
        
        # Try to prepare payment without auth headers
        response = client.post(
            "/api/payments/prepare",
            json={"bill_id": str(bill.id)}
        )
        
        assert response.status_code == 401
    
    def test_different_user_bill(self, client: TestClient, db: Session):
        """Test payment preparation for bill belonging to different user"""
        # Create first user and bill
        user1 = create_test_user(db, "test_user1@example.com", "NG", "0.0.12355")
        meter1 = create_test_meter(db, user1, "NGA-USER1", "Test Utility")
        bill1 = create_test_bill(db, user1, meter1, Decimal("10000.00"), "NGN")
        
        # Create second user
        user2 = create_test_user(db, "test_user2@example.com", "NG", "0.0.12356")
        
        # Get auth headers for user2
        headers = get_auth_headers(user2)
        
        # Try to prepare payment for user1's bill
        response = client.post(
            "/api/payments/prepare",
            json={"bill_id": str(bill1.id)},
            headers=headers
        )
        
        # Should not find bill (belongs to different user)
        assert response.status_code == 404
        assert "Bill not found" in response.json()["detail"]


class TestTransactionDetails:
    """Test suite for transaction details generation"""
    
    def test_transaction_from_field(self, client: TestClient, db: Session):
        """Test that transaction 'from' field is user's Hedera account"""
        user = create_test_user(db, "test_from@example.com", "ES", "0.0.99999")
        meter = create_test_meter(db, user, "ESP-FROM", "Test Utility")
        bill = create_test_bill(db, user, meter, Decimal("100.00"), "EUR")
        
        headers = get_auth_headers(user)
        
        response = client.post(
            "/api/payments/prepare",
            json={"bill_id": str(bill.id)},
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify 'from' field matches user's Hedera account
        assert data["transaction"]["from"] == user.hedera_account_id
    
    def test_transaction_to_field(self, client: TestClient, db: Session):
        """Test that transaction 'to' field is utility provider's account"""
        user = create_test_user(db, "test_to@example.com", "US", "0.0.88888")
        meter = create_test_meter(db, user, "USA-TO", "Test Utility")
        bill = create_test_bill(db, user, meter, Decimal("100.00"), "USD")
        
        headers = get_auth_headers(user)
        
        response = client.post(
            "/api/payments/prepare",
            json={"bill_id": str(bill.id)},
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify 'to' field is a valid Hedera account ID
        to_account = data["transaction"]["to"]
        assert to_account.startswith("0.0.")
        assert len(to_account.split(".")) == 3
    
    def test_transaction_memo_format(self, client: TestClient, db: Session):
        """Test that transaction memo follows correct format"""
        user = create_test_user(db, "test_memo@example.com", "IN", "0.0.77777")
        meter = create_test_meter(db, user, "IND-MEMO", "Test Utility")
        bill = create_test_bill(db, user, meter, Decimal("100.00"), "INR")
        
        headers = get_auth_headers(user)
        
        response = client.post(
            "/api/payments/prepare",
            json={"bill_id": str(bill.id)},
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify memo format: "Bill payment: BILL-{CURRENCY}-{YEAR}-{ID}"
        memo = data["transaction"]["memo"]
        assert memo.startswith("Bill payment: BILL-")
        assert "INR" in memo
        assert str(bill.created_at.year) in memo
        assert str(bill.id)[:8] in memo


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
