# HCS Topics Setup Guide

## Overview

Task 3.3 requires creating 5 HCS (Hedera Consensus Service) topics for regional blockchain logging. These topics will log verifications, payments, and disputes for each geographic region.

## Regional Topics

The 5 topics map countries to regions as follows:

1. **EU Topic** - Europe (Spain → ES)
2. **US Topic** - United States (USA → US)
3. **Asia Topic** - Asia (India → IN)
4. **SA Topic** - South America (Brazil → BR)
5. **Africa Topic** - Africa (Nigeria → NG)

## Prerequisites

Before creating HCS topics, ensure:

1. ✅ Hedera operator account created (Task 3.1 - COMPLETED)
2. ✅ Operator account funded with testnet HBAR (Task 3.2 - COMPLETED)
3. ⚠️ Hedera SDK Python installed

## Installation Issue (Windows Long Path)

The `hedera-sdk-python` package has a known issue on Windows due to long file paths. You have two options:

### Option 1: Enable Windows Long Path Support (Recommended)

1. Open PowerShell as Administrator
2. Run: `New-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem" -Name "LongPathsEnabled" -Value 1 -PropertyType DWORD -Force`
3. Restart your computer
4. Install the package: `pip install hedera-sdk-python`

### Option 2: Use WSL or Linux Environment

If you have WSL (Windows Subsystem for Linux):

```bash
# In WSL terminal
cd backend
pip install hedera-sdk-python python-dotenv requests
python scripts/create_hcs_topics.py
```

### Option 3: Manual Topic Creation via Hedera Portal

If installation continues to fail, you can create topics manually:

1. Go to https://portal.hedera.com/
2. Login with your testnet account
3. Navigate to "Consensus Service" → "Topics"
4. Create 5 topics with these memos:
   - EU: "Hedera Flow - EU Region: Verifications, payments, disputes for European countries (ES)"
   - US: "Hedera Flow - US Region: Verifications, payments, disputes for United States (US)"
   - Asia: "Hedera Flow - Asia Region: Verifications, payments, disputes for Asian countries (IN)"
   - SA: "Hedera Flow - SA Region: Verifications, payments, disputes for South American countries (BR)"
   - Africa: "Hedera Flow - Africa Region: Verifications, payments, disputes for African countries (NG)"
5. Copy the topic IDs and update your `.env` file

## Running the Script

Once the Hedera SDK is installed:

```bash
cd backend
python scripts/create_hcs_topics.py
```

The script will:
1. Connect to Hedera testnet
2. Check operator balance (needs ~1 HBAR for topic creation fees)
3. Create 5 HCS topics with appropriate memos
4. Verify each topic was created successfully
5. Display topic IDs for your `.env` file

## Expected Output

```
======================================================================
🚀 HEDERA CONSENSUS SERVICE (HCS) TOPIC CREATION
======================================================================

✅ Connected with operator: 0.0.xxxxx
✅ Sufficient balance for topic creation

======================================================================
1️⃣  CREATING EU TOPIC
======================================================================
✅ Topic created: 0.0.12345
✅ Topic verified

... (similar for US, Asia, SA, Africa)

======================================================================
✅ SUCCESS! ALL 5 HCS TOPICS CREATED
======================================================================

📋 TOPIC IDs:
   EU Topic:     0.0.12345
   US Topic:     0.0.12346
   Asia Topic:   0.0.12347
   SA Topic:     0.0.12348
   Africa Topic: 0.0.12349
```

## Update .env File

After topics are created, update `backend/.env`:

```env
# ============================================
# HCS TOPICS (Hedera Consensus Service)
# ============================================
HCS_TOPIC_EU=0.0.12345
HCS_TOPIC_US=0.0.12346
HCS_TOPIC_ASIA=0.0.12347
HCS_TOPIC_SA=0.0.12348
HCS_TOPIC_AFRICA=0.0.12349
```

## Testing Topics

After creation, test the topics:

```bash
python scripts/test_hcs_topics.py
```

This will:
1. Submit test messages to each topic
2. Query the Mirror Node to verify messages
3. Display message content and metadata

## Topic Usage in Application

Once created, topics will be used for:

### Verification Logging
```json
{
  "type": "VERIFICATION",
  "region": "EU",
  "user_id": "uuid-anonymized",
  "meter_reading": 5142.7,
  "confidence": 0.96,
  "fraud_score": 0.12,
  "status": "VERIFIED",
  "timestamp": "2026-02-19T10:30:00Z"
}
```

### Payment Logging
```json
{
  "type": "PAYMENT",
  "region": "EU",
  "bill_id": "BILL-ES-2026-001",
  "amount_hbar": 251.17,
  "amount_fiat": 85.40,
  "currency": "EUR",
  "exchange_rate": 0.34,
  "tx_id": "0.0.123456@1710789700.123",
  "timestamp": "2026-02-19T10:35:00Z"
}
```

### Dispute Logging
```json
{
  "type": "DISPUTE_CREATED",
  "region": "EU",
  "dispute_id": "DISP-ES-2026-001",
  "bill_id": "BILL-ES-2026-001",
  "reason": "OVERCHARGE",
  "escrow_amount_hbar": 251.17,
  "timestamp": "2026-02-19T10:40:00Z"
}
```

## Cost Estimate

- Topic creation: ~$0.01 per topic = ~$0.05 total
- At current HBAR price (~$0.30): ~0.15 HBAR total
- Recommended balance: 1+ HBAR for safety

## Verification

After setup, verify topics on HashScan:
- https://hashscan.io/testnet/topic/0.0.YOUR_TOPIC_ID

## Troubleshooting

### Error: "Missing operator credentials"
- Ensure `HEDERA_OPERATOR_ID` and `HEDERA_OPERATOR_KEY` are set in `.env`
- Run Task 3.1 if not completed

### Error: "Insufficient balance"
- Fund your operator account with testnet HBAR
- Visit https://portal.hedera.com/ for testnet faucet
- Run Task 3.2 if not completed

### Error: "Module not found: hedera"
- Install Hedera SDK: `pip install hedera-sdk-python`
- Enable Windows Long Path support (see above)
- Or use WSL/Linux environment

## Next Steps

After HCS topics are created:

1. ✅ Update `.env` file with topic IDs
2. ⏭️ Proceed to Task 3.4: Test basic HBAR transfers
3. ⏭️ Proceed to Task 3.5: Test HCS message submission

## Files

- **Creation Script**: `backend/scripts/create_hcs_topics.py`
- **Test Script**: `backend/scripts/test_hcs_topics.py`
- **Environment Config**: `backend/.env`
- **This Guide**: `backend/HCS_TOPICS_SETUP.md`

## Requirements Mapping

This task fulfills:
- **FR-5.12**: System shall create HCS topics for regional logging
- **US-8**: Blockchain logging for verification audit trail

## Important Notes

⚠️ **These are blockchain logging topics, NOT utility providers**
- Utility providers (100+ companies) are already seeded in database via Task 2.3
- Each topic logs verifications/payments for its region
- Country-to-region mapping: ES→EU, US→US, IN→Asia, BR→SA, NG→Africa

✅ **Topics are immutable once created**
- Topic IDs cannot be changed
- Messages are permanently logged
- Suitable for audit trail and compliance

🔒 **Security**
- Admin key set to operator account (allows topic updates)
- Submit key set to operator account (controls message submission)
- Messages are public on testnet (use anonymized user IDs)
