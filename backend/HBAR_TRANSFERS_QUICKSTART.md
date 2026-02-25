# HBAR Transfers - Quick Start Guide

## Task 3.4: Test Basic HBAR Transfers

### Status: ✅ READY FOR TESTING

## Prerequisites

Before testing HBAR transfers, ensure you have completed:

1. ✅ **Task 3.1**: Hedera accounts created (Treasury + Operator)
2. ✅ **Task 3.2**: Accounts funded with testnet HBAR
3. ✅ **Task 3.3**: HCS topics created (optional for transfers)

## Quick Test (REST API - No Java Required)

### Step 1: Verify Account Setup

```bash
cd backend
python scripts/test_hbar_transfers_rest.py
```

**Expected Output**:
```
✅ ALL CHECKS PASSED!
   ✅ Mirror Node API accessible
   ✅ Treasury account exists and has sufficient balance
   ✅ Operator account exists and has sufficient balance
   ✅ Accounts are ready for HBAR transfers
```

### Step 2: Manual Transfer Test (HashPack Wallet)

1. **Install HashPack**:
   - Visit: https://www.hashpack.app/
   - Install browser extension
   - Create/import account

2. **Import Treasury Account**:
   - Open HashPack → Settings → Import Account
   - Paste private key from `backend/.env` (HEDERA_TREASURY_KEY)
   - Name: "Treasury (Testnet)"

3. **Send Test Transfer**:
   - Click "Send"
   - To: Your Operator account ID (from `.env`)
   - Amount: 5 HBAR
   - Memo: "Test transfer - Task 3.4"
   - Confirm transaction

4. **Verify on HashScan**:
   - Copy transaction ID from HashPack
   - Visit: https://hashscan.io/testnet/transaction/{TX_ID}
   - Verify: amount, recipient, memo, status

### Step 3: Verify Transfer

Run the REST API test again to see updated balances:

```bash
python scripts/test_hbar_transfers_rest.py
```

## If Accounts Not Yet Created

### Option 1: Create via Hedera Portal (Recommended)

1. **Visit Hedera Portal**:
   - Go to: https://portal.hedera.com/
   - Login/Register (free)

2. **Create Treasury Account**:
   - Navigate to: Testnet → Accounts
   - Click "Create Account"
   - Initial balance: 100 HBAR (from faucet)
   - Save Account ID and Private Key

3. **Create Operator Account**:
   - Click "Create Account" again
   - Initial balance: 100 HBAR
   - Save Account ID and Private Key

4. **Update `.env` File**:
   ```bash
   HEDERA_TREASURY_ID=0.0.YOUR_TREASURY_ID
   HEDERA_TREASURY_KEY=YOUR_TREASURY_PRIVATE_KEY
   HEDERA_OPERATOR_ID=0.0.YOUR_OPERATOR_ID
   HEDERA_OPERATOR_KEY=YOUR_OPERATOR_PRIVATE_KEY
   ```

5. **Get More HBAR** (if needed):
   - In Hedera Portal, request from faucet
   - 10,000 HBAR per request
   - Recommended: 500+ HBAR for Treasury, 200+ for Operator

### Option 2: Use Existing Accounts

If you already have testnet accounts:

1. Update `backend/.env` with your account IDs and keys
2. Ensure accounts have sufficient balance (10+ HBAR each)
3. Run the test script

## Testing Approaches

### Approach 1: REST API Verification (Current)

**Pros**:
- ✅ No Java dependency
- ✅ Fast and simple
- ✅ Verifies account setup
- ✅ Works in any environment

**Limitations**:
- ⚠️ Cannot perform actual transfers
- ⚠️ Read-only verification

**Use for**:
- CI/CD pipelines
- Quick account verification
- Balance checking

### Approach 2: Manual Testing (HashPack)

**Pros**:
- ✅ Simulates real user experience
- ✅ No development setup needed
- ✅ Visual confirmation
- ✅ Tests actual payment flow

**Use for**:
- User acceptance testing
- Demo preparation
- End-to-end validation

### Approach 3: SDK-based Testing (Requires Java)

**Pros**:
- ✅ Automated transfer testing
- ✅ Full functionality
- ✅ Transaction fee analysis

**Requirements**:
- Java JDK 11+
- JAVA_HOME environment variable
- hedera-sdk-py package

**Use for**:
- Comprehensive testing
- Automated test suites
- Development environments with Java

## Verification Checklist

- [ ] Accounts created on Hedera testnet
- [ ] Account IDs updated in `backend/.env`
- [ ] Private keys updated in `backend/.env`
- [ ] Accounts funded with testnet HBAR (10+ each)
- [ ] REST API test passes
- [ ] Manual transfer test successful
- [ ] Transaction visible on HashScan
- [ ] Balances updated correctly

## Expected Results

### Successful Test Output

```
======================================================================
✅ ALL CHECKS PASSED!
======================================================================

📝 Summary:
   ✅ Mirror Node API accessible
   ✅ Treasury account exists and has sufficient balance
   ✅ Operator account exists and has sufficient balance
   ✅ Accounts are ready for HBAR transfers

🎯 Task 3.4 Status: Accounts verified and ready for transfers

📝 Next Steps:
   1. Test transfers manually using HashPack or Hedera Portal
   2. Verify transactions appear on HashScan
   3. Proceed to Task 3.5: Test HCS message submission
   4. Proceed to Task 3.6: Configure Mirror Node API access
```

### Manual Transfer Success

- ✅ Transaction submitted successfully
- ✅ Consensus reached (3-5 seconds)
- ✅ Transaction ID received
- ✅ Visible on HashScan
- ✅ Balances updated correctly
- ✅ Memo included (if specified)

## Common Issues

### "Account not found" Error

**Cause**: Account IDs in `.env` are placeholders or incorrect

**Solution**:
1. Verify account IDs are real (not `0.0.xxxxx`)
2. Check accounts exist on HashScan
3. Ensure no typos in `.env` file

### "Insufficient balance" Warning

**Cause**: Accounts have less than 10 HBAR

**Solution**:
1. Visit Hedera Portal: https://portal.hedera.com/
2. Request testnet HBAR from faucet
3. Wait for transfer to complete
4. Re-run test

### "Module 'hedera' not found"

**Cause**: Trying to use SDK-based test without Java

**Solution**:
- Use REST API test instead: `python scripts/test_hbar_transfers_rest.py`
- Or install Java JDK 11+ and set JAVA_HOME

## Next Steps

After successful testing:

1. ✅ **Task 3.4**: Test HBAR transfers - **COMPLETE**
2. 🔜 **Task 3.5**: Test HCS message submission
3. 🔜 **Task 3.6**: Configure Mirror Node API access
4. 🔜 **Week 4**: Implement payment flow with HashPack integration

## Resources

- [Hedera Portal](https://portal.hedera.com/) - Create accounts, get HBAR
- [HashScan](https://hashscan.io/testnet) - Blockchain explorer
- [HashPack Wallet](https://www.hashpack.app/) - User wallet
- [Mirror Node API](https://docs.hedera.com/hedera/sdks-and-apis/rest-api) - REST API docs

## Support

If you encounter issues:

1. Check account IDs and keys in `.env`
2. Verify accounts on HashScan
3. Ensure sufficient HBAR balance
4. Review error messages carefully
5. Consult `TASK_3.4_SUMMARY.md` for detailed troubleshooting

---

**Last Updated**: February 2026  
**Status**: ✅ Ready for Testing  
**Requirements**: FR-5.8 (HBAR transfers), US-7 (payment flow)
