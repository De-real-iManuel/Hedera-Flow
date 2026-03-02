# Smart Contract Deployment - Quick Start

## 🚀 Deploy in 3 Steps

### Step 1: Compile Contract
```bash
cd backend
npx hardhat compile
```

### Step 2: Deploy to Testnet
```bash
python scripts/deploy_contract.py
```

### Step 3: Test Deployment
```bash
python scripts/test_deployed_contract.py
```

## ✅ Success Indicators

After deployment, you should see:
- ✅ Contract ID saved to `.env` and `deployment.json`
- ✅ HashScan explorer link displayed
- ✅ All tests passing

## 📋 Prerequisites Checklist

- [ ] Contract compiled (`artifacts/` folder exists)
- [ ] Hedera operator account created
- [ ] Operator account funded (30+ HBAR)
- [ ] `.env` file configured with:
  - `HEDERA_OPERATOR_ID`
  - `HEDERA_OPERATOR_KEY`
  - `HEDERA_NETWORK=testnet`

## 💰 Cost

**Total**: ~20-30 HBAR (~$1-2 USD at current rates)

## 🔗 Useful Links

- **Get Testnet HBAR**: https://portal.hedera.com/faucet
- **HashScan Explorer**: https://hashscan.io/testnet
- **Hedera Docs**: https://docs.hedera.com/hedera/sdks-and-apis/sdks/smart-contracts

## 🆘 Quick Troubleshooting

| Error | Solution |
|-------|----------|
| "Contract artifact not found" | Run `npx hardhat compile` |
| "Missing Hedera credentials" | Set `HEDERA_OPERATOR_ID` and `HEDERA_OPERATOR_KEY` in `.env` |
| "Insufficient balance" | Fund account at https://portal.hedera.com/faucet |
| "Deployment failed" | Check operator account balance and private key |

## 📝 What Gets Created

1. **deployment.json** - Deployment metadata
2. **HEDERA_CONTRACT_ID** in `.env` - Contract address
3. **Contract on Hedera** - Live smart contract on testnet

## 🎯 Next Steps

After successful deployment:

1. **Integrate with Backend**:
   ```python
   from config import settings
   contract_id = settings.hedera_contract_id
   ```

2. **Test Contract Functions**:
   ```bash
   python scripts/test_deployed_contract.py
   ```

3. **View on Explorer**:
   Visit the HashScan link from deployment output

4. **Update Payment Service**:
   The payment service will automatically use the deployed contract

## 📚 Full Documentation

For detailed information, see: `DEPLOY_CONTRACT_README.md`
