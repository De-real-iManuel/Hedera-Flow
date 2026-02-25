# Hedera Accounts - Complete Quick Start

## One-Page Guide: From Zero to Funded Accounts

### Step 1: Get Testnet HBAR (5 minutes)

1. Go to [https://portal.hedera.com/](https://portal.hedera.com/)
2. Register/Login (free)
3. Navigate to **Testnet** → **Accounts**
4. Create account or request HBAR (10,000 HBAR per request)
5. Save your account ID and private key

### Step 2: Create Treasury & Operator Accounts (2 minutes)

```bash
cd backend
python scripts/create_hedera_accounts.py
```

**When prompted**:
- Enter your funded account ID (from Step 1)
- Enter your funded account private key
- Script creates 2 accounts with 100 HBAR each

**Save the output**:
- Treasury ID and private key
- Operator ID and private key

### Step 3: Update Configuration (1 minute)

Edit `backend/.env`:

```bash
HEDERA_OPERATOR_ID=0.0.YOUR_OPERATOR_ID
HEDERA_OPERATOR_KEY=YOUR_OPERATOR_PRIVATE_KEY
HEDERA_TREASURY_ID=0.0.YOUR_TREASURY_ID
HEDERA_TREASURY_KEY=YOUR_TREASURY_PRIVATE_KEY
```

### Step 4: Fund Accounts (3 minutes)

```bash
python scripts/fund_hedera_accounts.py
```

**When prompted**:
- Enter your funded account ID (from Step 1)
- Enter your funded account private key
- Treasury amount: **500 HBAR**
- Operator amount: **200 HBAR**
- Confirm: **yes**

### Step 5: Verify (1 minute)

```bash
python scripts/test_hedera_accounts.py
```

**Expected**:
```
✅ All tests passed!
   Operator Account: ✅ PASS (200 HBAR)
   Treasury Account: ✅ PASS (500 HBAR)
```

---

## Total Time: ~12 minutes

## What You Have Now

- ✅ Treasury account with 500 HBAR
- ✅ Operator account with 200 HBAR
- ✅ Verified configuration
- ✅ Ready for development

## Verify on HashScan

**Treasury**: `https://hashscan.io/testnet/account/{TREASURY_ID}`  
**Operator**: `https://hashscan.io/testnet/account/{OPERATOR_ID}`

## Next Steps

1. ✅ Accounts created and funded
2. 🔜 Create HCS topics (Task 3.3)
3. 🔜 Test HBAR transfers (Task 3.4)
4. 🔜 Build authentication (Task 6.1)

## Need Help?

- **Full Guides**: See `FUNDING_GUIDE.md` and `README_HEDERA_ACCOUNTS.md`
- **Hedera Portal**: [https://portal.hedera.com/](https://portal.hedera.com/)
- **Discord**: [https://hedera.com/discord](https://hedera.com/discord)

---

## Quick Commands Reference

```bash
# Create accounts
python scripts/create_hedera_accounts.py

# Fund accounts
python scripts/fund_hedera_accounts.py

# Verify setup
python scripts/test_hedera_accounts.py

# Check balances
python -c "from config import settings; from hedera import Client, AccountBalanceQuery; client = Client.forTestnet(); client.setOperator(settings.hedera_operator_id, settings.hedera_operator_key); print(f'Treasury: {AccountBalanceQuery().setAccountId(settings.hedera_treasury_id).execute(client).hbars}'); print(f'Operator: {AccountBalanceQuery().setAccountId(settings.hedera_operator_id).execute(client).hbars}'); client.close()"
```

---

**That's it! You're ready to build on Hedera! 🚀**
