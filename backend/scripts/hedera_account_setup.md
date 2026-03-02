# Quick Start: Hedera Account Setup

## Option 1: Automated Script (Recommended)

```bash
cd backend
python scripts/create_hedera_accounts.py
```

Follow the prompts and save the output to your `.env` file.

## Option 2: Manual Setup via Hedera Portal

### Step 1: Get Testnet HBAR

1. Visit https://portal.hedera.com/
2. Sign up for a free account
3. Navigate to "Testnet" → "Faucet"
4. Request testnet HBAR (you'll receive ~10,000 HBAR)
5. Save your account ID and private key

### Step 2: Create Treasury Account

1. In Hedera Portal, go to "Testnet" → "Accounts"
2. Click "Create Account"
3. Set initial balance: 100 HBAR
4. Save the account ID (e.g., `0.0.12345`)
5. Save the private key (starts with `302e020100...`)

### Step 3: Create Operator Account

1. Click "Create Account" again
2. Set initial balance: 100 HBAR
3. Save the account ID (e.g., `0.0.12346`)
4. Save the private key

### Step 4: Update .env File

Add to `backend/.env`:

```bash
HEDERA_TREASURY_ID=0.0.YOUR_TREASURY_ID
HEDERA_TREASURY_KEY=YOUR_TREASURY_PRIVATE_KEY
HEDERA_OPERATOR_ID=0.0.YOUR_OPERATOR_ID
HEDERA_OPERATOR_KEY=YOUR_OPERATOR_PRIVATE_KEY
```

### Step 5: Verify on HashScan

Check your accounts:
- https://hashscan.io/testnet/account/0.0.YOUR_TREASURY_ID
- https://hashscan.io/testnet/account/0.0.YOUR_OPERATOR_ID

## Quick Verification

Test your setup:

```bash
cd backend
python -c "from config import settings; print(f'✅ Operator: {settings.hedera_operator_id}'); print(f'✅ Treasury: {settings.hedera_treasury_id}')"
```

## Need Help?

See `README_HEDERA_ACCOUNTS.md` for detailed instructions and troubleshooting.
