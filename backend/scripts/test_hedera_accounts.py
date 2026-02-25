"""
Test Hedera Account Configuration

This script verifies that the Treasury and Operator accounts are properly
configured and accessible on Hedera testnet.

Usage:
    python scripts/test_hedera_accounts.py
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from hedera import Client, AccountBalanceQuery
from config import settings


def test_account_connection(client, account_id, account_name):
    """
    Test connection to a Hedera account
    
    Args:
        client: Hedera Client instance
        account_id: Account ID to test
        account_name: Name for display (e.g., "Treasury", "Operator")
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        print(f"\n🔍 Testing {account_name} Account: {account_id}")
        
        # Query account balance
        query = AccountBalanceQuery().setAccountId(account_id)
        balance = query.execute(client)
        
        print(f"   ✅ Account exists")
        print(f"   💰 Balance: {balance.hbars} HBAR")
        
        # Check if balance is sufficient
        hbar_amount = float(str(balance.hbars).replace(" ℏ", ""))
        if hbar_amount < 10:
            print(f"   ⚠️  WARNING: Low balance (< 10 HBAR)")
            print(f"      Consider funding from: https://portal.hedera.com/")
        else:
            print(f"   ✅ Sufficient balance")
        
        return True
        
    except Exception as e:
        print(f"   ❌ ERROR: {str(e)}")
        return False


def main():
    """Main test function"""
    print("=" * 70)
    print("🧪 HEDERA ACCOUNT CONFIGURATION TEST")
    print("=" * 70)
    
    # Check configuration
    print("\n📋 Configuration Check:")
    print(f"   Network: {settings.hedera_network}")
    print(f"   Operator ID: {settings.hedera_operator_id}")
    print(f"   Treasury ID: {settings.hedera_treasury_id or 'Not configured'}")
    
    if not settings.hedera_operator_id or not settings.hedera_operator_key:
        print("\n❌ ERROR: Operator account not configured")
        print("   Please set HEDERA_OPERATOR_ID and HEDERA_OPERATOR_KEY in .env")
        return 1
    
    # Create client
    print("\n🌐 Connecting to Hedera testnet...")
    
    try:
        client = Client.forTestnet()
        client.setOperator(settings.hedera_operator_id, settings.hedera_operator_key)
        print("   ✅ Connected successfully")
        
    except Exception as e:
        print(f"   ❌ Connection failed: {str(e)}")
        return 1
    
    # Test accounts
    print("\n" + "=" * 70)
    print("🔐 TESTING ACCOUNTS")
    print("=" * 70)
    
    results = []
    
    # Test Operator Account
    operator_ok = test_account_connection(
        client,
        settings.hedera_operator_id,
        "Operator"
    )
    results.append(("Operator", operator_ok))
    
    # Test Treasury Account (if configured)
    if settings.hedera_treasury_id:
        treasury_ok = test_account_connection(
            client,
            settings.hedera_treasury_id,
            "Treasury"
        )
        results.append(("Treasury", treasury_ok))
    else:
        print("\n⚠️  Treasury account not configured (optional for now)")
        print("   Set HEDERA_TREASURY_ID and HEDERA_TREASURY_KEY in .env")
    
    # Print summary
    print("\n" + "=" * 70)
    print("📊 TEST SUMMARY")
    print("=" * 70)
    
    all_passed = all(result[1] for result in results)
    
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"   {name} Account: {status}")
    
    if all_passed:
        print("\n✅ All tests passed!")
        print("\n📝 Next Steps:")
        print("   1. Verify accounts on HashScan:")
        print(f"      Operator: https://hashscan.io/testnet/account/{settings.hedera_operator_id}")
        if settings.hedera_treasury_id:
            print(f"      Treasury: https://hashscan.io/testnet/account/{settings.hedera_treasury_id}")
        print("   2. Proceed to Task 3.2: Fund accounts with testnet HBAR")
        print("   3. Proceed to Task 3.3: Create HCS topics")
    else:
        print("\n❌ Some tests failed")
        print("\n🔧 Troubleshooting:")
        print("   1. Verify account IDs are correct (format: 0.0.12345)")
        print("   2. Verify private keys are correct (DER format)")
        print("   3. Check accounts exist on HashScan:")
        print(f"      https://hashscan.io/testnet/account/{settings.hedera_operator_id}")
        print("   4. Ensure testnet is operational: https://status.hedera.com/")
    
    print("\n" + "=" * 70)
    
    # Close client
    client.close()
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
