"""
Fund Hedera Testnet Accounts

This script funds the Treasury and Operator accounts with testnet HBAR
for transaction fees and test payments.

Requirements:
- Hedera SDK Python installed (hedera-sdk-python)
- Treasury and Operator accounts created (Task 3.1)
- Funded testnet account with sufficient HBAR
- Internet connection to Hedera testnet

Usage:
    python scripts/fund_hedera_accounts.py

Output:
    - Transfers HBAR to Treasury and Operator accounts
    - Verifies final balances
    - Provides transaction IDs for verification
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from hedera import (
    Client,
    PrivateKey,
    TransferTransaction,
    Hbar,
    AccountBalanceQuery
)
from config import settings


def get_account_balance(client, account_id, account_name="Account"):
    """
    Get the balance of a Hedera account
    
    Args:
        client: Hedera Client instance
        account_id: Account ID to check
        account_name: Name for display purposes
        
    Returns:
        Hbar: Account balance
    """
    try:
        print(f"\n💰 Checking balance for {account_name} ({account_id})...")
        
        query = AccountBalanceQuery().setAccountId(account_id)
        balance = query.execute(client)
        
        hbar_amount = float(str(balance.hbars).replace(" ℏ", ""))
        print(f"   Current balance: {balance.hbars} HBAR")
        
        return balance.hbars
        
    except Exception as e:
        print(f"   ❌ ERROR: {str(e)}")
        raise


def transfer_hbar(client, from_account_id, to_account_id, amount_hbar, memo=""):
    """
    Transfer HBAR between accounts
    
    Args:
        client: Hedera Client instance (with operator set)
        from_account_id: Source account ID
        to_account_id: Destination account ID
        amount_hbar: Amount to transfer in HBAR
        memo: Transaction memo
        
    Returns:
        str: Transaction ID
    """
    try:
        print(f"\n📤 Transferring {amount_hbar} HBAR...")
        print(f"   From: {from_account_id}")
        print(f"   To:   {to_account_id}")
        
        # Create transfer transaction
        transaction = (
            TransferTransaction()
            .addHbarTransfer(from_account_id, Hbar(-amount_hbar))
            .addHbarTransfer(to_account_id, Hbar(amount_hbar))
            .setTransactionMemo(memo)
        )
        
        # Execute transaction
        response = transaction.execute(client)
        
        # Get receipt
        receipt = response.getReceipt(client)
        
        # Get transaction ID
        tx_id = str(response.transactionId)
        
        print(f"   ✅ Transfer successful!")
        print(f"   Transaction ID: {tx_id}")
        print(f"   Status: {receipt.status}")
        
        return tx_id
        
    except Exception as e:
        print(f"   ❌ Transfer failed: {str(e)}")
        raise


def main():
    """
    Main function to fund Treasury and Operator accounts
    """
    print("=" * 70)
    print("💰 FUND HEDERA TESTNET ACCOUNTS")
    print("=" * 70)
    print("\nThis script will fund your Treasury and Operator accounts with")
    print("testnet HBAR for transaction fees and test payments.")
    print("\n⚠️  You need a funded testnet account to transfer HBAR from.")
    print("Get free testnet HBAR from: https://portal.hedera.com/")
    print("=" * 70)
    
    # Check if accounts are configured
    print("\n📋 Configuration Check:")
    
    if not settings.hedera_operator_id or not settings.hedera_operator_key:
        print("   ❌ ERROR: Operator account not configured")
        print("   Please complete Task 3.1 first and update .env file")
        return 1
    
    if not settings.hedera_treasury_id or not settings.hedera_treasury_key:
        print("   ❌ ERROR: Treasury account not configured")
        print("   Please complete Task 3.1 first and update .env file")
        return 1
    
    print(f"   ✅ Operator ID: {settings.hedera_operator_id}")
    print(f"   ✅ Treasury ID: {settings.hedera_treasury_id}")
    
    # Get funding source account
    print("\n" + "=" * 70)
    print("🔑 FUNDING SOURCE ACCOUNT")
    print("=" * 70)
    print("\nEnter the credentials for your funded testnet account:")
    print("(This account will transfer HBAR to Treasury and Operator)")
    
    funded_account_id = input("\nFunded account ID (e.g., 0.0.12345): ").strip()
    funded_private_key = input("Funded account private key: ").strip()
    
    if not funded_account_id or not funded_private_key:
        print("\n❌ ERROR: Account credentials required")
        return 1
    
    # Get funding amounts
    print("\n" + "=" * 70)
    print("💵 FUNDING AMOUNTS")
    print("=" * 70)
    print("\nRecommended amounts:")
    print("  - Treasury: 500-1000 HBAR (for funding user accounts)")
    print("  - Operator: 200-500 HBAR (for transaction fees)")
    print("\nMinimum amounts:")
    print("  - Treasury: 100 HBAR")
    print("  - Operator: 50 HBAR")
    
    try:
        treasury_amount = float(input("\nAmount to fund Treasury (HBAR): ").strip())
        operator_amount = float(input("Amount to fund Operator (HBAR): ").strip())
    except ValueError:
        print("\n❌ ERROR: Invalid amount. Please enter numbers only.")
        return 1
    
    if treasury_amount < 0 or operator_amount < 0:
        print("\n❌ ERROR: Amounts must be positive")
        return 1
    
    total_amount = treasury_amount + operator_amount
    
    # Create client
    print("\n" + "=" * 70)
    print("🌐 CONNECTING TO HEDERA TESTNET")
    print("=" * 70)
    
    try:
        client = Client.forTestnet()
        client.setOperator(funded_account_id, funded_private_key)
        print("   ✅ Connected successfully")
        
    except Exception as e:
        print(f"   ❌ Connection failed: {str(e)}")
        print("\nTroubleshooting:")
        print("1. Verify account ID format (0.0.12345)")
        print("2. Verify private key is correct")
        print("3. Check internet connection")
        return 1
    
    # Check funded account balance
    print("\n" + "=" * 70)
    print("💰 BALANCE VERIFICATION")
    print("=" * 70)
    
    try:
        funded_balance = get_account_balance(client, funded_account_id, "Funded Account")
        funded_hbar = float(str(funded_balance).replace(" ℏ", ""))
        
        required_hbar = total_amount + 10  # +10 for fees
        
        if funded_hbar < required_hbar:
            print(f"\n❌ ERROR: Insufficient balance in funded account")
            print(f"   Current:  {funded_balance} HBAR")
            print(f"   Required: {required_hbar} HBAR (including fees)")
            print(f"\n   Get more testnet HBAR from: https://portal.hedera.com/")
            return 1
        
        print(f"   ✅ Sufficient balance: {funded_balance} HBAR")
        
        # Check current balances of target accounts
        treasury_balance = get_account_balance(
            client, 
            settings.hedera_treasury_id, 
            "Treasury"
        )
        operator_balance = get_account_balance(
            client,
            settings.hedera_operator_id,
            "Operator"
        )
        
    except Exception as e:
        print(f"\n❌ ERROR: Failed to check balances: {str(e)}")
        return 1
    
    # Confirm transfer
    print("\n" + "=" * 70)
    print("📝 TRANSFER SUMMARY")
    print("=" * 70)
    print(f"\nFrom: {funded_account_id}")
    print(f"  Current balance: {funded_balance} HBAR")
    print(f"\nTo Treasury ({settings.hedera_treasury_id}):")
    print(f"  Current: {treasury_balance} HBAR")
    print(f"  Transfer: {treasury_amount} HBAR")
    print(f"  New balance: ~{float(str(treasury_balance).replace(' ℏ', '')) + treasury_amount} HBAR")
    print(f"\nTo Operator ({settings.hedera_operator_id}):")
    print(f"  Current: {operator_balance} HBAR")
    print(f"  Transfer: {operator_amount} HBAR")
    print(f"  New balance: ~{float(str(operator_balance).replace(' ℏ', '')) + operator_amount} HBAR")
    print(f"\nTotal transfer: {total_amount} HBAR")
    print(f"Estimated fees: ~2-5 HBAR")
    
    confirm = input("\n⚠️  Proceed with transfer? (yes/no): ").strip().lower()
    
    if confirm not in ['yes', 'y']:
        print("\n❌ Transfer cancelled by user")
        return 0
    
    # Execute transfers
    print("\n" + "=" * 70)
    print("🚀 EXECUTING TRANSFERS")
    print("=" * 70)
    
    transaction_ids = []
    
    try:
        # Fund Treasury
        if treasury_amount > 0:
            print("\n1️⃣  Funding Treasury Account...")
            tx_id = transfer_hbar(
                client,
                funded_account_id,
                settings.hedera_treasury_id,
                treasury_amount,
                memo="Hedera Flow - Treasury Funding"
            )
            transaction_ids.append(("Treasury", tx_id))
        
        # Fund Operator
        if operator_amount > 0:
            print("\n2️⃣  Funding Operator Account...")
            tx_id = transfer_hbar(
                client,
                funded_account_id,
                settings.hedera_operator_id,
                operator_amount,
                memo="Hedera Flow - Operator Funding"
            )
            transaction_ids.append(("Operator", tx_id))
        
    except Exception as e:
        print(f"\n❌ ERROR: Transfer failed: {str(e)}")
        return 1
    
    # Verify final balances
    print("\n" + "=" * 70)
    print("✅ FINAL BALANCES")
    print("=" * 70)
    
    try:
        treasury_final = get_account_balance(
            client,
            settings.hedera_treasury_id,
            "Treasury"
        )
        operator_final = get_account_balance(
            client,
            settings.hedera_operator_id,
            "Operator"
        )
        funded_final = get_account_balance(
            client,
            funded_account_id,
            "Funded Account"
        )
        
    except Exception as e:
        print(f"\n⚠️  WARNING: Could not verify final balances: {str(e)}")
    
    # Print success summary
    print("\n" + "=" * 70)
    print("🎉 SUCCESS! ACCOUNTS FUNDED")
    print("=" * 70)
    
    print("\n📋 Transaction IDs:")
    for account_name, tx_id in transaction_ids:
        print(f"\n{account_name}:")
        print(f"  Transaction ID: {tx_id}")
        print(f"  HashScan: https://hashscan.io/testnet/transaction/{tx_id}")
    
    print("\n📊 Account Balances:")
    print(f"\nTreasury ({settings.hedera_treasury_id}):")
    print(f"  Balance: {treasury_final} HBAR")
    print(f"  HashScan: https://hashscan.io/testnet/account/{settings.hedera_treasury_id}")
    
    print(f"\nOperator ({settings.hedera_operator_id}):")
    print(f"  Balance: {operator_final} HBAR")
    print(f"  HashScan: https://hashscan.io/testnet/account/{settings.hedera_operator_id}")
    
    print("\n" + "=" * 70)
    print("📝 NEXT STEPS")
    print("=" * 70)
    print("\n1. Verify transactions on HashScan (links above)")
    print("2. Run test script to verify configuration:")
    print("   python scripts/test_hedera_accounts.py")
    print("3. Proceed to Task 3.3: Create HCS topics")
    print("4. Proceed to Task 3.4: Test basic HBAR transfers")
    
    print("\n💡 Tips:")
    print("  - Monitor account balances regularly")
    print("  - Refund accounts when balance drops below 50 HBAR")
    print("  - Keep track of transaction fees")
    print("  - Get more testnet HBAR from: https://portal.hedera.com/")
    
    print("\n" + "=" * 70)
    
    # Close client
    client.close()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
