#!/usr/bin/env python3
"""
Demo script for 2% volatility buffer (Task 16.6)

This script demonstrates how the volatility buffer protects users
from HBAR price fluctuations during the payment window.
"""

from decimal import Decimal


def calculate_hbar_without_buffer(fiat_amount: float, hbar_price: float) -> float:
    """Calculate HBAR amount without buffer"""
    return fiat_amount / hbar_price


def calculate_hbar_with_buffer(fiat_amount: float, hbar_price: float, buffer_pct: float = 2.0) -> float:
    """Calculate HBAR amount with buffer"""
    effective_fiat = fiat_amount * (1 + buffer_pct / 100)
    return effective_fiat / hbar_price


def demo_scenario(name: str, fiat_amount: float, currency: str, 
                  initial_price: float, final_price: float):
    """Demonstrate a volatility scenario"""
    print(f"\n{'='*70}")
    print(f"SCENARIO: {name}")
    print(f"{'='*70}")
    
    # Calculate amounts
    hbar_no_buffer = calculate_hbar_without_buffer(fiat_amount, initial_price)
    hbar_with_buffer = calculate_hbar_with_buffer(fiat_amount, initial_price, 2.0)
    
    # Price change
    price_change_pct = ((final_price - initial_price) / initial_price) * 100
    
    # What's needed at final price
    hbar_needed_at_final = calculate_hbar_without_buffer(fiat_amount, final_price)
    
    print(f"\n📊 Bill Details:")
    print(f"   Amount: {currency}{fiat_amount:.2f}")
    print(f"   Initial HBAR Price: {currency}{initial_price:.4f}")
    print(f"   Final HBAR Price: {currency}{final_price:.4f}")
    print(f"   Price Change: {price_change_pct:+.2f}%")
    
    print(f"\n💰 HBAR Calculations:")
    print(f"   Without Buffer: {hbar_no_buffer:.2f} HBAR")
    print(f"   With 2% Buffer: {hbar_with_buffer:.2f} HBAR")
    print(f"   Buffer Amount: {hbar_with_buffer - hbar_no_buffer:.2f} HBAR")
    
    print(f"\n🎯 At Transaction Time:")
    print(f"   HBAR Needed: {hbar_needed_at_final:.2f} HBAR")
    print(f"   HBAR Available: {hbar_with_buffer:.2f} HBAR")
    
    # Determine outcome
    if hbar_with_buffer >= hbar_needed_at_final:
        surplus = hbar_with_buffer - hbar_needed_at_final
        print(f"\n✅ SUCCESS: Transaction covered!")
        print(f"   Surplus: {surplus:.2f} HBAR ({surplus/hbar_with_buffer*100:.1f}%)")
    else:
        shortage = hbar_needed_at_final - hbar_with_buffer
        print(f"\n❌ FAILURE: Insufficient HBAR!")
        print(f"   Shortage: {shortage:.2f} HBAR ({shortage/hbar_needed_at_final*100:.1f}%)")


def main():
    """Run demo scenarios"""
    print("\n" + "="*70)
    print("2% VOLATILITY BUFFER DEMONSTRATION")
    print("Task 16.6 - Price Protection for HBAR Payments")
    print("="*70)
    
    # Scenario 1: Small price increase (within buffer)
    demo_scenario(
        name="Small Price Increase (1.5%)",
        fiat_amount=85.40,
        currency="€",
        initial_price=0.34,
        final_price=0.345
    )
    
    # Scenario 2: Exactly 2% increase (buffer limit)
    demo_scenario(
        name="Exactly 2% Price Increase",
        fiat_amount=85.40,
        currency="€",
        initial_price=0.34,
        final_price=0.3468
    )
    
    # Scenario 3: Large price increase (exceeds buffer)
    demo_scenario(
        name="Large Price Increase (3%)",
        fiat_amount=85.40,
        currency="€",
        initial_price=0.34,
        final_price=0.3502
    )
    
    # Scenario 4: Price decrease (user benefits)
    demo_scenario(
        name="Price Decrease (2%)",
        fiat_amount=85.40,
        currency="€",
        initial_price=0.34,
        final_price=0.3332
    )
    
    # Scenario 5: USA example
    demo_scenario(
        name="USA Bill with 1% Increase",
        fiat_amount=120.50,
        currency="$",
        initial_price=0.38,
        final_price=0.3838
    )
    
    # Scenario 6: Nigeria example
    demo_scenario(
        name="Nigeria Bill with 1.8% Increase",
        fiat_amount=12500.00,
        currency="₦",
        initial_price=425.00,
        final_price=432.65
    )
    
    # Summary
    print(f"\n{'='*70}")
    print("SUMMARY")
    print(f"{'='*70}")
    print("\n✅ Buffer Protection:")
    print("   • Covers price increases up to 2%")
    print("   • Reduces failed transactions")
    print("   • Transparent to users")
    print("\n⚠️ Limitations:")
    print("   • Price increases > 2% may require additional HBAR")
    print("   • Mitigated by 5-minute rate lock")
    print("\n💡 Best Practices:")
    print("   • Always apply buffer in production")
    print("   • Monitor volatility and adjust if needed")
    print("   • Combine with rate lock for maximum protection")
    print(f"\n{'='*70}\n")


if __name__ == "__main__":
    main()
