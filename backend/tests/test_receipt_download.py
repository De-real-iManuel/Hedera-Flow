"""
Test Receipt Download Functionality

Tests for Task 20.6: Implement download functionality
- Requirements: US-7

This test verifies that:
1. Receipt endpoint returns PDF with correct Content-Disposition header
2. PDF can be downloaded with proper filename
3. Download works for authenticated users
4. Download fails for non-existent bills
5. Download fails for unpaid bills
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime
from decimal import Decimal

from app.core.app import app
from app.models.user import User
from app.models.bill import Bill
from app.models.meter import Meter
from app.utils.auth import create_access_token


@pytest.fixture
def test_client():
    """Create test client"""
    return TestClient(app)


@pytest.fixture
def test_user(db: Session):
    """Create test user"""
    user = User(
        email="test@example.com",
        password_hash="hashed_password",
        country_code="NG",
        hedera_account_id="0.0.123456"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def test_meter(db: Session, test_user: User):
    """Create test meter"""
    meter = Meter(
        user_id=test_user.id,
        meter_id="NG-12345678",
        utility_provider_id=None,
        state_province="Lagos",
        utility_provider="IKEDP",
        meter_type="postpaid"
    )
    db.add(meter)
    db.commit()
    db.refresh(meter)
    return meter


@pytest.fixture
def paid_bill(db: Session, test_user: User, test_meter: Meter):
    """Create paid bill"""
    bill = Bill(
        user_id=test_user.id,
        meter_id=test_meter.id,
        consumption_kwh=Decimal("250.5"),
        base_charge=Decimal("10000.00"),
        taxes=Decimal("750.00"),
        subsidies=Decimal("0.00"),
        total_fiat=Decimal("10750.00"),
        currency="NGN",
        amount_hbar=Decimal("215.00"),
        exchange_rate=Decimal("50.00"),
        exchange_rate_timestamp=datetime.utcnow(),
        status="paid",
        hedera_tx_id="0.0.123456@1234567890.123",
        hedera_consensus_timestamp=datetime.utcnow(),
        paid_at=datetime.utcnow()
    )
    db.add(bill)
    db.commit()
    db.refresh(bill)
    return bill


@pytest.fixture
def unpaid_bill(db: Session, test_user: User, test_meter: Meter):
    """Create unpaid bill"""
    bill = Bill(
        user_id=test_user.id,
        meter_id=test_meter.id,
        consumption_kwh=Decimal("250.5"),
        base_charge=Decimal("10000.00"),
        taxes=Decimal("750.00"),
        subsidies=Decimal("0.00"),
        total_fiat=Decimal("10750.00"),
        currency="NGN",
        status="pending"
    )
    db.add(bill)
    db.commit()
    db.refresh(bill)
    return bill


@pytest.fixture
def auth_headers(test_user: User):
    """Create authentication headers"""
    token = create_access_token({"sub": test_user.email})
    return {"Authorization": f"Bearer {token}"}


def test_download_receipt_success(test_client, paid_bill, auth_headers):
    """Test successful receipt download"""
    response = test_client.get(
        f"/api/payments/{paid_bill.id}/receipt",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    
    # Check Content-Disposition header for download
    content_disposition = response.headers.get("content-disposition")
    assert content_disposition is not None
    assert "attachment" in content_disposition
    assert "filename=" in content_disposition
    assert f"hedera-flow-receipt-{str(paid_bill.id)[:8]}.pdf" in content_disposition
    
    # Verify PDF content
    pdf_bytes = response.content
    assert len(pdf_bytes) > 0
    
    # Verify it starts with PDF magic bytes
    assert pdf_bytes[:4] == b'%PDF'


def test_download_receipt_filename_format(test_client, paid_bill, auth_headers):
    """Test receipt filename format"""
    response = test_client.get(
        f"/api/payments/{paid_bill.id}/receipt",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    
    # Extract filename from Content-Disposition header
    content_disposition = response.headers.get("content-disposition")
    assert "attachment" in content_disposition
    
    # Filename should be: hedera-flow-receipt-{first-8-chars-of-bill-id}.pdf
    expected_filename = f"hedera-flow-receipt-{str(paid_bill.id)[:8]}.pdf"
    assert expected_filename in content_disposition


def test_download_receipt_unauthenticated(test_client, paid_bill):
    """Test receipt download without authentication"""
    response = test_client.get(f"/api/payments/{paid_bill.id}/receipt")
    
    assert response.status_code == 401


def test_download_receipt_nonexistent_bill(test_client, auth_headers):
    """Test receipt download for non-existent bill"""
    fake_bill_id = "00000000-0000-0000-0000-000000000000"
    response = test_client.get(
        f"/api/payments/{fake_bill_id}/receipt",
        headers=auth_headers
    )
    
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_download_receipt_unpaid_bill(test_client, unpaid_bill, auth_headers):
    """Test receipt download for unpaid bill"""
    response = test_client.get(
        f"/api/payments/{unpaid_bill.id}/receipt",
        headers=auth_headers
    )
    
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_download_receipt_invalid_bill_id(test_client, auth_headers):
    """Test receipt download with invalid bill ID format"""
    response = test_client.get(
        "/api/payments/invalid-id/receipt",
        headers=auth_headers
    )
    
    assert response.status_code == 400
    assert "invalid" in response.json()["detail"].lower()


def test_download_receipt_pdf_content(test_client, paid_bill, auth_headers):
    """Test receipt PDF contains expected content"""
    response = test_client.get(
        f"/api/payments/{paid_bill.id}/receipt",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    
    # Verify PDF is valid
    pdf_bytes = response.content
    assert pdf_bytes[:4] == b'%PDF'
    
    # Verify PDF contains some expected text (basic check)
    # Note: Full text extraction would require PyPDF2 or similar library
    # For now, we just verify it's a valid PDF with content
    assert len(pdf_bytes) > 1000  # Should be a substantial PDF


def test_download_receipt_multiple_times(test_client, paid_bill, auth_headers):
    """Test downloading receipt multiple times (idempotent)"""
    # First download
    response1 = test_client.get(
        f"/api/payments/{paid_bill.id}/receipt",
        headers=auth_headers
    )
    assert response1.status_code == 200
    pdf1 = response1.content
    
    # Second download
    response2 = test_client.get(
        f"/api/payments/{paid_bill.id}/receipt",
        headers=auth_headers
    )
    assert response2.status_code == 200
    pdf2 = response2.content
    
    # Both downloads should produce identical PDFs
    assert pdf1 == pdf2


def test_download_receipt_different_users(test_client, db: Session, paid_bill, test_meter):
    """Test user can only download their own receipts"""
    # Create another user
    other_user = User(
        email="other@example.com",
        password_hash="hashed_password",
        country_code="NG",
        hedera_account_id="0.0.654321"
    )
    db.add(other_user)
    db.commit()
    
    # Create token for other user
    other_token = create_access_token({"sub": other_user.email})
    other_headers = {"Authorization": f"Bearer {other_token}"}
    
    # Try to download first user's receipt
    response = test_client.get(
        f"/api/payments/{paid_bill.id}/receipt",
        headers=other_headers
    )
    
    # Should fail - user can only access their own receipts
    assert response.status_code == 404


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
