"""
Visual Test for Receipt with QR Code
Generates a sample receipt PDF to verify QR code appearance
"""
import os
from datetime import datetime
from decimal import Decimal

from app.services.receipt_service import get_receipt_service


def test_generate_sample_receipt_with_qr():
    """Generate a sample receipt PDF with QR code for visual inspection"""
    receipt_service = get_receipt_service()
    
    # Sample bill data
    bill_data = {
        'bill_id': '123e4567-e89b-12d3-a456-426614174000',
        'consumption_kwh': Decimal('450.5'),
        'base_charge': Decimal('75.00'),
        'taxes': Decimal('15.75'),
        'subsidies': Decimal('0.00'),
        'total_fiat': Decimal('90.75'),
        'currency': 'EUR',
        'amount_hbar': Decimal('267.05882353'),
        'exchange_rate': Decimal('0.34'),
        'hedera_tx_id': '0.0.123456@1710789700.123456789',
        'consensus_timestamp': datetime(2024, 3, 18, 15, 30, 0),
        'paid_at': datetime(2024, 3, 18, 15, 30, 5),
        'user_email': 'test@hederaflow.com',
        'meter_id': 'ESP-12345678'
    }
    
    # Generate receipt
    output_path = 'tests/sample_receipt_with_qr.pdf'
    pdf_bytes = receipt_service.generate_receipt_pdf(bill_data, output_path)
    
    # Verify file was created
    assert os.path.exists(output_path)
    assert len(pdf_bytes) > 0
    
    print(f"\n✓ Sample receipt generated: {output_path}")
    print(f"  File size: {len(pdf_bytes)} bytes")
    print(f"  QR code links to: https://hashscan.io/testnet/transaction/{bill_data['hedera_tx_id']}")
    print("\nPlease open the PDF to verify:")
    print("  1. QR code is visible and properly sized")
    print("  2. QR code has descriptive label")
    print("  3. QR code is positioned appropriately")
    print("  4. QR code is scannable with mobile device")


if __name__ == '__main__':
    test_generate_sample_receipt_with_qr()
