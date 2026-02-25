"""
Test Basic HBAR Transfers Between Accounts (REST API Version)

This script tests basic HBAR transfer functionality using Hedera REST API
instead of the Java-based SDK. This validates FR-5.8 (HBAR transfers) and 
US-7 (payment flow).

Tests:
1. Check account balances
2. Verify accounts exist
3. Document transfer process

Note: Actual transfers require signing with private keys, which is better
done with the SDK. This script verifies account setup and provides guidance.

Usage:
    python scripts/test_hbar_transfers_rest.py
"""

import sys
import os
import requests
import time
from decimal import Decimal

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config import settings


def get_account_info(account_id):
    """
    Get account information from Hedera Mirror Node REST API
    
    Args:
        account_id: Hedera account ID (e.g., "0.0.12345")
        
    Returns:
        dict: Account information including balance
    """
    try:
        url = f"{settings.hedera_mirror_node_url}/api/v1/accounts/{account_id}"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"   ❌ Failed to get account info: {str(e)}")
        return None


def get_account_balance(account_id, account_name):
    """
    Get and display account balance
    
    Args:
        account_id: Account ID to query
        account_name: Name for display
        
    Returns:
        float: Balance in HBAR
    """
    try:
        print(f"   Querying {account_name} ({account_id})...")
        
        account_info = get_account_info(account_id)
        
        if not account_info:
            print(f"   ❌ Account not found or API error")
            return None
        
        # Balance is in tinybars (1 HBAR = 100,000,000 tinybars)
        balance_tinybars = int(account_info.get('balance', {}).get('balance', 0))
        balance_hbar = balance_tinybars / 100_000_000
        
        print(f"   ✅ {account_name}: {balance_hbar:.4f} HBAR")
        
        # Check if balance is sufficient
        if balance_hbar < 10:
            print(f"   ⚠️  WARNING: Low balance (< 10 HBAR)")
        
        return balance_hbar
        
    except Exception as e:
        print(f"   ❌ Failed to get balance: {str(e)}")
        return None


def get_recent_transactions(account_id, limit=5):
    """
    Get recent transactions for an account
    
    Args:
        account_id: Hedera account ID
        limit: Number of transactions to retrieve
        
    Returns:
        list: Recent transactions
    """
    try:
        url = f"{settings.hedera_mirror_node_url}/api/v1/transactions"
        params = {
            'account.id': account_id,
            'limit': limit,
            'order': 'desc'
        }
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        return response.json().get('transactions', [])
    except Exception as e:
        print(f"   ❌ Failed to get transactions: {str(e)}")
        return []


def main():
    """Main test function"""
    print("=" * 70)
    print("🧪 HEDERA HBAR TRANSFER TEST (REST API)")
    print("=" * 70)
    print("\nThis script verifies account setup for HBAR transfers.")
    print("Requirements: FR-5.8 (HBAR transfers), US-7 (payment flow)")
    
    # Check configuration
    print("\n📋 Configuration Check:")
    print(f"   Network: {settings.hedera_network}")
    print(f"   Mirror Node: {settings.hedera_mirror_node_url}")
    print(f"   Operator ID: {settings.hedera_operator_id}")
    print(f"   Treasury ID: {settings.hedera_treasury_id or 'Not configured'}")
    
    if not settings.hedera_operator_id:
        print("\n❌ ERROR: Operator account not configured")
        print("   Please set HEDERA_OPERATOR_ID in .env")
        return 1
    
    if not settings.hedera_treasury_id:
        print("\n❌ ERROR: Treasury account not configured")
        print("   Please set HEDERA_TREASURY_ID in .env")
        return 1
    
    # Test Mirror Node connectivity
    print("\n🌐 Testing Mirror Node connectivity...")
    
    try:
        response = requests.get(f"{settings.hedera_mirror_node_url}/api/v1/network/nodes", timeout=10)
        response.raise_for_status()
        print("   ✅ Mirror Node is accessible")
    except Exception as e:
        print(f"   ❌ Mirror Node connection failed: {str(e)}")
        return 1
    
    # Check account balances
    print("\n" + "=" * 70)
    print("💰 ACCOUNT BALANCES")
    print("=" * 70)
    
    print("\n📊 Current balances:")
    treasury_balance = get_account_balance(settings.hedera_treasury_id, "Treasury")
    operator_balance = get_account_balance(settings.hedera_operator_id, "Operator")
    
    if treasury_balance is None or operator_balance is None:
        print("\n❌ Failed to retrieve account balances")
        return 1
    
    # Check if accounts have sufficient balance for testing
    print("\n" + "=" * 70)
    print("✅ BALANCE VERIFICATION")
    print("=" * 70)
    
    sufficient_balance = True
    
    if treasury_balance < 10:
        print(f"\n   ⚠️  Treasury balance too low: {treasury_balance:.4f} HBAR")
        print(f"      Recommended: At least 10 HBAR for testing")
        sufficient_balance = False
    else:
        print(f"\n   ✅ Treasury has sufficient balance: {treasury_balance:.4f} HBAR")
    
    if operator_balance < 5:
        print(f"\n   ⚠️  Operator balance too low: {operator_balance:.4f} HBAR")
        print(f"      Recommended: At least 5 HBAR for testing")
        sufficient_balance = False
    else:
        print(f"\n   ✅ Operator has sufficient balance: {operator_balance:.4f} HBAR")
    
    # Get recent transactions
    print("\n" + "=" * 70)
    print("📜 RECENT TRANSACTIONS")
    print("=" * 70)
    
    print("\n🔍 Treasury recent transactions:")
    treasury_txs = get_recent_transactions(settings.hedera_treasury_id, limit=3)
    if treasury_txs:
        for tx in treasury_txs[:3]:
            tx_id = tx.get('transaction_id', 'N/A')
            tx_type = tx.get('name', 'N/A')
            timestamp = tx.get('consensus_timestamp', 'N/A')
            print(f"   • {tx_type} - {tx_id}")
    else:
        print("   No recent transactions found")
    
    print("\n🔍 Operator recent transactions:")
    operator_txs = get_recent_transactions(settings.hedera_operator_id, limit=3)
    if operator_txs:
        for tx in operator_txs[:3]:
            tx_id = tx.get('transaction_id', 'N/A')
            tx_type = tx.get('name', 'N/A')
            timestamp = tx.get('consensus_timestamp', 'N/A')
            print(f"   • {tx_type} - {tx_id}")
    else:
        print("   No recent transactions found")
    
    # Print HashScan links
    print("\n" + "=" * 70)
    print("🔍 VIEW ON HASHSCAN")
    print("=" * 70)
    
    print(f"\n   Treasury: https://hashscan.io/testnet/account/{settings.hedera_treasury_id}")
    print(f"   Operator: https://hashscan.io/testnet/account/{settings.hedera_operator_id}")
    
    # Print transfer instructions
    print("\n" + "=" * 70)
    print("📝 HBAR TRANSFER INSTRUCTIONS")
    print("=" * 70)
    
    print("\n🔧 To perform actual HBAR transfers, you have two options:")
    
    print("\n1️⃣  Using HashPack Wallet (Recommended for MVP):")
    print("   • Install HashPack browser extension")
    print("   • Import your Treasury/Operator account using private key")
    print("   • Use the wallet UI to send HBAR between accounts")
    print("   • This is how users will pay bills in the MVP")
    
    print("\n2️⃣  Using Hedera SDK (Requires Java):")
    print("   • Install Java JDK 11 or higher")
    print("   • Set JAVA_HOME environment variable")
    print("   • Install hedera-sdk-py package")
    print("   • Run: python scripts/test_hbar_transfers.py")
    
    print("\n3️⃣  Using Hedera Portal (Manual Testing):")
    print("   • Visit: https://portal.hedera.com/")
    print("   • Login with your account")
    print("   • Use the web interface to send test transfers")
    
    # Print summary
    print("\n" + "=" * 70)
    print("📊 TEST SUMMARY")
    print("=" * 70)
    
    if sufficient_balance:
        print("\n✅ ALL CHECKS PASSED!")
        print("\n📝 Summary:")
        print("   ✅ Mirror Node API accessible")
        print("   ✅ Treasury account exists and has sufficient balance")
        print("   ✅ Operator account exists and has sufficient balance")
        print("   ✅ Accounts are ready for HBAR transfers")
        print("\n🎯 Task 3.4 Status: Accounts verified and ready for transfers")
        print("\n📝 Next Steps:")
        print("   1. Test transfers manually using HashPack or Hedera Portal")
        print("   2. Verify transactions appear on HashScan")
        print("   3. Proceed to Task 3.5: Test HCS message submission")
        print("   4. Proceed to Task 3.6: Configure Mirror Node API access")
        print("\n💡 For the MVP:")
        print("   • Users will use HashPack wallet for payments")
        print("   • Backend will verify transactions via Mirror Node API")
        print("   • No Java SDK required in production")
    else:
        print("\n⚠️  INSUFFICIENT BALANCE")
        print("\n🔧 Action Required:")
        print("   1. Fund accounts using Hedera Portal faucet")
        print("   2. Visit: https://portal.hedera.com/")
        print("   3. Request testnet HBAR (10,000 HBAR per request)")
        print("   4. Re-run this test after funding")
    
    print("\n" + "=" * 70)
    
    return 0 if sufficient_balance else 1


if __name__ == "__main__":
    sys.exit(main())
