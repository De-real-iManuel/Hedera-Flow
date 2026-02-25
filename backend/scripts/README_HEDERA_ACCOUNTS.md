# Hedera Testnet Account Creation Guide

This guide explains how to create Treasury and Operator accounts for the Hedera Flow MVP on Hedera testnet.

## Overview

The Hedera Flow platform requires two testnet accounts:

1. **Treasury Account** (`0.0.TREASURY`)
   - Holds HBAR for funding test accounts
   - Receives platform fees (future feature)
   - Funds operator account when needed

2. **Operator Account** (`0.0.OPERATOR`)
   - Submits transactions to Hedera network
   - Pays transaction fees
   - Manages HCS topics and smart contracts

## Prerequisites

### 1. Get Testnet HBAR

Before creating accounts, you need a funded testnet account:

1. Visit [Hedera Portal](https://portal.hedera.com/)
2. Create a free account
3. Request testnet HBAR (you'll receive ~10,000 HBAR)
4. Save your account ID and private key

**Minimum Required**: 250 HBAR (for creating 2 accounts + transaction fees)

### 2. Install Dependencies

Ensure you have the Hedera SDK installed:

```bash
cd backend
pip install -r requirements.txt
```

## Creating Accounts

### Method 1: Using the Python Script (Recommended)

Run the account creation script:

```bash
cd backend
python scripts/create_hedera_accounts.py
```

The script will:
1. Prompt for your funded testnet account credentials
2. Create a Treasury account with 100 HBAR
3. Create an Operator account with 100 HBAR
4. Display account IDs and private keys
5. Provide instructions for updating `.env`

**Example Output:**

```
======================================================================
✅ SUCCESS! ACCOUNTS CREATED
======================================================================

📋 TREASURY ACCOUNT:
   Account ID:  0.0.12345
   Private Key: 302e020100300506032b657004220420...
   Public Key:  302a300506032b6570032100...

📋 OPERATOR ACCOUNT:
   Account ID:  0.0.12346
   Private Key: 302e020100300506032b657004220420...
   Public Key:  302a300506032b6570032100...

======================================================================
📝 NEXT STEPS:
======================================================================

1. Update your backend/.env file with these values:

   HEDERA_TREASURY_ID=0.0.12345
   HEDERA_TREASURY_KEY=302e020100300506032b657004220420...
   HEDERA_OPERATOR_ID=0.0.12346
   HEDERA_OPERATOR_KEY=302e020100300506032b657004220420...
```

### Method 2: Using Hedera Portal (Manual)

If you prefer to create accounts manually:

1. Go to [Hedera Portal](https://portal.hedera.com/)
2. Navigate to "Testnet" → "Accounts"
3. Click "Create Account" twice (for Treasury and Operator)
4. Save the account IDs and private keys
5. Transfer HBAR to each account (minimum 100 HBAR each)

## Updating Configuration

### 1. Update `.env` File

Copy the account details to `backend/.env`:

```bash
# Hedera Configuration
HEDERA_NETWORK=testnet
HEDERA_OPERATOR_ID=0.0.YOUR_OPERATOR_ID
HEDERA_OPERATOR_KEY=YOUR_OPERATOR_PRIVATE_KEY
HEDERA_TREASURY_ID=0.0.YOUR_TREASURY_ID
HEDERA_TREASURY_KEY=YOUR_TREASURY_PRIVATE_KEY
```

### 2. Verify Configuration

Test your configuration:

```bash
cd backend
python -c "from config import settings; print(f'Operator: {settings.hedera_operator_id}'); print(f'Treasury: {settings.hedera_treasury_id}')"
```

## Verifying Accounts

### Check on HashScan

View your accounts on the Hedera testnet explorer:

- Treasury: `https://hashscan.io/testnet/account/0.0.YOUR_TREASURY_ID`
- Operator: `https://hashscan.io/testnet/account/0.0.YOUR_OPERATOR_ID`

You should see:
- Account balance (100 HBAR each)
- Account creation timestamp
- Public key

### Test Account Access

Create a simple test script:

```python
from hedera import Client, AccountBalanceQuery
from config import settings

# Create client
client = Client.forTestnet()
client.setOperator(settings.hedera_operator_id, settings.hedera_operator_key)

# Check operator balance
query = AccountBalanceQuery().setAccountId(settings.hedera_operator_id)
balance = query.execute(client)
print(f"Operator Balance: {balance.hbars} HBAR")

# Check treasury balance
query = AccountBalanceQuery().setAccountId(settings.hedera_treasury_id)
balance = query.execute(client)
print(f"Treasury Balance: {balance.hbars} HBAR")

client.close()
```

## Account Structure

```
Treasury Account: 0.0.TREASURY
├─ Initial Balance: 100 HBAR
├─ Purpose: Fund test accounts and platform operations
├─ Receives: Platform fees (future)
└─ Funds: Operator account when needed

Operator Account: 0.0.OPERATOR
├─ Initial Balance: 100 HBAR
├─ Purpose: Submit transactions and pay fees
├─ Submits: Verifications, payments, disputes
└─ Manages: HCS topics, smart contracts
```

## Funding Accounts

### Getting More Testnet HBAR

If you need more testnet HBAR:

1. Visit [Hedera Portal](https://portal.hedera.com/)
2. Go to "Testnet" → "Faucet"
3. Enter your account ID
4. Request HBAR (limit: 10,000 HBAR per day)

### Transferring Between Accounts

Transfer HBAR from Treasury to Operator:

```python
from hedera import Client, TransferTransaction, Hbar
from config import settings

client = Client.forTestnet()
client.setOperator(settings.hedera_treasury_id, settings.hedera_treasury_key)

# Transfer 50 HBAR from Treasury to Operator
transaction = (
    TransferTransaction()
    .addHbarTransfer(settings.hedera_treasury_id, Hbar(-50))
    .addHbarTransfer(settings.hedera_operator_id, Hbar(50))
)

response = transaction.execute(client)
receipt = response.getReceipt(client)

print(f"Transfer successful: {receipt.status}")
client.close()
```

## Security Best Practices

### 1. Protect Private Keys

- **NEVER** commit private keys to version control
- Add `.env` to `.gitignore`
- Use environment variables in production
- Rotate keys regularly

### 2. Testnet vs Mainnet

- These accounts are for **TESTNET ONLY**
- Do not use testnet keys on mainnet
- Testnet HBAR has no real value
- Create separate accounts for mainnet deployment

### 3. Access Control

- Limit who has access to private keys
- Use separate accounts for different environments (dev, staging, prod)
- Monitor account activity on HashScan

## Troubleshooting

### Error: "Insufficient Balance"

**Problem**: Not enough HBAR to create accounts

**Solution**:
1. Get more testnet HBAR from [Hedera Portal](https://portal.hedera.com/)
2. Ensure funded account has at least 250 HBAR
3. Check account balance on HashScan

### Error: "Invalid Account ID"

**Problem**: Account ID format is incorrect

**Solution**:
1. Verify format: `0.0.12345` (three parts separated by dots)
2. Check for typos
3. Ensure account exists on testnet

### Error: "Invalid Private Key"

**Problem**: Private key format is incorrect

**Solution**:
1. Verify key is in DER format (starts with `302e020100...`)
2. Check for extra spaces or line breaks
3. Ensure key matches the account ID

### Error: "Network Timeout"

**Problem**: Cannot connect to Hedera testnet

**Solution**:
1. Check internet connection
2. Verify testnet is operational: [Hedera Status](https://status.hedera.com/)
3. Try again in a few minutes

## Next Steps

After creating accounts:

1. ✅ Update `.env` file with account IDs and keys
2. ✅ Verify accounts on HashScan
3. ✅ Test account access with balance query
4. 🔜 Create HCS topics (Task 3.3)
5. 🔜 Test HBAR transfers (Task 3.4)
6. 🔜 Deploy smart contracts (Task 21)

## Resources

- [Hedera Portal](https://portal.hedera.com/) - Get testnet HBAR
- [HashScan Testnet](https://hashscan.io/testnet) - Blockchain explorer
- [Hedera Docs](https://docs.hedera.com/) - Official documentation
- [Hedera SDK Python](https://github.com/hashgraph/hedera-sdk-python) - SDK documentation
- [Hedera Status](https://status.hedera.com/) - Network status

## Support

If you encounter issues:

1. Check [Hedera Discord](https://hedera.com/discord) - Community support
2. Review [Hedera Docs](https://docs.hedera.com/) - Official guides
3. Search [Stack Overflow](https://stackoverflow.com/questions/tagged/hedera-hashgraph) - Q&A

---

**Last Updated**: February 2026  
**Task**: 3.1 Create Hedera testnet accounts (treasury, operator)  
**Status**: Complete
