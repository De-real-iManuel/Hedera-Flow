"""
Payment Flow Integration Example - Task 16.5

This example demonstrates how the HBAR calculation will be integrated
into the payment preparation endpoint (Task 17.1).
"""
from typing import Dict, Any
from decimal import Decimal
from unittest.mock import Mock
from app.services.exchange_rate_service import ExchangeRateService


def prepare_payment_example(bill_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Example of how calculate_hbar_amount will be used in payment preparation.
    
    This simulates the POST /api/payments/prepare endpoint (Task 17.1).
    
    Args:
        bill_data: Dictionary containing bill information
        
    Returns:
        Payment preparation data with HBAR amount
    """
    # Extract bill details
    bill_id = bill_data['id']
    total_fiat = bill_data['total_fiat']
    currency = bill_data['currency']
    user_account = bill_data['user_hedera_account']
    utility_account = bill_data['utility_hedera_account']
    
    # Initialize exchange rate service
    db = Mock()  # In real code, this would be the actual database session
    exchange_service = ExchangeRateService(db)
    
    # Calculate HBAR amount with 2% buffer for volatility protection
    hbar_calculation = exchange_service.calculate_hbar_amount(
        fiat_amount=total_fiat,
        currency=currency,
        use_cache=True,
        apply_buffer=True,
        buffer_percentage=2.0
    )
    
    # Prepare payment response
    payment_data = {
        'bill': {
            'id': bill_id,
            'total_fiat': total_fiat,
            'currency': currency,
            'amount_hbar': hbar_calculation['hbar_amount_rounded'],
            'exchange_rate': hbar_calculation['hbar_price'],
            'exchange_rate_timestamp': hbar_calculation['exchange_rate_timestamp'],
            'buffer_applied': hbar_calculation['buffer_applied'],
            'buffer_percentage': hbar_calculation['buffer_percentage']
        },
        'transaction': {
            'from': user_account,
            'to': utility_account,
            'amount': hbar_calculation['hbar_amount_rounded'],
            'memo': f"Bill payment: {bill_id}"
        },
        'display': {
            'fiat_display': f"{currency} {total_fiat:,.2f}",
            'hbar_display': f"{hbar_calculation['hbar_amount_rounded']:.8f} HBAR",
            'rate_display': f"1 HBAR = {hbar_calculation['hbar_price']} {currency}",
            'rate_expires_in': '5 minutes'
        }
    }
    
    return payment_data


def main():
    """Demonstrate payment flow for all regions"""
    
    print("\n" + "=" * 70)
    print("PAYMENT FLOW INTEGRATION EXAMPLE")
    print("=" * 70 + "\n")
    
    # Example bills from different regions
    example_bills = [
        {
            'id': 'BILL-ES-2024-001',
            'total_fiat': 85.40,
            'currency': 'EUR',
            'user_hedera_account': '0.0.123456',
            'utility_hedera_account': '0.0.IBERDROLA',
            'region': 'Spain'
        },
        {
            'id': 'BILL-US-2024-001',
            'total_fiat': 120.50,
            'currency': 'USD',
            'user_hedera_account': '0.0.123457',
            'utility_hedera_account': '0.0.PGE',
            'region': 'USA'
        },
        {
            'id': 'BILL-IN-2024-001',
            'total_fiat': 450.00,
            'currency': 'INR',
            'user_hedera_account': '0.0.123458',
            'utility_hedera_account': '0.0.TPDDL',
            'region': 'India'
        },
        {
            'id': 'BILL-BR-2024-001',
            'total_fiat': 95.00,
            'currency': 'BRL',
            'user_hedera_account': '0.0.123459',
            'utility_hedera_account': '0.0.ENEL',
            'region': 'Brazil'
        },
        {
            'id': 'BILL-NG-2024-001',
            'total_fiat': 12500.00,
            'currency': 'NGN',
            'user_hedera_account': '0.0.123460',
            'utility_hedera_account': '0.0.IKEDP',
            'region': 'Nigeria'
        }
    ]
    
    # Mock exchange rates
    exchange_rates = {
        'EUR': 0.34,
        'USD': 0.38,
        'INR': 28.5,
        'BRL': 1.75,
        'NGN': 540.0
    }
    
    for bill in example_bills:
        print(f"Region: {bill['region']}")
        print(f"Bill ID: {bill['id']}")
        print("-" * 70)
        
        # Mock the exchange rate service
        ExchangeRateService.get_hbar_price = lambda self, c, use_cache=True: exchange_rates[c]
        
        # Prepare payment
        payment = prepare_payment_example(bill)
        
        # Display payment details
        print(f"\n📄 Bill Details:")
        print(f"   Amount: {payment['display']['fiat_display']}")
        print(f"   Currency: {bill['currency']}")
        
        print(f"\n💰 HBAR Calculation:")
        print(f"   Exchange Rate: {payment['display']['rate_display']}")
        print(f"   HBAR Amount: {payment['display']['hbar_display']}")
        print(f"   Buffer Applied: {payment['bill']['buffer_applied']} ({payment['bill']['buffer_percentage']}%)")
        
        print(f"\n🔗 Transaction Details:")
        print(f"   From: {payment['transaction']['from']}")
        print(f"   To: {payment['transaction']['to']}")
        print(f"   Amount: {payment['transaction']['amount']:.8f} HBAR")
        print(f"   Memo: {payment['transaction']['memo']}")
        
        print(f"\n⏰ Rate Validity:")
        print(f"   Timestamp: {payment['bill']['exchange_rate_timestamp']}")
        print(f"   Expires In: {payment['display']['rate_expires_in']}")
        
        print("\n" + "=" * 70 + "\n")
    
    print("✅ Payment flow integration working correctly!")
    print("\nNext Steps:")
    print("  1. Implement POST /api/payments/prepare endpoint (Task 17.1)")
    print("  2. Add rate lock mechanism (Task 17.4)")
    print("  3. Integrate with HashPack wallet (Task 18.5)")
    print("  4. Implement payment confirmation (Task 19.1)")


if __name__ == '__main__':
    main()
