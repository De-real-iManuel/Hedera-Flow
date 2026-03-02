"""
Generate sample receipts with itemized breakdown for visual inspection
"""
from datetime import datetime
from app.services.receipt_service import get_receipt_service


def generate_sample_receipts():
    """Generate sample receipts for all rate structures"""
    receipt_service = get_receipt_service()
    
    # 1. Tiered Rate (USA)
    print("Generating USA tiered rate receipt...")
    usa_bill_data = {
        'bill_id': '12345678-1234-1234-1234-123456789abc',
        'consumption_kwh': 850.00,
        'base_charge': 313.00,
        'taxes': 22.69,
        'subsidies': 0,
        'total_fiat': 345.69,
        'currency': 'USD',
        'amount_hbar': 6913.80,
        'exchange_rate': 0.05,
        'hedera_tx_id': '0.0.123456@1710789700.123456789',
        'consensus_timestamp': datetime(2024, 3, 18, 14, 30, 0),
        'paid_at': datetime(2024, 3, 18, 14, 30, 5),
        'user_email': 'test@example.com',
        'meter_id': 'USA-CA-87654321',
        'tariff_snapshot': {
            'rate_structure_type': 'tiered',
            'breakdown': {
                'tiers': [
                    {'tier': 'Tier 1 (0-400 kWh)', 'kwh': 400, 'rate': 0.32, 'charge': 128.00},
                    {'tier': 'Tier 2 (401-800 kWh)', 'kwh': 400, 'rate': 0.40, 'charge': 160.00},
                    {'tier': 'Tier 3 (801+ kWh)', 'kwh': 50, 'rate': 0.50, 'charge': 25.00}
                ]
            },
            'taxes_and_fees': {
                'vat': 0.0725,
                'service_charge': 10.00
            }
        },
        'breakdown': {
            'tiers': [
                {'tier': 'Tier 1 (0-400 kWh)', 'kwh': 400, 'rate': 0.32, 'charge': 128.00},
                {'tier': 'Tier 2 (401-800 kWh)', 'kwh': 400, 'rate': 0.40, 'charge': 160.00},
                {'tier': 'Tier 3 (801+ kWh)', 'kwh': 50, 'rate': 0.50, 'charge': 25.00}
            ]
        },
        'service_charge': 10.00,
        'tax_breakdown': {
            'vat': 22.69,
            'vat_rate': 0.0725,
            'other_taxes': 0
        }
    }
    
    pdf_bytes = receipt_service.generate_receipt_pdf(
        usa_bill_data,
        'tests/sample_receipt_usa_tiered.pdf'
    )
    print(f"✓ Generated: tests/sample_receipt_usa_tiered.pdf ({len(pdf_bytes)} bytes)")
    
    # 2. Time-of-Use (Spain)
    print("\nGenerating Spain time-of-use receipt...")
    spain_bill_data = {
        'bill_id': '87654321-4321-4321-4321-cba987654321',
        'consumption_kwh': 450.50,
        'base_charge': 125.13,
        'taxes': 26.28,
        'subsidies': 2.12,
        'total_fiat': 149.29,
        'currency': 'EUR',
        'amount_hbar': 438.79,
        'exchange_rate': 0.34,
        'hedera_tx_id': '0.0.654321@1710789800.987654321',
        'consensus_timestamp': datetime(2024, 3, 19, 10, 15, 30),
        'paid_at': datetime(2024, 3, 19, 10, 15, 35),
        'user_email': 'user@test.com',
        'meter_id': 'ESP-12345678',
        'tariff_snapshot': {
            'rate_structure_type': 'time_of_use',
            'breakdown': {
                'periods': [
                    {'period': 'Peak (10-14h, 18-22h)', 'kwh': 150.0, 'rate': 0.40, 'charge': 60.00},
                    {'period': 'Standard (8-10h, 14-18h, 22-24h)', 'kwh': 200.5, 'rate': 0.25, 'charge': 50.13},
                    {'period': 'Off-Peak (0-8h)', 'kwh': 100.0, 'rate': 0.15, 'charge': 15.00}
                ]
            },
            'taxes_and_fees': {
                'vat': 0.21,
                'distribution_charge': 0.045
            }
        },
        'breakdown': {
            'periods': [
                {'period': 'Peak (10-14h, 18-22h)', 'kwh': 150.0, 'rate': 0.40, 'charge': 60.00},
                {'period': 'Standard (8-10h, 14-18h, 22-24h)', 'kwh': 200.5, 'rate': 0.25, 'charge': 50.13},
                {'period': 'Off-Peak (0-8h)', 'kwh': 100.0, 'rate': 0.15, 'charge': 15.00}
            ]
        },
        'distribution_charge': 20.27,
        'tax_breakdown': {
            'vat': 26.28,
            'vat_rate': 0.21,
            'other_taxes': 0
        }
    }
    
    pdf_bytes = receipt_service.generate_receipt_pdf(
        spain_bill_data,
        'tests/sample_receipt_spain_time_of_use.pdf'
    )
    print(f"✓ Generated: tests/sample_receipt_spain_time_of_use.pdf ({len(pdf_bytes)} bytes)")
    
    # 3. Band-Based (Nigeria)
    print("\nGenerating Nigeria band-based receipt...")
    nigeria_bill_data = {
        'bill_id': 'abcdef12-abcd-abcd-abcd-abcdef123456',
        'consumption_kwh': 320.00,
        'base_charge': 16000.00,
        'taxes': 1200.00,
        'subsidies': 0,
        'total_fiat': 18700.00,
        'currency': 'NGN',
        'amount_hbar': 374000.00,
        'exchange_rate': 0.05,
        'hedera_tx_id': '0.0.789012@1710790000.111222333',
        'consensus_timestamp': datetime(2024, 3, 20, 8, 45, 15),
        'paid_at': datetime(2024, 3, 20, 8, 45, 20),
        'user_email': 'nigeria@test.com',
        'meter_id': 'NG-IKEDP-12345',
        'tariff_snapshot': {
            'rate_structure_type': 'band_based',
            'breakdown': {
                'band': 'C',
                'rate': 50.00
            },
            'taxes_and_fees': {
                'vat': 0.075,
                'service_charge': 1500.00
            }
        },
        'breakdown': {
            'band': 'C',
            'rate': 50.00
        },
        'service_charge': 1500.00,
        'tax_breakdown': {
            'vat': 1200.00,
            'vat_rate': 0.075,
            'other_taxes': 0
        }
    }
    
    pdf_bytes = receipt_service.generate_receipt_pdf(
        nigeria_bill_data,
        'tests/sample_receipt_nigeria_band_based.pdf'
    )
    print(f"✓ Generated: tests/sample_receipt_nigeria_band_based.pdf ({len(pdf_bytes)} bytes)")
    
    # 4. With Subsidies (India)
    print("\nGenerating India receipt with subsidies...")
    india_bill_data = {
        'bill_id': 'subsidy-1234-5678-9abc-def012345678',
        'consumption_kwh': 250.00,
        'base_charge': 1125.00,
        'taxes': 202.50,
        'subsidies': 150.00,
        'total_fiat': 1177.50,
        'currency': 'INR',
        'amount_hbar': 23550.00,
        'exchange_rate': 0.05,
        'hedera_tx_id': '0.0.111222@1710790100.444555666',
        'consensus_timestamp': datetime(2024, 3, 21, 12, 0, 0),
        'paid_at': datetime(2024, 3, 21, 12, 0, 5),
        'user_email': 'india@test.com',
        'meter_id': 'IN-TPDDL-54321',
        'tariff_snapshot': {
            'rate_structure_type': 'tiered',
            'breakdown': {
                'tiers': [
                    {'tier': 'Tier 1 (0-100 kWh)', 'kwh': 100, 'rate': 4.50, 'charge': 450.00},
                    {'tier': 'Tier 2 (101-300 kWh)', 'kwh': 150, 'rate': 6.00, 'charge': 900.00}
                ]
            },
            'taxes_and_fees': {
                'vat': 0.18
            }
        },
        'breakdown': {
            'tiers': [
                {'tier': 'Tier 1 (0-100 kWh)', 'kwh': 100, 'rate': 4.50, 'charge': 450.00},
                {'tier': 'Tier 2 (101-300 kWh)', 'kwh': 150, 'rate': 6.00, 'charge': 900.00}
            ]
        },
        'tax_breakdown': {
            'vat': 202.50,
            'vat_rate': 0.18,
            'other_taxes': 0
        }
    }
    
    pdf_bytes = receipt_service.generate_receipt_pdf(
        india_bill_data,
        'tests/sample_receipt_india_with_subsidies.pdf'
    )
    print(f"✓ Generated: tests/sample_receipt_india_with_subsidies.pdf ({len(pdf_bytes)} bytes)")
    
    # 5. With Platform Charges (Brazil)
    print("\nGenerating Brazil receipt with platform charges...")
    brazil_bill_data = {
        'bill_id': 'platform-1234-5678-9abc-def012345678',
        'consumption_kwh': 500.00,
        'base_charge': 350.00,
        'taxes': 73.50,
        'subsidies': 0,
        'total_fiat': 436.20,
        'currency': 'BRL',
        'amount_hbar': 8724.00,
        'exchange_rate': 0.05,
        'hedera_tx_id': '0.0.333444@1710790200.777888999',
        'consensus_timestamp': datetime(2024, 3, 22, 15, 30, 0),
        'paid_at': datetime(2024, 3, 22, 15, 30, 5),
        'user_email': 'brazil@test.com',
        'meter_id': 'BR-ENEL-98765',
        'tariff_snapshot': {
            'rate_structure_type': 'tiered',
            'breakdown': {
                'tiers': [
                    {'tier': 'Tier 1 (0-100 kWh)', 'kwh': 100, 'rate': 0.50, 'charge': 50.00},
                    {'tier': 'Tier 2 (101-300 kWh)', 'kwh': 200, 'rate': 0.70, 'charge': 140.00},
                    {'tier': 'Tier 3 (301+ kWh)', 'kwh': 200, 'rate': 0.90, 'charge': 180.00}
                ]
            },
            'taxes_and_fees': {
                'vat': 0.18
            }
        },
        'breakdown': {
            'tiers': [
                {'tier': 'Tier 1 (0-100 kWh)', 'kwh': 100, 'rate': 0.50, 'charge': 50.00},
                {'tier': 'Tier 2 (101-300 kWh)', 'kwh': 200, 'rate': 0.70, 'charge': 140.00},
                {'tier': 'Tier 3 (301+ kWh)', 'kwh': 200, 'rate': 0.90, 'charge': 180.00}
            ]
        },
        'platform_service_charge': 10.50,
        'platform_vat': 2.20,
        'tax_breakdown': {
            'vat': 73.50,
            'vat_rate': 0.18,
            'other_taxes': 0
        }
    }
    
    pdf_bytes = receipt_service.generate_receipt_pdf(
        brazil_bill_data,
        'tests/sample_receipt_brazil_with_platform.pdf'
    )
    print(f"✓ Generated: tests/sample_receipt_brazil_with_platform.pdf ({len(pdf_bytes)} bytes)")
    
    print("\n" + "="*60)
    print("✓ All sample receipts generated successfully!")
    print("="*60)
    print("\nGenerated files:")
    print("  1. tests/sample_receipt_usa_tiered.pdf")
    print("  2. tests/sample_receipt_spain_time_of_use.pdf")
    print("  3. tests/sample_receipt_nigeria_band_based.pdf")
    print("  4. tests/sample_receipt_india_with_subsidies.pdf")
    print("  5. tests/sample_receipt_brazil_with_platform.pdf")


if __name__ == '__main__':
    generate_sample_receipts()
