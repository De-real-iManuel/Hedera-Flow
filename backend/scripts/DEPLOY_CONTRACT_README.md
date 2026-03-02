# Smart Contract Deployment Guide

This guide explains how to deploy the BillingSettlement smart contract to Hedera testnet.

## Prerequisites

### 1. Compiled Contract
The contract must be compiled before deployment:

```bash
cd backend
npx hardhat compile
```

This will generate the contract artifacts in `backend/artifacts/contracts/BillingSettlement.sol/`.

### 2. Hedera Operator Account
You need a Hedera testnet account with sufficient HBAR:

- **Minimum Balance**: 30-50 HBAR recommended
- **Account ID**: Set in `.env` as `HEDERA_OPERATOR_ID`
- **Private Key**: Set in `.env` as `HEDERA_OPERATOR_KEY`

If you don't have an account yet, run:
```bash
python scripts/create_hedera_accounts.py
```

### 3. Environment Variables
Ensure your `.env` file has:

```bash
HEDERA_NETWORK=testnet
HEDERA_OPERATOR_ID=0.0.xxxxx
HEDERA_OPERATOR_KEY=302e020100300506032b657004220420...
```

## Deployment Process

### Step 1: Verify Prerequisites

```bash
# Check if contract is compiled
ls -la backend/artifacts/contracts/BillingSettlement.sol/BillingSettlement.json

# Check operator account balance
python scripts/test_hedera_accounts.py
```

### Step 2: Run Deployment Script

```bash
cd backend
python scripts/deploy_contract.py
```

The script will:
1. ✅ Load compiled contract bytecode
2. ✅ Upload bytecode to Hedera File Service
3. ✅ Deploy contract to Hedera testnet
4. ✅ Save contract ID to `.env` and `deployment.json`

### Step 3: Verify Deployment

After successful deployment, you'll see:

```
🎉 DEPLOYMENT SUCCESSFUL!
============================================================
Contract ID:  0.0.xxxxx
File ID:      0.0.xxxxx
Network:      testnet
Explorer:     https://hashscan.io/testnet/contract/0.0.xxxxx
============================================================
```

Visit the HashScan explorer link to verify the contract on-chain.

## Deployment Output

### deployment.json
The script creates a `deployment.json` file with deployment details:

```json
{
  "contract_id": "0.0.xxxxx",
  "file_id": "0.0.xxxxx",
  "network": "testnet",
  "operator_id": "0.0.xxxxx",
  "deployed_at": "2026-02-18T12:34:56.789012",
  "contract_name": "BillingSettlement",
  "solidity_version": "0.8.0"
}
```

### .env Update
The contract ID is automatically added to your `.env` file:

```bash
# Smart Contract
HEDERA_CONTRACT_ID=0.0.xxxxx
```

## Cost Breakdown

Deploying the contract costs approximately:

| Operation | Cost (HBAR) |
|-----------|-------------|
| File Creation | ~2 HBAR |
| File Append (if needed) | ~2-5 HBAR |
| Contract Creation | ~15-20 HBAR |
| **Total** | **~20-30 HBAR** |

## Troubleshooting

### Error: "Contract artifact not found"
**Solution**: Compile the contract first:
```bash
npx hardhat compile
```

### Error: "Missing Hedera credentials"
**Solution**: Set environment variables in `.env`:
```bash
HEDERA_OPERATOR_ID=0.0.xxxxx
HEDERA_OPERATOR_KEY=302e020100300506032b657004220420...
```

### Error: "Insufficient balance"
**Solution**: Fund your operator account:
```bash
# Get testnet HBAR from faucet
# Visit: https://portal.hedera.com/faucet

# Or run funding script
python scripts/fund_hedera_accounts.py
```

### Error: "File creation failed"
**Solution**: Check your operator account has sufficient HBAR and the private key is correct.

### Error: "Contract deployment failed"
**Solution**: 
- Increase gas limit in the script (default: 100,000)
- Check bytecode size (should be < 100 KB)
- Verify contract compiles without errors

## Manual Deployment (Alternative)

If the Python script fails, you can deploy manually using Hedera SDK:

### Using JavaScript/TypeScript:

```javascript
const {
  Client,
  AccountId,
  PrivateKey,
  FileCreateTransaction,
  ContractCreateTransaction,
  Hbar
} = require("@hashgraph/sdk");
const fs = require("fs");

async function deployContract() {
  // Setup client
  const client = Client.forTestnet();
  client.setOperator(
    AccountId.fromString(process.env.HEDERA_OPERATOR_ID),
    PrivateKey.fromString(process.env.HEDERA_OPERATOR_KEY)
  );

  // Load bytecode
  const artifact = JSON.parse(
    fs.readFileSync("./artifacts/contracts/BillingSettlement.sol/BillingSettlement.json")
  );
  const bytecode = artifact.bytecode.replace("0x", "");

  // Upload bytecode
  const fileCreateTx = await new FileCreateTransaction()
    .setContents(bytecode)
    .setKeys([client.operatorPublicKey])
    .execute(client);
  
  const fileReceipt = await fileCreateTx.getReceipt(client);
  const fileId = fileReceipt.fileId;
  console.log("File ID:", fileId.toString());

  // Deploy contract
  const contractCreateTx = await new ContractCreateTransaction()
    .setBytecodeFileId(fileId)
    .setGas(100000)
    .execute(client);
  
  const contractReceipt = await contractCreateTx.getReceipt(client);
  const contractId = contractReceipt.contractId;
  console.log("Contract ID:", contractId.toString());

  client.close();
}

deployContract();
```

## Next Steps

After deployment:

1. **Update Backend Services**: The contract ID is automatically added to `.env`, restart your backend:
   ```bash
   python main.py
   ```

2. **Test Contract Functions**: Run contract tests:
   ```bash
   python scripts/test_contract_functions.py
   ```

3. **Integrate with Payment Flow**: Update payment service to use the deployed contract:
   ```python
   from app.services.hedera_service import HederaService
   
   hedera_service = HederaService()
   # Contract ID is loaded from settings.hedera_contract_id
   ```

4. **Verify on HashScan**: Visit the explorer link to see your contract on-chain.

## Contract Functions

The deployed contract has these functions:

### payBill
```solidity
function payBill(
    bytes32 billId,
    address utility,
    uint256 amountFiat,
    string memory currency
) external payable
```

### createDispute
```solidity
function createDispute(
    bytes32 disputeId,
    bytes32 billId
) external payable
```

### resolveDispute
```solidity
function resolveDispute(
    bytes32 disputeId,
    address winner
) external onlyOwner
```

### View Functions
```solidity
function getBill(bytes32 billId) external view returns (Bill memory)
function getDispute(bytes32 disputeId) external view returns (Dispute memory)
```

## Security Notes

⚠️ **Important Security Considerations**:

1. **Private Keys**: Never commit private keys to version control
2. **Testnet Only**: This deployment is for testnet only. Mainnet deployment requires additional security audits
3. **Owner Account**: The deployer account becomes the contract owner (can resolve disputes)
4. **Minimum Transfer**: Contract enforces 5 HBAR minimum (safety check)
5. **Immutable**: Once deployed, contract code cannot be changed

## Support

If you encounter issues:

1. Check the [Hedera Documentation](https://docs.hedera.com)
2. Visit [Hedera Discord](https://hedera.com/discord)
3. Review [HashScan Explorer](https://hashscan.io/testnet)
4. Check deployment logs in `deployment.json`

## References

- [Hedera Smart Contract Service](https://docs.hedera.com/hedera/sdks-and-apis/sdks/smart-contracts)
- [Solidity Documentation](https://docs.soliditylang.org/)
- [Hardhat Documentation](https://hardhat.org/docs)
- [HashScan Explorer](https://hashscan.io/)
