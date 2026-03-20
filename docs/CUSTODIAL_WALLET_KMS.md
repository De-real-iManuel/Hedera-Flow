# Custodial Wallet & AWS KMS Key Management

This document covers the end-to-end implementation of custodial Hedera account creation, 50 HBAR airdrop, and AWS KMS-backed private key storage in Hedera Flow.

---

## Overview

When a user registers without an existing wallet, the platform automatically:

1. Creates a real Hedera testnet account via the Hedera SDK
2. Funds it with **50 HBAR** from the operator treasury (`0.0.7942971`)
3. Encrypts the new account's private key inside **AWS KMS** (HSM-backed)
4. Stores only the **KMS key ARN** in the database — the plaintext private key never touches the DB or logs

---

## Registration Flow

```mermaid
sequenceDiagram
    participant U as User (Browser)
    participant API as FastAPI (Railway)
    participant HS as HederaService
    participant HN as Hedera Testnet
    participant KMS as AWS KMS (HSM)
    participant DB as PostgreSQL

    U->>API: POST /api/auth/register<br/>{email, password, country_code}

    API->>API: Validate password strength<br/>Hash password (bcrypt cost=12)

    API->>HS: create_account(initial_balance=50 HBAR)
    HS->>HN: AccountCreateTransaction<br/>(new keypair, fund from operator)
    HN-->>HS: account_id (0.0.xxxxxxx)<br/>private_key (302e...)
    HS-->>API: (account_id, private_key_str)

    Note over API,KMS: Private key exists in memory ONLY at this point

    API->>KMS: kms.encrypt(KeyId=master_key_arn, Plaintext=private_key_bytes)
    KMS-->>API: CiphertextBlob (encrypted bytes)<br/>KeyId (KMS key ARN)

    Note over API: Plaintext private key is discarded from memory

    API->>DB: INSERT users SET<br/>hedera_account_id = "0.0.xxxxxxx"<br/>kms_key_id = "arn:aws:kms:..."<br/>preferences.encrypted_hedera_key = base64(CiphertextBlob)

    Note over DB: NO plaintext private key ever written

    API->>API: Generate JWT access_token + refresh_token
    API-->>U: 201 Created<br/>{user, hedera_account_id, access_token}<br/>+ httpOnly cookies
```

---

## KMS Proof Endpoint

`GET /api/auth/kms-proof` (requires auth) returns live evidence that the key is in KMS, not the DB.

```mermaid
sequenceDiagram
    participant U as Authenticated User
    participant API as FastAPI
    participant KMS as AWS KMS
    participant MN as Hedera Mirror Node

    U->>API: GET /api/auth/kms-proof<br/>Authorization: Bearer <token>

    API->>API: Load user from DB<br/>Read kms_key_id (ARN only — no plaintext key)

    API->>KMS: describe_key(KeyId=kms_key_id)
    KMS-->>API: KeyMetadata {<br/>  key_state: "Enabled",<br/>  origin: "AWS_KMS",<br/>  key_usage: "ENCRYPT_DECRYPT"<br/>}

    API->>MN: GET /api/v1/accounts/{hedera_account_id}
    MN-->>API: balance: { balance: 5000000000 tinybars }

    API-->>U: {<br/>  hedera_account_id: "0.0.xxxxxxx",<br/>  kms_key_id: "arn:aws:kms:...",<br/>  db_has_plaintext_key: false,<br/>  has_encrypted_key: true,<br/>  kms_key_metadata: { origin: "AWS_KMS", ... },<br/>  hedera_balance_hbar: 50.0,<br/>  proof_statement: "..."<br/>}
```

---

## Wallet Connect Flow (Existing Wallet)

Users with HashPack or MetaMask skip account creation entirely.

```mermaid
sequenceDiagram
    participant U as User (Browser)
    participant API as FastAPI
    participant HS as HederaService
    participant MN as Hedera Mirror Node
    participant DB as PostgreSQL

    U->>API: POST /api/auth/wallet-connect<br/>{hedera_account_id, signature, message}

    alt Hedera native wallet (0.0.xxx)
        API->>MN: GET /accounts/{account_id}
        MN-->>API: 200 OK (account exists)
        API->>HS: verify_signature(account_id, message, signature)
        HS-->>API: true / false
    else MetaMask (0x...)
        API->>API: Accept signature (EVM verification MVP)
    end

    alt User already exists
        API->>DB: UPDATE last_login
        DB-->>API: existing user
    else New wallet user
        API->>DB: INSERT users<br/>{wallet_email, hedera_account_id, wallet_type=hashpack}
        DB-->>API: new user
    end

    API-->>U: 200 OK {user, access_token}<br/>+ httpOnly cookies
```

---

## Token Refresh & Session Management

```mermaid
sequenceDiagram
    participant U as Browser
    participant API as FastAPI

    Note over U: access_token expires after 15 min

    U->>API: POST /api/auth/refresh-token<br/>(refresh_token cookie sent automatically)

    API->>API: Decode refresh_token JWT<br/>Verify type == "refresh"<br/>Load user from DB

    API->>API: Generate new access_token (15 min)<br/>Generate new refresh_token (7 days)

    API-->>U: 200 OK {user}<br/>Set-Cookie: access_token (new)<br/>Set-Cookie: refresh_token (new)

    Note over U,API: Both tokens rotated on every refresh
```

---

## Schema Migration Strategy

Railway's PostgreSQL doesn't auto-apply model changes. The app runs migrations on every startup.

```mermaid
flowchart TD
    A[App starts on Railway] --> B[run_schema_migrations called\nbefore lifespan yield]
    B --> C{For each ALTER TABLE\nstatement}
    C --> D[Open new DB connection]
    D --> E[Execute single DDL statement\nALTER TABLE users ADD COLUMN IF NOT EXISTS ...]
    E --> F{Success?}
    F -->|Yes| G[conn.commit]
    F -->|No - column exists| H[WARN logged, continue]
    G --> C
    H --> C
    C -->|All statements done| I[Seed utility providers\nON CONFLICT DO NOTHING]
    I --> J[Seed tariffs per-row\nWHERE NOT EXISTS check]
    J --> K[App ready to serve requests]

    style A fill:#2d6a4f,color:#fff
    style K fill:#2d6a4f,color:#fff
    style H fill:#e76f51,color:#fff
```

**Why individual statements?** psycopg2 aborts the entire transaction on any error. Batching multiple `ALTER TABLE` statements in one `execute()` call means a single "column already exists" error kills all subsequent migrations. Each statement gets its own connection and commit.

**Emergency fix endpoint:** `POST /api/health/fix-schema` runs the same statements and returns which columns now exist — useful immediately after a deploy if Railway logs show `UndefinedColumn`.

---

## Prepaid Token Purchase Flow

```mermaid
sequenceDiagram
    participant U as User
    participant API as FastAPI
    participant TS as TariffService
    participant HS as HederaService
    participant HN as Hedera Testnet
    participant HCS as Hedera Consensus Service
    participant DB as PostgreSQL

    U->>API: POST /api/prepaid/pay-custodial<br/>{meter_id, amount_fiat, currency}

    API->>TS: get_tariff(country_code, utility_provider)
    TS-->>API: tariff {rate_structure, currency}

    API->>API: Calculate kWh units from fiat amount\nConvert fiat → HBAR via exchange rate

    API->>HS: transfer_hbar(treasury_id → operator, amount_hbar)
    HS->>HN: TransferTransaction (signed by operator)
    HN-->>HS: tx_id, receipt

    API->>HS: log_payment_to_hcs(topic_id, bill_id, ...)
    HS->>HCS: TopicMessageSubmitTransaction
    HCS-->>HS: sequence_number

    API->>DB: INSERT prepaid_tokens\n{token_id, units, hedera_tx_id, hcs_sequence_number}

    API-->>U: {token, transaction_details}
```

---

## Bill Verification (OCR + Hedera)

```mermaid
flowchart LR
    A[User uploads\nbill image] --> B[Google Vision OCR\nextract reading + amount]
    B --> C{Fraud detection\ncheck}
    C -->|Pass| D[Calculate bill\nwith tariff rates]
    C -->|Suspicious| E[Flag for review]
    D --> F[Store bill in DB]
    F --> G[Log to HCS topic\nby country/region]
    G --> H[Return verification\nresult + HCS proof]

    subgraph HCS Topics
        T1[EU - Spain]
        T2[US]
        T3[Asia - India]
        T4[SA - Brazil]
        T5[Africa - Nigeria]
    end

    G --> T1
    G --> T2
    G --> T3
    G --> T4
    G --> T5
```

---

## Security Properties

| Property | Implementation |
|---|---|
| Private key never in DB | Only `kms_key_id` (ARN) stored; ciphertext in `preferences.encrypted_hedera_key` |
| Private key never in logs | Discarded from memory immediately after KMS encrypt call |
| Key material in HSM | KMS `origin: "AWS_KMS"` — key material generated and stored in FIPS 140-2 Level 3 HSM |
| Audit trail | Every KMS operation logged in AWS CloudTrail |
| Token expiry | Access tokens: 15 min · Refresh tokens: 7 days · Both rotated on refresh |
| Cookie security | `httpOnly=True`, `secure=True`, `samesite=none` on Railway (HTTPS) |
| Password hashing | bcrypt cost factor 12 |
| Fallback on SDK failure | Account marked `0.0.PENDING_xxxx` — user can link wallet later |

---

## Environment Variables Required

```env
# Hedera
HEDERA_NETWORK=testnet
HEDERA_OPERATOR_ID=0.0.xxxxxxx
HEDERA_OPERATOR_KEY=302e...
HEDERA_TREASURY_ID=0.0.7942971

# AWS KMS
AWS_KMS_REGION=us-east-1
AWS_KMS_MASTER_KEY_ID=arn:aws:kms:us-east-1:...

# HCS Topics (per region)
HCS_TOPIC_EU=0.0.xxxxxxx
HCS_TOPIC_US=0.0.xxxxxxx
HCS_TOPIC_ASIA=0.0.xxxxxxx
HCS_TOPIC_SA=0.0.xxxxxxx
HCS_TOPIC_AFRICA=0.0.xxxxxxx
```

---

## Existing Users

Users registered before this implementation have `evm_address = NULL` and `kms_key_id = NULL`. They can still log in normally. To get a custodial Hedera account they can:

- Re-register (new account)
- Use `PATCH /api/auth/link-wallet` to attach an existing HashPack/MetaMask wallet

Backfilling existing users with new Hedera accounts requires a separate migration script and is not done automatically.
