# Hedera Account Funding - Quick Start

## TL;DR

Fund your Hedera testnet accounts in 3 steps:

### Step 1: Get Testnet HBAR

Visit [Hedera Portal](https://portal.hedera.com/) and request testnet HBAR (free).

### Step 2: Run Funding Script

```bash
cd backend
python scripts/fund_hedera_accounts.py
```

### Step 3: Verify

```bash
python scripts/test_hedera_accounts.py
```

---

## Detailed Steps

### 1. Prerequisites

- ✅ Completed Task 3.1 (accounts created)
- ✅ Updated `backend/.env` with account IDs and keys
- ✅ Have funded testnet account with 200+ HBAR

### 2. Get Testnet HBAR

**Option A: Hedera Portal (Recommended)**
1. Go to [https://portal.hedera.com/](https://portal.hedera.com/)
2. Register/Login
3. Navigate to Testnet → Accounts
4. Create account or request HBAR (10,000 HBAR per request)
5. Save account ID and private key

**Option B: Use Existing Account**
- If you already have a funded testnet account, use it

### 3. Run Funding Script

```bash
cd backend
python scripts/fund_hedera_accounts.py
```

**What you'll be asked**:
1. Funded account ID (e.g., `0.0.12345`)
2. Funded account private key
3. Amount to fund Treasury (recommended: 500 HBAR)
4. Amount to fund Operator (recommended: 200 HBAR)
5. Confirmation (yes/no)

**Example**:
```
Funded account ID: 0.0.98765
Funded account private key: 302e020100...
Amount to fund Treasury (HBAR): 500
Amount to fund Operator (HBAR): 200
Proceed with transfer? (yes/no): yes
```

### 4. Verify Funding

**Run test script**:
```bash
python scripts/test_hedera_accounts.py
```

**Expected output**:
```
✅ All tests passed!
   Operator Account: ✅ PASS (200 HBAR)
   Treasury Account: ✅ PASS (500 HBAR)
```

**Check on HashScan**:
- Treasury: `https://hashscan.io/testnet/account/{TREASURY_ID}`
- Operator: `https://hashscan.io/testnet/account/{OPERATOR_ID}`

---

## Recommended Amounts

| Account | Minimum | Recommended | Purpose |
|---------|---------|-------------|---------|
| Treasury | 100 HBAR | 500-1000 HBAR | Fund user accounts |
| Operator | 50 HBAR | 200-500 HBAR | Transaction fees |

---

## Common Issues

### "Insufficient Balance"
- Get more HBAR from [Hedera Portal](https://portal.hedera.com/)
- Reduce funding amounts

### "Account Not Found"
- Verify account ID format: `0.0.12345`
- Check `.env` file for typos
- Ensure Task 3.1 is complete

### "Invalid Private Key"
- Verify key format (starts with `302e020100...`)
- Check for extra spaces
- Copy key from account creation output

---

## Next Steps

After funding:

1. ✅ Task 3.2 complete
2. 🔜 Task 3.3: Create HCS topics
3. 🔜 Task 3.4: Test HBAR transfers

---

## Need Help?

- **Full Guide**: See `FUNDING_GUIDE.md`
- **Hedera Portal**: [https://portal.hedera.com/](https://portal.hedera.com/)
- **HashScan**: [https://hashscan.io/testnet](https://hashscan.io/testnet)
- **Hedera Discord**: [https://hedera.com/discord](https://hedera.com/discord)

---

**Quick Commands**:

```bash
# Fund accounts
python scripts/fund_hedera_accounts.py

# Verify funding
python scripts/test_hedera_accounts.py

# Check balances manually
python -c "from config import settings; from hedera import Client, AccountBalanceQuery; client = Client.forTestnet(); client.setOperator(settings.hedera_operator_id, settings.hedera_operator_key); print(f'Treasury: {AccountBalanceQuery().setAccountId(settings.hedera_treasury_id).execute(client).hbars}'); print(f'Operator: {AccountBalanceQuery().setAccountId(settings.hedera_operator_id).execute(client).hbars}'); client.close()"
```
