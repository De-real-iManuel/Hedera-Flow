# HCS Topics - Quick Start Guide

## 🚀 Quick Setup (3 Steps)

### Step 1: Fix Windows Long Path Issue

Run PowerShell as Administrator:

```powershell
New-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem" -Name "LongPathsEnabled" -Value 1 -PropertyType DWORD -Force
```

Restart your computer, then:

```bash
pip install hedera-sdk-python
```

### Step 2: Create Topics

```bash
cd backend
python scripts/create_hcs_topics.py
```

### Step 3: Update .env

Copy the topic IDs from the output and paste into `backend/.env`:

```env
HCS_TOPIC_EU=0.0.xxxxx
HCS_TOPIC_US=0.0.xxxxx
HCS_TOPIC_ASIA=0.0.xxxxx
HCS_TOPIC_SA=0.0.xxxxx
HCS_TOPIC_AFRICA=0.0.xxxxx
```

## ✅ Verify

```bash
python scripts/test_hcs_topics.py
```

## 📋 What You Get

5 HCS topics for regional blockchain logging:

| Topic | Region | Countries |
|-------|--------|-----------|
| EU | Europe | Spain (ES) |
| US | United States | USA (US) |
| Asia | Asia | India (IN) |
| SA | South America | Brazil (BR) |
| Africa | Africa | Nigeria (NG) |

## 💰 Cost

- ~0.15 HBAR total (~$0.05 at $0.30/HBAR)
- Ensure operator account has 1+ HBAR

## 🔗 View on HashScan

https://hashscan.io/testnet/topic/YOUR_TOPIC_ID

## 📚 Full Documentation

See `HCS_TOPICS_SETUP.md` for detailed instructions and troubleshooting.

## ⚠️ Important

- These are **blockchain logging topics**, NOT utility providers
- Utility providers (100+) already seeded in database (Task 2.3)
- Topics log verifications/payments for each region
- Messages are immutable and permanent

## 🆘 Troubleshooting

**Can't install hedera-sdk-python?**
- Use WSL: `cd backend && pip install hedera-sdk-python`
- Or create topics manually at https://portal.hedera.com/

**Missing operator credentials?**
- Check `.env` has `HEDERA_OPERATOR_ID` and `HEDERA_OPERATOR_KEY`
- Complete Task 3.1 if not done

**Insufficient balance?**
- Fund operator account at https://portal.hedera.com/
- Complete Task 3.2 if not done

## ✨ Next Steps

After topics are created:
- ✅ Task 3.3 complete
- ⏭️ Task 3.4: Test HBAR transfers
- ⏭️ Task 3.5: Test HCS message submission
