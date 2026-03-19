# ⚡ Hedera Flow — Pay Your Electricity Bill with Crypto

> **The Decentralized Trust Layer for Utility Billing**  
> Built for the Hello Future Apex Hackathon 2026

[![Live Demo](https://img.shields.io/badge/Live%20Demo-Railway-blueviolet)](https://hedera-flow-github-production.up.railway.app)
[![Frontend](https://img.shields.io/badge/Frontend-Vercel-black)](https://hedera-flow-ivory.vercel.app)
[![HCS Topic](https://img.shields.io/badge/Hedera%20HCS-0.0.8052391-00D4AA)](https://hashscan.io/testnet/topic/0.0.8052391)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

---

## 🎯 What Is Hedera Flow?

Hedera Flow lets people **pay their electricity bills using HBAR or USDC** — with every meter reading verified on the Hedera blockchain so neither the utility company nor the customer can dispute it.

Think of it as: **"Your electricity bill, but with a blockchain receipt that nobody can fake."**

### The Problem We Solve

- **$2.96 billion** is lost globally every year to utility billing fraud
- In Nigeria alone, **40% of electricity bills are disputed**
- Paying bills across borders costs **3–7% in bank fees** and takes **3–7 days**
- There is no way to prove a meter reading is real — it's always "trust us"

### Our Solution

1. **Scan your meter** with your phone camera
2. **AI verifies** the reading is real (not a fake photo)
3. **AWS KMS signs** the data with a hardware security key that never leaves the vault
4. **Hedera records** it permanently — no one can change it
5. **Pay your bill** with HBAR or USDC in under 2 seconds

---

## 🔗 Live Links

| Resource | URL |
|----------|-----|
| 🌐 Frontend App | https://hedera-flow-ivory.vercel.app |
| 🔧 Backend API | https://hedera-flow-github-production.up.railway.app |
| 📖 API Docs | https://hedera-flow-github-production.up.railway.app/docs |
| ⛓️ HCS Topic (Africa) | https://hashscan.io/testnet/topic/0.0.8052391 |
| 🔍 Operator Account | https://hashscan.io/testnet/account/0.0.7942957 |
| 💻 GitHub Repo | https://github.com/De-real-iManuel/Hedera-Flow |

---

## 🏗️ How It Works — The Full Flow

```
📱 Phone Camera
      │
      ▼
🔍 Google Vision OCR          ← Reads the meter number from the photo
      │
      ▼
🛡️ Fraud Detection Engine     ← Checks GPS, timestamp, image manipulation
      │
      ▼
🔐 AWS KMS (HSM)              ← Signs the data — private key NEVER leaves hardware
      │
      ▼
⛓️ Hedera HCS                 ← Stores the signed record permanently on blockchain
      │
      ▼
💰 Pay with HBAR / USDC       ← HashPack wallet, settled in 1.8 seconds
      │
      ▼
✅ Bill Marked Paid            ← Immutable receipt on Hedera
```

---

## 🔐 AWS KMS Integration (Bounty Feature)

This is the security backbone of Hedera Flow. Here's why it matters in plain English:

**The old way (insecure):**
> The app stores a secret key in a database. If a hacker breaks in, they steal the key and can forge any transaction.

**Our way (HSM-backed):**
> The secret key lives inside AWS hardware that physically cannot export it. The app sends data to AWS, AWS signs it inside the vault, and sends back only the signature. The key never moves.

### What We Built

| Feature | Description |
|---------|-------------|
| `create_meter_key()` | Creates a unique secp256k1 key per smart meter inside AWS HSM |
| `sign_consumption_data()` | Blind-signs meter readings — key stays in hardware |
| `verify_signature()` | Verifies any signature using the public key |
| `rotate_key()` | Enables automatic 90-day key rotation |
| `get_key_audit_trail()` | Full CloudTrail log of every signing operation |

### Key Security Properties
- **FIPS 140-2 Level 3** hardware backing
- **secp256k1** curve — same as Hedera's native signing
- **Zero key exposure** — private key never touches application memory or database
- **Complete audit trail** — every sign operation logged in AWS CloudTrail

```python
# How we sign a meter reading (simplified)
response = kms_client.sign(
    KeyId=meter_kms_key_id,      # Points to key inside HSM
    Message=consumption_data,     # The meter reading data
    MessageType='RAW',
    SigningAlgorithm='ECDSA_SHA_256'
)
# Private key never left the hardware vault ✅
```

---

## ⛓️ Hedera Integration

### Hedera Consensus Service (HCS)

Every verified meter reading is logged to HCS — a public, tamper-proof ledger. This creates a "third-party truth" that neither the utility company nor the customer can alter.

**Regional HCS Topics:**

| Region | Topic ID | Countries |
|--------|----------|-----------|
| Africa | `0.0.8052391` | Nigeria, South Africa, Kenya |
| Europe | `0.0.8052384` | Spain, Germany, France |
| Americas | `0.0.8052396` | USA, Brazil |
| Asia | `0.0.8052389` | India, Singapore |
| South America | `0.0.8052390` | Brazil, Argentina |

### What Gets Recorded on HCS

```json
{
  "type": "SMART_METER_CONSUMPTION",
  "meter_id": "SM-NG-LAG-001",
  "consumption_kwh": 245.7,
  "ocr_confidence": 0.95,
  "fraud_score": 0.17,
  "kms_signature": "3045022100...",
  "gps_coordinates": [6.5244, 3.3792],
  "timestamp": 1710681600
}
```

Once this is on HCS, it has a **sequence number** and **consensus timestamp** — permanent, public, and verifiable by anyone at https://hashscan.io.

---

## 💰 Payments

Users pay electricity bills directly with crypto:

| Method | Fee | Settlement Time |
|--------|-----|-----------------|
| Traditional bank | 3–7% | 3–7 days |
| **Hedera Flow (HBAR/USDC)** | **0.1%** | **1.8 seconds** |

**Prepaid tokens** — buy electricity credits in advance, consumed automatically using FIFO logic.

**Cross-border** — family abroad sends HBAR for electricity. No Western Union, no waiting.

---

## 🛡️ Fraud Detection

We solve the "fake photo" problem with multiple layers:

| Check | What It Does |
|-------|-------------|
| GPS verification | Confirms phone is within 50m of the registered meter |
| Timestamp check | Reading must be submitted within 5 minutes of capture |
| Error Level Analysis | Detects if the photo was digitally edited |
| OCR confidence | Rejects readings below 95% confidence |
| Behavioral analysis | Flags readings that don't match historical patterns |

A fraud score below 0.3 = proceed. Above 0.7 = block.

---

## 🚀 Quick Start

### Prerequisites
- Node.js 18+
- Python 3.11+
- PostgreSQL
- AWS account (for KMS)
- Hedera testnet account

### 1. Clone & Install

```bash
git clone https://github.com/De-real-iManuel/Hedera-Flow.git
cd Hedera-Flow

# Frontend
npm install

# Backend
cd backend && pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Frontend
cp .env.example .env.local
# Set VITE_API_BASE_URL=http://localhost:8080/api

# Backend
cp backend/.env.example backend/.env
# Set DATABASE_URL, JWT_SECRET_KEY, HEDERA_OPERATOR_ID, AWS_KMS_MASTER_KEY_ID
```

### 3. Run

```bash
# Backend
cd backend && uvicorn app.core.app:app --port 8080 --reload

# Frontend (new terminal)
npm run dev
```

### 4. Environment Variables

**Backend (required):**
```
DATABASE_URL=postgresql://user:pass@localhost:5432/hedera_flow
JWT_SECRET_KEY=your-secret-key
HEDERA_OPERATOR_ID=0.0.xxxxxx
HEDERA_OPERATOR_KEY=your-private-key
AWS_KMS_REGION=us-east-1
AWS_KMS_MASTER_KEY_ID=your-kms-key-id
```

**Frontend (required):**
```
VITE_API_BASE_URL=https://hedera-flow-github-production.up.railway.app/api
VITE_HEDERA_NETWORK=testnet
```

---

## 🏛️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    FRONTEND (Vercel)                     │
│         React + TypeScript + Vite + Tailwind CSS         │
│    HashPack Wallet  │  MetaMask  │  Email/Password Auth  │
└──────────────────────────┬──────────────────────────────┘
                           │ HTTPS
┌──────────────────────────▼──────────────────────────────┐
│                   BACKEND (Railway)                      │
│              FastAPI + Python + PostgreSQL               │
│                                                          │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────────┐  │
│  │  Auth API   │  │  Meters API  │  │  Payments API │  │
│  │  JWT + bcrypt│  │  OCR + Fraud │  │  HBAR / USDC  │  │
│  └─────────────┘  └──────────────┘  └───────────────┘  │
└──────────┬──────────────┬──────────────────┬────────────┘
           │              │                  │
    ┌──────▼──────┐ ┌─────▼──────┐  ┌───────▼────────┐
    │  AWS KMS    │ │Google Vision│  │  Hedera HCS    │
    │  HSM Signing│ │  OCR API   │  │  Immutable Log │
    │  (secp256k1)│ │  95%+ acc. │  │  5 regions     │
    └─────────────┘ └────────────┘  └────────────────┘
```

---

## 📁 Project Structure

```
Hedera-Flow/
├── src/                          # React frontend
│   ├── components/               # UI components
│   ├── hooks/                    # useAuth, useMeters, etc.
│   ├── lib/                      # api-client.ts, api.ts
│   └── pages/                    # Auth, Home, Dashboard
├── backend/
│   ├── app/
│   │   ├── api/endpoints/        # auth, meters, payments, bills
│   │   ├── services/
│   │   │   ├── aws_kms_service.py    # ← AWS KMS HSM integration
│   │   │   ├── hedera_service.py     # ← Hedera HCS + payments
│   │   │   ├── billing_service.py    # ← Bill generation
│   │   │   └── fraud_detection_service.py  # ← Multi-layer fraud checks
│   │   ├── models/               # SQLAlchemy DB models
│   │   └── schemas/              # Pydantic request/response schemas
│   └── reset_password.py         # Utility script
├── docker-compose.yml
└── vercel.json
```

---

## 🧪 Testing

```bash
cd backend

# Run all tests
python -m pytest

# Test KMS integration
python -m pytest tests/unit/test_kms_service.py -v

# Test fraud detection
python -m pytest tests/unit/test_fraud_detection.py -v
```

---

## 📊 Performance

| Metric | Value |
|--------|-------|
| End-to-end (photo → HCS) | ~3.2 seconds |
| Payment settlement | 1.8 seconds |
| OCR accuracy | 95%+ |
| Fraud detection | <100ms |
| API response time | <200ms |

---

## 🤝 Team

**De real iManuel**  
📧 nwajarieemmanuel355@gmail.com  
🐙 [@De-real-iManuel](https://github.com/De-real-iManuel)

---

## 📄 License

MIT — see [LICENSE](LICENSE)

---

*Built with ❤️ for the Hello Future Apex Hackathon 2026*  
*Powered by Hedera Hashgraph + AWS KMS + Google Vision*
