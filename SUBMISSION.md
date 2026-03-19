# Hedera Flow — Hackathon Submission
## Hello Future Apex Hackathon 2026

---

## Project Details

| Field | Value |
|-------|-------|
| **Project Name** | Hedera Flow |
| **Tagline** | The Decentralized Trust Layer for Utility Billing |
| **Team** | De real iManuel |
| **Email** | nwajarieemmanuel355@gmail.com |
| **Live App** | https://hedera-flow-ivory.vercel.app |
| **Backend API** | https://hedera-flow-github-production.up.railway.app |
| **GitHub** | https://github.com/De-real-iManuel/Hedera-Flow |
| **HCS Topic** | https://hashscan.io/testnet/topic/0.0.8052391 |

---

## What We Built

Hedera Flow is a **utility bill payment platform** where:

1. Meter readings are verified using AI (Google Vision OCR) and fraud detection
2. Each reading is cryptographically signed using **AWS KMS hardware security modules** — the private key never leaves the vault
3. The signed record is permanently stored on **Hedera HCS** — immutable, public, verifiable
4. Users pay their electricity bills with **HBAR or USDC** in under 2 seconds

**The problem it solves:** $2.96 billion is lost globally every year to utility billing fraud because there is no neutral, tamper-proof record of what a meter actually read. Hedera Flow creates that record.

---

## Hedera Integration

### Hedera Consensus Service (HCS)

Every verified meter reading is submitted to a regional HCS topic. This creates an immutable, publicly verifiable audit trail.

**Topics deployed:**
- Africa: `0.0.8052391`
- Europe: `0.0.8052384`
- Americas: `0.0.8052396`
- Asia: `0.0.8052389`
- South America: `0.0.8052390`

**Verify live:** https://hashscan.io/testnet/topic/0.0.8052391

**HCS message format:**
```json
{
  "type": "SMART_METER_CONSUMPTION",
  "meter_id": "SM-NG-LAG-001",
  "consumption_kwh": 245.7,
  "fraud_score": 0.17,
  "kms_signature": "3045022100...",
  "ocr_confidence": 0.95,
  "timestamp": 1710681600
}
```

### HBAR / USDC Payments

Users pay electricity bills directly from HashPack or MetaMask wallets. Exchange rates are locked for 5 minutes to protect against volatility. Settlement happens in 1.8 seconds.

**Operator account:** `0.0.7942957`  
**Network:** Hedera Testnet

---

## AWS KMS Integration (Bounty)

### What We Built

Every smart meter gets a unique cryptographic key stored inside AWS KMS hardware security modules. When a meter reading is submitted:

1. The consumption data is serialized to JSON
2. Sent to AWS KMS for signing (`MessageType='RAW'`, `SigningAlgorithm='ECDSA_SHA_256'`)
3. KMS signs it **inside the hardware vault** — the private key never leaves
4. The signature is attached to the HCS message

**Key file:** `backend/app/services/aws_kms_service.py`

**Key operations implemented:**
- `create_meter_key()` — Creates secp256k1 key per meter (HSM-backed)
- `sign_consumption_data()` — Blind signing, key stays in hardware
- `verify_signature()` — Verify any signature using public key
- `rotate_key()` — Enable 90-day automatic rotation
- `get_key_audit_trail()` — CloudTrail integration for compliance

**Security properties:**
- FIPS 140-2 Level 3 hardware
- secp256k1 curve (Hedera-compatible)
- Zero key exposure — private key never in application memory or database
- Full audit trail via AWS CloudTrail

**Database stores only the key ID, never the key:**
```sql
CREATE TABLE smart_meter_keys (
    kms_key_id VARCHAR(255) NOT NULL,  -- AWS KMS Key ID only
    public_key TEXT NOT NULL,           -- For verification
    -- NO private_key column — it lives in AWS HSM
);
```

**Relevant Hedera tutorial followed:**  
https://docs.hedera.com/hedera/tutorials/more-tutorials/HSM-signing/aws-kms

---

## Architecture Diagram

```
📱 User Phone
     │
     ▼
🌐 React Frontend (Vercel)
     │
     ▼
⚙️ FastAPI Backend (Railway)
     │
     ├──► 👁️ Google Vision OCR → Extract meter reading
     │
     ├──► 🛡️ Fraud Detection → GPS + timestamp + ELA + history
     │
     ├──► 🔐 AWS KMS HSM → Sign consumption data (blind signing)
     │         └── 📋 CloudTrail → Audit every operation
     │
     ├──► ⛓️ Hedera HCS → Immutable record (5 regional topics)
     │
     └──► 💰 Hedera Payments → HBAR/USDC bill payment (1.8s)
```

Full diagrams with Mermaid: see `docs/ARCHITECTURE.md`

---

## Demo Instructions

### Option 1: Use the Live App

1. Go to https://hedera-flow-ivory.vercel.app
2. Register with any email (e.g., `demo@test.com`, password: `Demo1234`)
3. You'll be redirected to the dashboard
4. Explore meters, bills, and payment flows

### Option 2: Test the API Directly

```bash
# Health check
curl https://hedera-flow-github-production.up.railway.app/api/health

# Register
curl -X POST https://hedera-flow-github-production.up.railway.app/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"first_name":"Demo","last_name":"User","email":"demo@test.com","password":"Demo1234","country_code":"NG"}'

# Login
curl -X POST https://hedera-flow-github-production.up.railway.app/api/auth/login \
  -d "username=demo@test.com&password=Demo1234"
```

### Option 3: View Blockchain Records

- HCS Topic: https://hashscan.io/testnet/topic/0.0.8052391
- Operator: https://hashscan.io/testnet/account/0.0.7942957

---

## Bounties Targeted

### Primary: AWS KMS Bounty
- ✅ AWS KMS HSM integration for meter key management
- ✅ Blind signing — private keys never leave hardware
- ✅ secp256k1 keys for Hedera compatibility
- ✅ CloudTrail audit trail
- ✅ Automatic key rotation
- ✅ Follows official Hedera KMS tutorial

### Main Prize: Hedera DePIN / Utility Track
- ✅ Real-world physical device integration (smart meters)
- ✅ Hedera HCS for immutable audit trail
- ✅ HBAR/USDC payments
- ✅ Multi-region deployment
- ✅ Fraud detection solving the oracle problem

---

## Technical Stack

| Component | Technology |
|-----------|-----------|
| Frontend | React 18 + TypeScript + Vite + Tailwind CSS |
| Backend | FastAPI + Python 3.11 |
| Database | PostgreSQL (Supabase) |
| Blockchain | Hedera Hashgraph (HCS + Payments) |
| Key Security | AWS KMS (HSM, secp256k1) |
| OCR | Google Cloud Vision API |
| Auth | JWT + bcrypt + HashPack + MetaMask |
| Deployment | Railway (backend) + Vercel (frontend) |

---

## Repository Structure

```
Hedera-Flow/
├── src/                          # React frontend
│   ├── components/WalletConnect.tsx
│   ├── hooks/useAuth.ts
│   └── lib/api-client.ts
├── backend/
│   ├── app/services/
│   │   ├── aws_kms_service.py    ← AWS KMS HSM integration
│   │   ├── hedera_service.py     ← Hedera HCS + payments
│   │   └── fraud_detection_service.py
│   └── app/api/endpoints/
│       ├── auth.py
│       ├── payments.py
│       └── smart_meter.py
└── docs/ARCHITECTURE.md          ← Full diagrams
```

---

## Contact

**Developer:** De real iManuel  
**Email:** nwajarieemmanuel355@gmail.com  
**GitHub:** https://github.com/De-real-iManuel  
**Project:** https://github.com/De-real-iManuel/Hedera-Flow
