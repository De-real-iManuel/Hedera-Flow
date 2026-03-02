# Hedera Scripts

Utility scripts for Hedera network operations.

## Available Scripts

### 1. test_hedera_connection.py

Test Hedera testnet connection and check account balances.

```bash
python scripts/test_hedera_connection.py
```

**What it does**:
- Connects to Hedera testnet
- Checks operator account balance
- Checks treasury account balance
- Verifies credentials are correct

**Use when**:
- First time setup
- Troubleshooting connection issues
- Verifying account funding

---

### 2. create_hcs_topics.py

Create 5 HCS topics for regional blockchain logging.

```bash
python scripts/create_hcs_topics.py
```

**What it does**:
- Creates HCS topic for Europe (Spain)
- Creates HCS topic for United States
- Creates HCS topic for Asia (India)
- Creates HCS topic for South America (Brazil)
- Creates HCS topic for Africa (Nigeria)
- Outputs topic IDs to add to .env

**Use when**:
- Initial setup (run once)
- Setting up new environment
- Recreating topics if needed

**Output**:
```
HCS_TOPIC_EU=0.0.XXXXXX
HCS_TOPIC_US=0.0.XXXXXX
HCS_TOPIC_ASIA=0.0.XXXXXX
HCS_TOPIC_SA=0.0.XXXXXX
HCS_TOPIC_AFRICA=0.0.XXXXXX
```

Copy these to your `backend/.env` file.

---

## Requirements

All scripts require:
- Python 3.8+
- Hedera SDK installed: `pip install hedera-sdk-python`
- Valid `.env` file with Hedera credentials

## Environment Variables

Required in `backend/.env`:

```bash
HEDERA_NETWORK=testnet
HEDERA_OPERATOR_ID=0.0.xxxxx
HEDERA_OPERATOR_KEY=302e020100300506032b657004220420...
HEDERA_TREASURY_ID=0.0.xxxxx
HEDERA_TREASURY_KEY=302e020100300506032b657004220420...
```

## Troubleshooting

### "Failed to initialize Hedera client"
- Check operator ID and key in .env
- Ensure accounts exist on testnet
- Verify network is set to "testnet"

### "Insufficient balance"
- Visit https://portal.hedera.com/faucet
- Request testnet HBAR for your accounts
- Wait 1-2 minutes and retry

### "Module not found"
- Run: `pip install -r requirements.txt`
- Ensure you're in the backend directory

## Support

- Hedera Docs: https://docs.hedera.com
- Hedera Discord: https://hedera.com/discord
- HashScan Explorer: https://hashscan.io/testnet
