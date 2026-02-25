"""
Create Hedera Testnet Accounts (Treasury and Operator)

This script creates two Hedera testnet accounts:
1. Treasury Account - Holds HBAR for funding test accounts and platform operations
2. Operator Account - Submits transactions, pays fees, manages topics/contracts

Requirements:
- Hedera SDK Python installed (hedera-sdk-python)
- Internet connection to Hedera testnet

Usage:
    python scripts/create_hedera_accounts.py

Output:
    - Account IDs and private keys printed to console
    - Instructions for updating .env file
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from hedera import (
    Client,
    PrivateKey,
    AccountCreateTransaction,
    Hbar,
    AccountBalanceQuery
)


def create_testnet_account(client, initial_balance_hbar=100):
    """
    Create a new Hedera testnet account
    
    Args:
        client: Hedera Client instance
        initial_balance_hbar: Initial HBAR balance for the account
        
    Returns:
        tuple: (account_id, private_key, public_key)
    """
    print(f"\n🔑 Generating new key pair...")
    
    # Generate a new private key
    private_key = PrivateKey.generateED25519()
    public_key = private_key.getPublicKey()
    
    print(f"✅ Private key generated")
    print(f"✅ Public key: {public_key}")
    
    # Create the account
    print(f"\n📝 Creating account with {initial_balance_hbar} HBAR initial balance...")
    
    transaction = (
        AccountCreateTransaction()
        .setKey(public_key)
        .setInitialBalance(Hbar(initial_balance_hbar))
    )
    
    # Submit the transaction
    response = transaction.execute(client)
    
    # Get the receipt
    receipt = response.getReceipt(client)
    account_id = receipt.accountId
    
    print(f"✅ Account created: {account_id}")
    
    return account_id, private_key, public_key


def verify_account_balance(client, account_id):
    """
    Verify the account balance
    
    Args:
        client: Hedera Client instance
        account_id: Account ID to check
        
    Returns:
        Hbar: Account balance
    """
    print(f"\n💰 Checking balance for {account_id}...")
    
    query = AccountBalanceQuery().setAccountId(account_id)
    balance = query.execute(client)
    
    print(f"✅ Balance: {balance.hbars} HBAR")
    
    return balance.hbars


def main():
    """
    Main function to create treasury and operator accounts
    """
    print("=" * 70)
    print("🚀 HEDERA TESTNET ACCOUNT CREATION")
    print("=" * 70)
    print("\nThis script will create two Hedera testnet accounts:")
    print("1. Treasury Account - For funding and platform operations")
    print("2. Operator Account - For submitting transactions and managing topics")
    print("\n⚠️  IMPORTANT: Save the output securely! You'll need it for .env file")
    print("=" * 70)
    
    # Create client for testnet
    print("\n🌐 Connecting to Hedera testnet...")
    
    try:
        # For testnet, we need to use a funded account to create new accounts
        # Users should get testnet HBAR from: https://portal.hedera.com/
        print("\n⚠️  NOTE: You need a funded testnet account to create new accounts.")
        print("Get free testnet HBAR from: https://portal.hedera.com/")
        print("\nPlease enter your funded testnet account credentials:")
        
        funded_account_id = input("\nEnter your funded account ID (e.g., 0.0.12345): ").strip()
        funded_private_key = input("Enter your funded account private key: ").strip()
        
        # Create client with funded account
        client = Client.forTestnet()
        client.setOperator(funded_account_id, funded_private_key)
        
        print(f"\n✅ Connected to testnet with account {funded_account_id}")
        
        # Verify funded account has sufficient balance
        funded_balance = verify_account_balance(client, funded_account_id)
        
        if funded_balance.toTinybars() < Hbar(250).toTinybars():
            print(f"\n❌ ERROR: Insufficient balance in funded account")
            print(f"   Current: {funded_balance} HBAR")
            print(f"   Required: At least 250 HBAR (for creating 2 accounts + fees)")
            print(f"\n   Get more testnet HBAR from: https://portal.hedera.com/")
            return
        
        print(f"\n✅ Sufficient balance available: {funded_balance} HBAR")
        
        # Create Treasury Account
        print("\n" + "=" * 70)
        print("1️⃣  CREATING TREASURY ACCOUNT")
        print("=" * 70)
        
        treasury_id, treasury_key, treasury_pub = create_testnet_account(
            client, 
            initial_balance_hbar=100
        )
        
        # Verify treasury account
        verify_account_balance(client, treasury_id)
        
        # Create Operator Account
        print("\n" + "=" * 70)
        print("2️⃣  CREATING OPERATOR ACCOUNT")
        print("=" * 70)
        
        operator_id, operator_key, operator_pub = create_testnet_account(
            client,
            initial_balance_hbar=100
        )
        
        # Verify operator account
        verify_account_balance(client, operator_id)
        
        # Print summary
        print("\n" + "=" * 70)
        print("✅ SUCCESS! ACCOUNTS CREATED")
        print("=" * 70)
        
        print("\n📋 TREASURY ACCOUNT:")
        print(f"   Account ID:  {treasury_id}")
        print(f"   Private Key: {treasury_key}")
        print(f"   Public Key:  {treasury_pub}")
        
        print("\n📋 OPERATOR ACCOUNT:")
        print(f"   Account ID:  {operator_id}")
        print(f"   Private Key: {operator_key}")
        print(f"   Public Key:  {operator_pub}")
        
        print("\n" + "=" * 70)
        print("📝 NEXT STEPS:")
        print("=" * 70)
        print("\n1. Update your backend/.env file with these values:")
        print(f"\n   HEDERA_TREASURY_ID={treasury_id}")
        print(f"   HEDERA_TREASURY_KEY={treasury_key}")
        print(f"   HEDERA_OPERATOR_ID={operator_id}")
        print(f"   HEDERA_OPERATOR_KEY={operator_key}")
        
        print("\n2. Verify accounts on HashScan:")
        print(f"   Treasury: https://hashscan.io/testnet/account/{treasury_id}")
        print(f"   Operator: https://hashscan.io/testnet/account/{operator_id}")
        
        print("\n3. Fund accounts with more testnet HBAR if needed:")
        print("   https://portal.hedera.com/")
        
        print("\n⚠️  SECURITY WARNING:")
        print("   - Keep private keys secure and never commit to version control")
        print("   - These are testnet accounts - DO NOT use on mainnet")
        print("   - Add .env to .gitignore")
        
        print("\n" + "=" * 70)
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        print("\nTroubleshooting:")
        print("1. Verify you have testnet HBAR in your funded account")
        print("2. Check your account ID and private key are correct")
        print("3. Ensure you have internet connection")
        print("4. Visit https://portal.hedera.com/ for testnet HBAR")
        return 1
    
    finally:
        if 'client' in locals():
            client.close()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
