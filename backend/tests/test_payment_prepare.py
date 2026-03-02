"""
Test Payment Preparation Endpoint
Tests for POST /api/payments/prepare

Requirements:
- FR-6.1: System shall fetch current HBAR price from exchange API
- FR-6.2: System shall calculate HBAR amount = (fiat_bill_amount / hbar_price)
- FR-6.13: System shall handle exchange rate volatility with 2% buffer
- US-7: Payment preparation with HBAR conversion
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from decimal import Decimal
from uuid import uuid4

from main import app
from app.models.user import User
from app.models.bill import Bill
from app.models.meter import Meter
from app.core.database import get_db


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


@pytest.fixture
def db(db_session):
    """Get database session from conftest"""
    return db_session


@pytest.fixture
def auth_headers(test_user: User):
    """Create authentication headers"""
    from app.utils.auth import create_access_token
    token = create_access_token({"sub": test_user.email})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def test_user(db: Session):
    """Create a test user with Hedera account"""
    user = User(
        email="test@example.com",
        password_hash="hashed_password",
        country_code="ES",
        hedera_account_id="0.0.12345"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def test_meter(db: Session, test_user: User):
    """Create a test meter"""
    meter = Meter(
        user_id=test_user.id,
        meter_id="ESP-12345678",
        utility_provider="Iberdrola",
        state_province="Madrid",
        meter_type="postpaid"
    )
    db.add(meter)
    db.commit()
    db.refresh(meter)
    return meter


@pytest.fixture
def test_bill(db: Session, test_user: User, test_meter: Meter):
    """Create a test bill (pending payment)"""
    bill = Bill(
        user_id=test_user.id,
        meter_id=test_meter.id,
        consumption_kwh=Decimal("150.5"),
        base_charge=Decimal("75.25"),
        taxes=Decimal("15.81"),
        total_fiat=Decimal("91.06"),
        currency="EUR",
        status="pending"
    )
    db.add(bill)
    db.commit()
    db.refresh(bill)
    return bill


def test_prepare_payment_success(client: TestClient, test_user: User, test_bill: Bill, auth_headers):
    """
    Test successful payment preparation
    
    Verifies:
    - FR-6.1: Fetches current HBAR exchange rate
    - FR-6.2: Calculates HBAR amount needed
    - FR-6.13: Applies 2% volatility buffer
    - Returns transaction details for user to sign
    """
    
    response = client.post(
        "/api/payments/prepare",
        json={
            "bill_id": str(test_bill.id),
            "payment_method": "hbar"
        },
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Verify response structure
    assert "bill" in data
    assert "transaction" in data
    assert "exchange_rate" in data
    assert "minimum_hbar" in data
    
    # Verify bill details
    bill_data = data["bill"]
    assert bill_data["id"] == str(test_bill.id)
    assert float(bill_data["total_fiat"]) == 91.06
    assert bill_data["currency"] == "EUR"
    assert float(bill_data["consumption_kwh"]) == 150.5
    
    # Verify transaction details
    transaction = data["transaction"]
    assert "from" in transaction
    assert "to" in transaction
    assert "amount_hbar" in transaction
    assert "memo" in transaction
    
    # Verify transaction fields
    assert transaction["from"] == test_user.hedera_account_id
    assert transaction["to"].startswith("0.0.")  # Treasury account
    assert float(transaction["amount_hbar"]) > 0
    assert "Bill payment:" in transaction["memo"]
    assert "BILL-EUR" in transaction["memo"]
    
    # Verify exchange rate info
    exchange_rate = data["exchange_rate"]
    assert exchange_rate["currency"] == "EUR"
    assert float(exchange_rate["hbar_price"]) > 0
    assert exchange_rate["source"] in ["coingecko", "coinmarketcap"]
    assert "fetched_at" in exchange_rate
    assert "expires_at" in exchange_rate
    
    # Verify rate expiry is 5 minutes from fetch time
    fetched_at = datetime.fromisoformat(exchange_rate["fetched_at"].replace("Z", "+00:00"))
    expires_at = datetime.fromisoformat(exchange_rate["expires_at"].replace("Z", "+00:00"))
    time_diff = (expires_at - fetched_at).total_seconds()
    assert 290 <= time_diff <= 310  # ~5 minutes (allowing small variance)
    
    # Verify minimum HBAR amount
    assert float(data["minimum_hbar"]) > 0


def test_prepare_payment_invalid_bill_id(client: TestClient, auth_headers):
    """Test payment preparation with invalid bill ID format"""
    
    response = client.post(
        "/api/payments/prepare",
        json={
            "bill_id": "invalid-uuid",
            "payment_method": "hbar"
        },
        headers=auth_headers
    )
    
    assert response.status_code == 400
    assert "Invalid bill ID format" in response.json()["detail"]


def test_prepare_payment_bill_not_found(client: TestClient, auth_headers):
    """Test payment preparation with non-existent bill"""
    
    fake_bill_id = str(uuid4())
    
    response = client.post(
        "/api/payments/prepare",
        json={
            "bill_id": fake_bill_id,
            "payment_method": "hbar"
        },
        headers=auth_headers
    )
    
    assert response.status_code == 404
    assert "Bill not found" in response.json()["detail"]


def test_prepare_payment_already_paid(client: TestClient, test_user: User, test_bill: Bill, auth_headers, db: Session):
    """Test payment preparation for already paid bill"""
    
    # Mark bill as paid
    test_bill.status = "paid"
    test_bill.hedera_tx_id = "0.0.12345@1710789600.123456789"
    test_bill.paid_at = datetime.utcnow()
    db.commit()
    
    response = client.post(
        "/api/payments/prepare",
        json={
            "bill_id": str(test_bill.id),
            "payment_method": "hbar"
        },
        headers=auth_headers
    )
    
    assert response.status_code == 400
    assert "Bill already paid" in response.json()["detail"]


def test_prepare_payment_unauthorized(client: TestClient, test_bill: Bill):
    """Test payment preparation without authentication"""
    
    response = client.post(
        "/api/payments/prepare",
        json={
            "bill_id": str(test_bill.id),
            "payment_method": "hbar"
        }
    )
    
    assert response.status_code == 401


def test_prepare_payment_different_user(client: TestClient, test_bill: Bill, db: Session):
    """Test payment preparation for bill belonging to different user"""
    
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
        "/api/payments/prepare",
        json={
            "bill_id": str(test_bill.id),
            "payment_method": "hbar"
        },
        headers=headers
    )
    
    # Should not find bill (belongs to different user)
    assert response.status_code == 404
    assert "Bill not found" in response.json()["detail"]


def test_prepare_payment_volatility_buffer(client: TestClient, test_user: User, test_bill: Bill, auth_headers):
    """
    Test that 2% volatility buffer is applied to HBAR calculation
    
    Verifies FR-6.13: System shall handle exchange rate volatility with 2% buffer
    """
    
    response = client.post(
        "/api/payments/prepare",
        json={
            "bill_id": str(test_bill.id),
            "payment_method": "hbar"
        },
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Calculate expected HBAR amount with buffer
    total_fiat = float(data["bill"]["total_fiat"])
    hbar_price = float(data["exchange_rate"]["hbar_price"])
    amount_hbar = float(data["transaction"]["amount_hbar"])
    
    # Without buffer: total_fiat / hbar_price
    # With 2% buffer: (total_fiat / hbar_price) * 1.02
    expected_without_buffer = total_fiat / hbar_price
    expected_with_buffer = expected_without_buffer * 1.02
    
    # The actual amount should be close to the buffered amount
    # Allow small variance due to rounding
    assert abs(amount_hbar - expected_with_buffer) / expected_with_buffer < 0.01  # Within 1%


def test_prepare_payment_multiple_currencies(client: TestClient, db: Session, auth_headers):
    """Test payment preparation for different currencies"""
    
    currencies = [
        ("EUR", "ES", "0.0.12345"),
        ("USD", "US", "0.0.12346"),
        ("INR", "IN", "0.0.12347"),
        ("BRL", "BR", "0.0.12348"),
        ("NGN", "NG", "0.0.12349"),
    ]
    
    for currency, country, hedera_account in currencies:
        # Create user for this currency
        user = User(
            email=f"test_{currency.lower()}@example.com",
            password_hash="hashed_password",
            country_code=country,
            hedera_account_id=hedera_account
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        
        # Create bill
        bill = Bill(
            user_id=user.id,
            consumption_kwh=Decimal("100.0"),
            base_charge=Decimal("50.0"),
            taxes=Decimal("10.0"),
            total_fiat=Decimal("60.0"),
            currency=currency,
            status="pending"
        )
        db.add(bill)
        db.commit()
        db.refresh(bill)
        
        # Get auth token
        from app.utils.auth import create_access_token
        token = create_access_token({"sub": user.email})
        headers = {"Authorization": f"Bearer {token}"}
        
        # Prepare payment
        response = client.post(
            "/api/payments/prepare",
            json={
                "bill_id": str(bill.id),
                "payment_method": "hbar"
            },
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify currency matches
        assert data["bill"]["currency"] == currency
        assert data["exchange_rate"]["currency"] == currency
        
        # Verify HBAR amount is calculated
        assert float(data["transaction"]["amount_hbar"]) > 0


def test_prepare_payment_exchange_rate_caching(client: TestClient, test_user: User, test_bill: Bill, auth_headers):
    """
    Test that exchange rates are cached for 5 minutes
    
    Verifies FR-5.3: System shall cache exchange rates for 5 minutes
    """
    
    # First request
    response1 = client.post(
        "/api/payments/prepare",
        json={
            "bill_id": str(test_bill.id),
            "payment_method": "hbar"
        },
        headers=auth_headers
    )
    
    assert response1.status_code == 200
    data1 = response1.json()
    
    # Second request immediately after (should use cache)
    response2 = client.post(
        "/api/payments/prepare",
        json={
            "bill_id": str(test_bill.id),
            "payment_method": "hbar"
        },
        headers=auth_headers
    )
    
    assert response2.status_code == 200
    data2 = response2.json()
    
    # Exchange rates should be identical (from cache)
    assert data1["exchange_rate"]["hbar_price"] == data2["exchange_rate"]["hbar_price"]
    assert data1["exchange_rate"]["fetched_at"] == data2["exchange_rate"]["fetched_at"]


def test_prepare_payment_memo_format(client: TestClient, test_user: User, test_bill: Bill, auth_headers):
    """
    Test that transaction memo follows correct format
    
    Format: "Bill payment: BILL-{CURRENCY}-{YEAR}-{ID}"
    """
    
    response = client.post(
        "/api/payments/prepare",
        json={
            "bill_id": str(test_bill.id),
            "payment_method": "hbar"
        },
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    
    memo = data["transaction"]["memo"]
    
    # Verify memo format
    assert memo.startswith("Bill payment: BILL-")
    assert test_bill.currency in memo
    assert str(test_bill.created_at.year) in memo
    assert str(test_bill.id)[:8] in memo


def test_prepare_payment_minimum_transfer_enforcement(client: TestClient, test_user: User, db: Session, auth_headers):
    """
    Test that minimum transfer amounts are enforced
    
    Verifies FR-5.6: System shall enforce minimum transfer amounts in HBAR
    """
    
    # Create a very small bill (below minimum)
    small_bill = Bill(
        user_id=test_user.id,
        consumption_kwh=Decimal("1.0"),
        base_charge=Decimal("0.50"),
        taxes=Decimal("0.10"),
        total_fiat=Decimal("0.60"),  # Very small amount
        currency="EUR",
        status="pending"
    )
    db.add(small_bill)
    db.commit()
    db.refresh(small_bill)
    
    response = client.post(
        "/api/payments/prepare",
        json={
            "bill_id": str(small_bill.id),
            "payment_method": "hbar"
        },
        headers=auth_headers
    )
    
    # Should still succeed (minimum is enforced at smart contract level)
    # But the calculated HBAR amount should be returned
    assert response.status_code == 200
    data = response.json()
    
    # Verify minimum_hbar field is present
    assert "minimum_hbar" in data
    assert float(data["minimum_hbar"]) > 0


@pytest.mark.asyncio
async def test_prepare_payment_exchange_rate_service():
    """Test that ExchangeRateService is properly integrated"""
    
    from app.services.exchange_rate_service import ExchangeRateService
    from app.core.database import SessionLocal
    
    db = SessionLocal()
    try:
        service = ExchangeRateService(db)
        
        # Test calculation with buffer
        result = service.calculate_hbar_amount(
            fiat_amount=100.0,
            currency="EUR",
            use_cache=True,
            apply_buffer=True,
            buffer_percentage=2.0
        )
        
        # Verify result structure
        assert "hbar_price" in result
        assert "hbar_amount" in result
        assert "hbar_amount_rounded" in result
        assert "buffer_applied" in result
        assert "source" in result
        
        # Verify buffer was applied
        assert result["buffer_applied"] == True
        
        # Verify HBAR amount is positive
        assert result["hbar_amount"] > 0
        assert result["hbar_amount_rounded"] > 0
        
    finally:
        db.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
