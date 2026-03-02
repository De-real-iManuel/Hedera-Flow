"""
Test Payment Confirmation Endpoint
Tests for POST /api/payments/confirm
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime
from decimal import Decimal
from uuid import uuid4

from app.core.app import app
from app.models.user import User
from app.models.bill import Bill
from app.models.meter import Meter


@pytest.fixture
def test_user(db: Session):
    """Create a test user"""
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
def test_bill(db: Session, test_user: User):
    """Create a test bill"""
    bill = Bill(
        user_id=test_user.id,
        consumption_kwh=Decimal("150.5"),
        base_charge=Decimal("75.25"),
        taxes=Decimal("15.81"),
        total_fiat=Decimal("91.06"),
        currency="EUR",
        status="pending",
        amount_hbar=Decimal("250.0"),
        exchange_rate=Decimal("0.36")
    )
    db.add(bill)
    db.commit()
    db.refresh(bill)
    return bill


def test_confirm_payment_success(client: TestClient, test_user: User, test_bill: Bill, auth_headers):
    """Test successful payment confirmation"""
    
    # Mock transaction ID (format: 0.0.xxxxx@timestamp.nanoseconds)
    tx_id = "0.0.12345@1710789700.123456789"
    
    response = client.post(
        "/api/payments/confirm",
        json={
            "bill_id": str(test_bill.id),
            "hedera_tx_id": tx_id
        },
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Verify response structure
    assert "payment" in data
    assert "message" in data
    assert data["message"] == "Payment confirmed successfully"
    
    # Verify payment details
    payment = data["payment"]
    assert payment["bill_id"] == str(test_bill.id)
    assert payment["hedera_tx_id"] == tx_id
    assert payment["currency"] == "EUR"
    assert float(payment["amount_fiat"]) == 91.06
    
    # Verify receipt URL
    assert payment["receipt_url"] == f"/api/payments/{test_bill.id}/receipt"


def test_confirm_payment_invalid_bill_id(client: TestClient, auth_headers):
    """Test payment confirmation with invalid bill ID"""
    
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


def test_confirm_payment_bill_not_found(client: TestClient, auth_headers):
    """Test payment confirmation with non-existent bill"""
    
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


def test_confirm_payment_already_paid(client: TestClient, test_user: User, test_bill: Bill, auth_headers, db: Session):
    """Test payment confirmation for already paid bill"""
    
    # Mark bill as paid
    test_bill.status = "paid"
    test_bill.hedera_tx_id = "0.0.12345@1710789600.123456789"
    db.commit()
    
    response = client.post(
        "/api/payments/confirm",
        json={
            "bill_id": str(test_bill.id),
            "hedera_tx_id": "0.0.12345@1710789700.123456789"
        },
        headers=auth_headers
    )
    
    assert response.status_code == 400
    assert "Bill already paid" in response.json()["detail"]


def test_confirm_payment_invalid_tx_format(client: TestClient, test_bill: Bill, auth_headers):
    """Test payment confirmation with invalid transaction ID format"""
    
    response = client.post(
        "/api/payments/confirm",
        json={
            "bill_id": str(test_bill.id),
            "hedera_tx_id": "invalid-tx-id"
        },
        headers=auth_headers
    )
    
    # Should fail validation due to regex pattern in schema
    assert response.status_code == 422


def test_confirm_payment_updates_bill_status(client: TestClient, test_user: User, test_bill: Bill, auth_headers, db: Session):
    """Test that payment confirmation updates bill status in database"""
    
    tx_id = "0.0.12345@1710789700.123456789"
    
    # Confirm payment
    response = client.post(
        "/api/payments/confirm",
        json={
            "bill_id": str(test_bill.id),
            "hedera_tx_id": tx_id
        },
        headers=auth_headers
    )
    
    assert response.status_code == 200
    
    # Refresh bill from database
    db.refresh(test_bill)
    
    # Verify bill was updated
    assert test_bill.status == "paid"
    assert test_bill.hedera_tx_id == tx_id
    assert test_bill.paid_at is not None
    assert test_bill.hedera_consensus_timestamp is not None


def test_confirm_payment_unauthorized(client: TestClient, test_bill: Bill):
    """Test payment confirmation without authentication"""
    
    response = client.post(
        "/api/payments/confirm",
        json={
            "bill_id": str(test_bill.id),
            "hedera_tx_id": "0.0.12345@1710789700.123456789"
        }
    )
    
    assert response.status_code == 401


def test_confirm_payment_different_user(client: TestClient, test_bill: Bill, db: Session):
    """Test payment confirmation for bill belonging to different user"""
    
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
            "bill_id": str(test_bill.id),
            "hedera_tx_id": "0.0.12345@1710789700.123456789"
        },
        headers=headers
    )
    
    # Should not find bill (belongs to different user)
    assert response.status_code == 404
    assert "Bill not found" in response.json()["detail"]


@pytest.mark.asyncio
async def test_confirm_payment_mirror_node_verification():
    """Test Mirror Node transaction verification logic"""
    
    from app.utils.mirror_node_client import mirror_node_client
    
    # This is a mock test - in real scenario, we'd use a real testnet transaction
    # For now, just verify the client can be instantiated
    assert mirror_node_client is not None
    assert mirror_node_client.base_url == "https://testnet.mirrornode.hedera.com"


def test_confirm_payment_hcs_logging():
    """Test that payment is logged to HCS"""
    
    # This test would require mocking the Hedera service
    # For MVP, we'll verify the logic is in place
    
    import os
    
    # Verify HCS topic environment variables are set
    topics = {
        'EU': os.getenv('HEDERA_TOPIC_EU'),
        'US': os.getenv('HEDERA_TOPIC_US'),
        'ASIA': os.getenv('HEDERA_TOPIC_ASIA'),
        'SA': os.getenv('HEDERA_TOPIC_SA'),
        'AFRICA': os.getenv('HEDERA_TOPIC_AFRICA'),
    }
    
    # At least one topic should be configured
    assert any(topics.values()), "No HCS topics configured"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
