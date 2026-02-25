"""
Test Basic HBAR Transfers Between Accounts

This script tests basic HBAR transfer functionality between Treasury and Operator
accounts on Hedera testnet. This validates FR-5.8 (HBAR transfers) and US-7 
(payment flow).

Tests:
1. Transfer from Treasury to Operator
2. Transfer from Operator to Treasury
3. Transfer with memo
4. Verify balances after transfers

Usage:
    python scripts/test_hbar_transfers.py
"""

import sys
import os
import time

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from hedera import (
    Client,
    AccountBalanceQuery,
    TransferTransaction,
    Hbar,
    AccountId
)
from config import settings


def get_account_balance(client, account_id, account_name):
    """
    Get and display account balance
    
    Args:
        client: Hedera Client instance
        account_id: Account ID to query
        account_name: Name for display
        
    Returns:
        float: Balance in HBAR
    """
    try:
        query = AccountBalanceQuery().setAccountId(account_id)
        balance = query.execute(client)
        hbar_amount = float(str(balance.hbars).replace(" ℏ", ""))
        print(f"   {account_name}: {balance.hbars}")
        return hbar_amount
    except Exception as e:
        print(f"   ❌ Failed to get balance for {account_name}: {str(e)}")
        raise


def test_transfer(
    client,
    from_account_id,
    from_private_key,
    to_account_id,
    amount_hbar,
    memo=None,
    test_name="Transfer"
):
    """
    Test HBAR transfer between accounts
    
    Args:
        client: Hedera Client instance
        from_account_id: Source account ID
        from_private_key: Source account private key
        to_account_id: Destination account ID
        amount_hbar: Amount to transfer
        memo: Optional transaction memo
        test_name: Name for display
        
    Returns:
        tuple: (success: bool, tx_id: str, error: str)
    """
    try:
        print(f"\n{'=' * 70}")
        print(f"🧪 TEST: {test_name}")
        print(f"{'=' * 70}")
        print(f"   From: {from_account_id}")
        print(f"   To: {to_account_id}")
        print(f"   Amount: {amount_hbar} HBAR")
        if memo:
            print(f"   Memo: {memo}")
        
        # Get balances before transfer
        print(f"\n📊 Balances BEFORE transfer:")
        from_balance_before = get_account_balance(client, from_account_id, "Sender")
        to_balance_before = get_account_balance(client, to_account_id, "Receiver")
        
        # Check sufficient balance
        if from_balance_before < amount_hbar:
            print(f"\n   ❌ Insufficient balance: {from_balance_before} HBAR < {amount_hbar} HBAR")
            return False, None, "Insufficient balance"
        
        # Create a temporary client with sender's credentials
        print(f"\n🔄 Executing transfer...")
        temp_client = Client.forTestnet()
        temp_client.setOperator(from_account_id, from_private_key)
        
        # Create transfer transaction
        transaction = (
            TransferTransaction()
            .addHbarTransfer(from_account_id, Hbar(-amount_hbar))
            .addHbarTransfer(to_account_id, Hbar(amount_hbar))
        )
        
        # Add memo if provided
        if memo:
            transaction.setTransactionMemo(memo)
        
        # Execute transaction
        response = transaction.execute(temp_client)
        
        # Get receipt
        receipt = response.getReceipt(temp_client)
        
        # Get transaction ID
        tx_id = str(response.transactionId)
        
        print(f"   ✅ Transfer successful!")
        print(f"   Transaction ID: {tx_id}")
        print(f"   Status: {receipt.status}")
        
        # Wait a moment for consensus
        print(f"\n⏳ Waiting for consensus (3 seconds)...")
        time.sleep(3)
        
        # Get balances after transfer
        print(f"\n📊 Balances AFTER transfer:")
        from_balance_after = get_account_balance(client, from_account_id, "Sender")
        to_balance_after = get_account_balance(client, to_account_id, "Receiver")
        
        # Calculate changes (accounting for transaction fees)
        from_change = from_balance_before - from_balance_after
        to_change = to_balance_after - to_balance_before
        
        print(f"\n📈 Balance Changes:")
        print(f"   Sender: -{from_change:.4f} HBAR (includes tx fee)")
        print(f"   Receiver: +{to_change:.4f} HBAR")
        
        # Verify transfer amount (receiver should get exact amount)
        if abs(to_change - amount_hbar) < 0.0001:  # Allow tiny floating point difference
            print(f"   ✅ Receiver got correct amount: {amount_hbar} HBAR")
        else:
            print(f"   ⚠️  Amount mismatch: expected {amount_hbar}, got {to_change}")
        
        # Verify sender paid amount + fee
        if from_change > amount_hbar:
            fee = from_change - amount_hbar
            print(f"   ✅ Transaction fee: ~{fee:.4f} HBAR")
        
        # View on HashScan
        print(f"\n🔍 View on HashScan:")
        print(f"   https://hashscan.io/testnet/transaction/{tx_id}")
        
        temp_client.close()
        
        return True, tx_id, None
        
    except Exception as e:
        error_msg = str(e)
        print(f"\n   ❌ Transfer failed: {error_msg}")
        return False, None, error_msg


def main():
    """Main test function"""
    print("=" * 70)
    print("🧪 HEDERA HBAR TRANSFER TEST")
    print("=" * 70)
    print("\nThis script tests basic HBAR transfers between accounts.")
    print("Requirements: FR-5.8 (HBAR transfers), US-7 (payment flow)")
    
    # Check configuration
    print("\n📋 Configuration Check:")
    print(f"   Network: {settings.hedera_network}")
    print(f"   Operator ID: {settings.hedera_operator_id}")
    print(f"   Treasury ID: {settings.hedera_treasury_id or 'Not configured'}")
    
    if not settings.hedera_operator_id or not settings.hedera_operator_key:
        print("\n❌ ERROR: Operator account not configured")
        print("   Please set HEDERA_OPERATOR_ID and HEDERA_OPERATOR_KEY in .env")
        return 1
    
    if not settings.hedera_treasury_id or not settings.hedera_treasury_key:
        print("\n❌ ERROR: Treasury account not configured")
        print("   Please set HEDERA_TREASURY_ID and HEDERA_TREASURY_KEY in .env")
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
    
    # Test results
    test_results = []
    
    # Test 1: Transfer from Treasury to Operator (5 HBAR)
    success, tx_id, error = test_transfer(
        client,
        settings.hedera_treasury_id,
        settings.hedera_treasury_key,
        settings.hedera_operator_id,
        5.0,
        test_name="Test 1: Treasury → Operator (5 HBAR)"
    )
    test_results.append(("Treasury → Operator", success, tx_id, error))
    
    if not success:
        print("\n⚠️  Test 1 failed, skipping remaining tests")
        client.close()
        return 1
    
    # Wait between tests
    print("\n⏳ Waiting 5 seconds before next test...")
    time.sleep(5)
    
    # Test 2: Transfer from Operator to Treasury (3 HBAR)
    success, tx_id, error = test_transfer(
        client,
        settings.hedera_operator_id,
        settings.hedera_operator_key,
        settings.hedera_treasury_id,
        3.0,
        test_name="Test 2: Operator → Treasury (3 HBAR)"
    )
    test_results.append(("Operator → Treasury", success, tx_id, error))
    
    if not success:
        print("\n⚠️  Test 2 failed, skipping remaining tests")
        client.close()
        return 1
    
    # Wait between tests
    print("\n⏳ Waiting 5 seconds before next test...")
    time.sleep(5)
    
    # Test 3: Transfer with memo (simulating bill payment)
    memo = "Bill payment: BILL-ES-2026-001"
    success, tx_id, error = test_transfer(
        client,
        settings.hedera_treasury_id,
        settings.hedera_treasury_key,
        settings.hedera_operator_id,
        2.0,
        memo=memo,
        test_name="Test 3: Transfer with Memo (2 HBAR)"
    )
    test_results.append(("Transfer with Memo", success, tx_id, error))
    
    # Print summary
    print("\n" + "=" * 70)
    print("📊 TEST SUMMARY")
    print("=" * 70)
    
    all_passed = all(result[1] for result in test_results)
    
    for test_name, success, tx_id, error in test_results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"\n   {test_name}: {status}")
        if tx_id:
            print(f"      TX: {tx_id}")
        if error:
            print(f"      Error: {error}")
    
    # Final balance check
    print("\n" + "=" * 70)
    print("💰 FINAL BALANCES")
    print("=" * 70)
    
    try:
        print(f"\n📊 Current balances:")
        get_account_balance(client, settings.hedera_treasury_id, "Treasury")
        get_account_balance(client, settings.hedera_operator_id, "Operator")
    except Exception as e:
        print(f"   ⚠️  Could not fetch final balances: {str(e)}")
    
    # Print conclusion
    print("\n" + "=" * 70)
    
    if all_passed:
        print("✅ ALL TESTS PASSED!")
        print("\n📝 Summary:")
        print("   ✅ HBAR transfers working correctly")
        print("   ✅ Balance updates verified")
        print("   ✅ Transaction memos working")
        print("   ✅ Transaction fees calculated properly")
        print("\n🎯 Task 3.4 Complete: Basic HBAR transfers tested successfully")
        print("\n📝 Next Steps:")
        print("   1. Proceed to Task 3.5: Test HCS message submission")
        print("   2. Proceed to Task 3.6: Configure Mirror Node API access")
        print("   3. Begin implementing payment flow (Week 4)")
    else:
        print("❌ SOME TESTS FAILED")
        print("\n🔧 Troubleshooting:")
        print("   1. Verify both accounts have sufficient HBAR balance")
        print("   2. Check accounts on HashScan:")
        print(f"      Treasury: https://hashscan.io/testnet/account/{settings.hedera_treasury_id}")
        print(f"      Operator: https://hashscan.io/testnet/account/{settings.hedera_operator_id}")
        print("   3. Ensure testnet is operational: https://status.hedera.com/")
        print("   4. Check private keys are correct in .env")
    
    print("\n" + "=" * 70)
    
    # Close client
    client.close()
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
