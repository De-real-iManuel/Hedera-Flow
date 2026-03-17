"""
Test Task 17.6: Return payment preparation data to frontend

This test verifies that the prepare_payment endpoint returns all required data
according to the API specification in design.md (Section 4.4) and requirements
for US-7 (Payment with HBAR).

Requirements Verified:
- FR-6.1: System shall fetch current HBAR price from exchange API
- FR-6.2: System shall calculate HBAR amount = (fiat_bill_amount / hbar_price)
- FR-6.6: System shall generate transaction with memo
- FR-6.13: System shall handle exchange rate volatility with 2% buffer
- US-7: Payment with HBAR (Native Token)
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
from decimal import Decimal
import os

from main import app
from app.core.database import Base, get_db
from app.models.user import User
from app.models.meter import Meter
from app.models.bill import Bill
from app.models.utility_provider import UtilityProvider
from app.utils.auth import create_access_token

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_task_17_6.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


@pytest.fixture(scope="function")
def setup_database():
    """Create test database and tables"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    # Clean up test database file
    if os.path.exists("./test_task_17_6.db"):
        os.remove("./test_task_17_6.db")


@pytest.fixture
def test_user(setup_database):
    """Create a test user"""
    db = TestingSessionLocal()
    user = User(
        email="test@example.com",
        password_hash="hashed_password",
        country_code="ES",
        hedera_account_id="0.0.123456"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Create access token
    token = create_access_token(data={"sub": user.email})
    
    yield {"user": user, "token": token}
    db.close()


@pytest.fixture
def test_utility_provider(setup_database):
    """Create a test utility provider"""
    db = TestingSessionLocal()
    provider = UtilityProvider(
        country_code="ES",
        state_province="Madrid",
        provider_name="Iberdrola",
        provider_code="IBERDROLA",
        hedera_account_id="0.0.789012"
    )
    db.add(provider)
    db.commit()
    db.refresh(provider)
    yield provider
    db.close()


@pytest.fixture
def test_bill(test_user, test_utility_provider):
    """Create a test bill"""
    db = TestingSessionLocal()
    user = test_user["user"]
    
    # Create meter
    meter = Meter(
        user_id=user.id,
        meter_id="ESP-12345678",
        utility_provider_id=test_utility_provider.id,
        state_province="Madrid",
        utility_provider="Iberdrola",
        meter_type="postpaid"
    )
    db.add(meter)
    db.commit()
    db.refresh(meter)
    
    # Create bill
    bill = Bill(
        user_id=user.id,
        meter_id=meter.id,
        consumption_kwh=Decimal("150.5"),
        base_charge=Decimal("70.50"),
        taxes=Decimal("14.90"),
        total_fiat=Decimal("85.40"),
        currency="EUR",
        status="pending"
    )
    db.add(bill)
    db.commit()
    db.refresh(bill)
    
    yield bill
    db.close()


def test_prepare_payment_returns_all_required_fields(test_user, test_bill):
    """
    Test that prepare_payment endpoint returns all required fields
    according to the API specification
    """
    # Prepare request
    headers = {"Authorization": f"Bearer {test_user['token']}"}
    payload = {
        "bill_id": str(test_bill.id)
    }
    
    # Make request
    response = client.post("/api/payments/prepare", json=payload, headers=headers)
    
    # Verify response status
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    
    data = response.json()
    
    # Verify top-level structure
    assert "bill" in data, "Response missing 'bill' field"
    assert "transaction" in data, "Response missing 'transaction' field"
    assert "exchange_rate" in data, "Response missing 'exchange_rate' field"
    assert "minimum_hbar" in data, "Response missing 'minimum_hbar' field"
    
    # Verify bill details (FR-6.2, US-7)
    bill = data["bill"]
    assert "id" in bill, "Bill missing 'id' field"
    assert "total_fiat" in bill, "Bill missing 'total_fiat' field"
    assert "currency" in bill, "Bill missing 'currency' field"
    assert "consumption_kwh" in bill, "Bill missing 'consumption_kwh' field"
    
    assert bill["id"] == str(test_bill.id)
    assert bill["total_fiat"] == 85.40
    assert bill["currency"] == "EUR"
    assert bill["consumption_kwh"] == 150.5
    
    # Verify transaction details (FR-6.6, US-7)
    transaction = data["transaction"]
    assert "from" in transaction, "Transaction missing 'from' field"
    assert "to" in transaction, "Transaction missing 'to' field"
    assert "amount_hbar" in transaction, "Transaction missing 'amount_hbar' field"
    assert "memo" in transaction, "Transaction missing 'memo' field"
    
    assert transaction["from"] == "0.0.123456", "Transaction 'from' should be user's Hedera account"
    assert transaction["to"] == "0.0.789012", "Transaction 'to' should be utility's Hedera account"
    assert float(transaction["amount_hbar"]) > 0, "HBAR amount should be positive"
    assert "BILL-EUR" in transaction["memo"], "Memo should contain bill reference"
    
    # Verify exchange rate info (FR-6.1, FR-6.13)
    exchange_rate = data["exchange_rate"]
    assert "currency" in exchange_rate, "Exchange rate missing 'currency' field"
    assert "hbar_price" in exchange_rate, "Exchange rate missing 'hbar_price' field"
    assert "source" in exchange_rate, "Exchange rate missing 'source' field"
    assert "fetched_at" in exchange_rate, "Exchange rate missing 'fetched_at' field"
    assert "expires_at" in exchange_rate, "Exchange rate missing 'expires_at' field"
    
    assert exchange_rate["currency"] == "EUR"
    assert float(exchange_rate["hbar_price"]) > 0, "HBAR price should be positive"
    assert exchange_rate["source"] in ["coingecko", "coinmarketcap"], "Source should be valid"
    
    # Verify expiry is 5 minutes from now (FR-6.13)
    fetched_at = datetime.fromisoformat(exchange_rate["fetched_at"].replace("Z", "+00:00"))
    expires_at = datetime.fromisoformat(exchange_rate["expires_at"].replace("Z", "+00:00"))
    expiry_duration = (expires_at - fetched_at).total_seconds()
    assert 290 <= expiry_duration <= 310, f"Expiry should be ~5 minutes (300s), got {expiry_duration}s"
    
    # Verify minimum HBAR amount
    assert float(data["minimum_hbar"]) > 0, "Minimum HBAR should be positive"
    
    print("✅ All required fields present and valid")


def test_prepare_payment_calculates_hbar_correctly(test_user, test_bill):
    """
    Test that HBAR amount is calculated correctly with 2% buffer
    (FR-6.2, FR-6.13)
    """
    headers = {"Authorization": f"Bearer {test_user['token']}"}
    payload = {"bill_id": str(test_bill.id)}
    
    response = client.post("/api/payments/prepare", json=payload, headers=headers)
    assert response.status_code == 200
    
    data = response.json()
    
    # Get values
    total_fiat = float(data["bill"]["total_fiat"])
    hbar_price = float(data["exchange_rate"]["hbar_price"])
    amount_hbar = float(data["transaction"]["amount_hbar"])
    
    # Calculate expected HBAR amount with 2% buffer
    expected_hbar_no_buffer = total_fiat / hbar_price
    expected_hbar_with_buffer = expected_hbar_no_buffer * 1.02
    
    # Verify the amount includes buffer (should be ~2% more than without buffer)
    buffer_ratio = amount_hbar / expected_hbar_no_buffer
    assert 1.01 <= buffer_ratio <= 1.03, f"Buffer should be ~2%, got {(buffer_ratio - 1) * 100:.2f}%"
    
    print(f"✅ HBAR calculation correct: {total_fiat} EUR = {amount_hbar} HBAR @ {hbar_price} EUR/HBAR (with 2% buffer)")


def test_prepare_payment_generates_correct_memo(test_user, test_bill):
    """
    Test that transaction memo is generated correctly
    (FR-6.6, US-7)
    """
    headers = {"Authorization": f"Bearer {test_user['token']}"}
    payload = {"bill_id": str(test_bill.id)}
    
    response = client.post("/api/payments/prepare", json=payload, headers=headers)
    assert response.status_code == 200
    
    data = response.json()
    memo = data["transaction"]["memo"]
    
    # Verify memo format: "Bill payment: BILL-{CURRENCY}-{YEAR}-{ID}"
    assert memo.startswith("Bill payment: BILL-"), "Memo should start with 'Bill payment: BILL-'"
    assert "EUR" in memo, "Memo should contain currency"
    assert str(datetime.now().year) in memo, "Memo should contain current year"
    assert str(test_bill.id)[:8] in memo, "Memo should contain bill ID prefix"
    
    print(f"✅ Memo format correct: {memo}")


def test_prepare_payment_invalid_bill_id(test_user):
    """
    Test error handling for invalid bill ID
    """
    headers = {"Authorization": f"Bearer {test_user['token']}"}
    payload = {"bill_id": "invalid-uuid"}
    
    response = client.post("/api/payments/prepare", json=payload, headers=headers)
    assert response.status_code == 400
    assert "Invalid bill ID format" in response.json()["detail"]
    
    print("✅ Invalid bill ID handled correctly")


def test_prepare_payment_bill_not_found(test_user):
    """
    Test error handling for non-existent bill
    """
    headers = {"Authorization": f"Bearer {test_user['token']}"}
    payload = {"bill_id": "00000000-0000-0000-0000-000000000000"}
    
    response = client.post("/api/payments/prepare", json=payload, headers=headers)
    assert response.status_code == 404
    assert "Bill not found" in response.json()["detail"]
    
    print("✅ Non-existent bill handled correctly")


def test_prepare_payment_already_paid(test_user, test_bill):
    """
    Test error handling for already paid bill
    """
    # Mark bill as paid
    db = TestingSessionLocal()
    test_bill.status = "paid"
    db.add(test_bill)
    db.commit()
    db.close()
    
    headers = {"Authorization": f"Bearer {test_user['token']}"}
    payload = {"bill_id": str(test_bill.id)}
    
    response = client.post("/api/payments/prepare", json=payload, headers=headers)
    assert response.status_code == 400
    assert "Bill already paid" in response.json()["detail"]
    
    print("✅ Already paid bill handled correctly")


def test_prepare_payment_uses_utility_hedera_account(test_user, test_bill, test_utility_provider):
    """
    Test that payment is directed to utility provider's Hedera account
    (US-7)
    """
    headers = {"Authorization": f"Bearer {test_user['token']}"}
    payload = {"bill_id": str(test_bill.id)}
    
    response = client.post("/api/payments/prepare", json=payload, headers=headers)
    assert response.status_code == 200
    
    data = response.json()
    
    # Verify transaction goes to utility provider's account
    assert data["transaction"]["to"] == test_utility_provider.hedera_account_id
    assert data["transaction"]["from"] == "0.0.123456"  # User's account
    
    print(f"✅ Payment directed to utility provider: {test_utility_provider.hedera_account_id}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
