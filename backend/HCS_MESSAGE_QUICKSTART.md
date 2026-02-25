# HCS Message Submission - Quick Start Guide

## 🚀 Quick Usage (3 Steps)

### Step 1: Import the Client

```python
from app.utils.hedera_client import submit_message, get_topic_info
```

### Step 2: Submit a Message

```python
# Verification message
message = {
    "type": "VERIFICATION",
    "timestamp": int(time.time()),
    "user_id": "user-123",
    "meter_id": "ESP-12345",
    "reading": 1234.5,
    "confidence": 0.95,
    "status": "VERIFIED"
}

# Submit to EU topic
result = await submit_message("0.0.YOUR_TOPIC_ID", message)

print(f"Transaction ID: {result['tx_id']}")
print(f"Sequence Number: {result['sequence_number']}")
```

### Step 3: Verify Submission

```python
# Get topic info
info = await get_topic_info("0.0.YOUR_TOPIC_ID")

print(f"Total Messages: {info['sequence_number']}")
print(f"Topic Memo: {info['memo']}")
```

## 📋 Message Types

### Verification Message (FR-5.13)

```python
verification_msg = {
    "type": "VERIFICATION",
    "timestamp": int(time.time()),
    "user_id": "uuid-anonymized",
    "meter_id": "ESP-12345678",
    "reading": 5142.7,
    "utility_reading": 5089.2,
    "confidence": 0.96,
    "fraud_score": 0.12,
    "status": "VERIFIED",
    "image_hash": "ipfs://Qm..."
}

result = await submit_message(topic_id, verification_msg)
```

### Payment Message (FR-5.14)

```python
payment_msg = {
    "type": "PAYMENT",
    "timestamp": int(time.time()),
    "bill_id": "BILL-ES-2024-001",
    "amount_fiat": 85.40,
    "currency_fiat": "EUR",
    "amount_hbar": 251.17,
    "exchange_rate": 0.34,
    "tx_id": "0.0.123456@1710789700.123",
    "status": "SUCCESS"
}

result = await submit_message(topic_id, payment_msg)
```

### Dispute Message (FR-5.15)

```python
dispute_msg = {
    "type": "DISPUTE_CREATED",
    "timestamp": int(time.time()),
    "dispute_id": "DISP-ES-2024-001",
    "bill_id": "BILL-ES-2024-001",
    "reason": "OVERCHARGE",
    "description": "Bill amount higher than expected",
    "evidence_hashes": ["ipfs://QmEvidence1"],
    "escrow_amount_hbar": 251.17,
    "status": "PENDING"
}

result = await submit_message(topic_id, dispute_msg)
```

## 🌍 Regional Topics

```python
import os

# Map country code to topic
def get_regional_topic(country_code: str) -> str:
    topics = {
        'ES': os.getenv('HCS_TOPIC_EU'),      # Spain → EU
        'US': os.getenv('HCS_TOPIC_US'),      # USA → US
        'IN': os.getenv('HCS_TOPIC_ASIA'),    # India → Asia
        'BR': os.getenv('HCS_TOPIC_SA'),      # Brazil → South America
        'NG': os.getenv('HCS_TOPIC_AFRICA')   # Nigeria → Africa
    }
    return topics.get(country_code)

# Usage
topic_id = get_regional_topic(user.country_code)
result = await submit_message(topic_id, message)
```

## ✅ Test Your Setup

```bash
cd backend
python scripts/validate_task_3_5.py
```

Expected output:
```
✅ TASK 3.5 VALIDATION COMPLETE
🎉 All tests passed successfully!
```

## 🔗 View Messages

### On HashScan

**Topic View:**
```
https://hashscan.io/testnet/topic/{TOPIC_ID}
```

**Transaction View:**
```
https://hashscan.io/testnet/transaction/{TX_ID}
```

### Using Mirror Node API (Task 3.6)

```bash
# Get all messages from topic
curl https://testnet.mirrornode.hedera.com/api/v1/topics/{TOPIC_ID}/messages

# Get specific message
curl https://testnet.mirrornode.hedera.com/api/v1/topics/{TOPIC_ID}/messages/{SEQUENCE_NUMBER}
```

## 💰 Cost

- **Message Submission**: ~0.0001 HBAR per message
- **Topic Query**: Free (not a transaction)

Example for 100 users/month:
- 500 verifications: 0.05 HBAR
- 200 payments: 0.02 HBAR
- 50 disputes: 0.005 HBAR
- **Total**: ~0.075 HBAR (~$0.025)

## 🔧 Troubleshooting

**"No topic configured"**
```bash
# Create topics
python scripts/create_hcs_topics.py

# Or use test topic
python scripts/validate_task_3_5.py
```

**"Insufficient balance"**
- Get testnet HBAR: https://portal.hedera.com/

**"Transaction failed"**
- Check operator credentials in `.env`
- Verify HBAR balance
- Check network status: https://status.hedera.com/

## 📚 Full Documentation

- **Task Summary**: `TASK_3.5_COMPLETE.md`
- **Comprehensive Tests**: `scripts/test_hcs_message_flow.py`
- **Validation Script**: `scripts/validate_task_3_5.py`
- **Hedera Client**: `app/utils/hedera_client.py`

## ⏭️ Next Steps

- **Task 3.6**: Configure Mirror Node API access
- **Task 13.8**: Integrate HCS logging in verification flow
- **Task 19.5**: Integrate HCS logging in payment flow
- **Task 22.6**: Integrate HCS logging in dispute flow

## 💡 Best Practices

1. **Always use regional topics** - Route messages to correct region
2. **Include timestamps** - Use `int(time.time())` for consistency
3. **Anonymize user data** - Hash or truncate sensitive IDs
4. **Store sequence numbers** - Save in database for retrieval
5. **Handle errors gracefully** - HCS submission can fail
6. **Test on testnet first** - Verify before mainnet deployment

## 🎯 Integration Example

```python
# In your verification service
async def create_verification(user_id, meter_id, reading):
    # 1. Perform verification
    verification = await verify_meter_reading(meter_id, reading)
    
    # 2. Save to database
    db_verification = await db.save_verification(verification)
    
    # 3. Log to HCS
    try:
        hcs_message = {
            "type": "VERIFICATION",
            "timestamp": int(time.time()),
            "user_id": user_id,
            "meter_id": meter_id,
            "reading": reading,
            "status": verification.status
        }
        
        topic_id = get_regional_topic(user.country_code)
        hcs_result = await submit_message(topic_id, hcs_message)
        
        # 4. Update database with HCS reference
        db_verification.hcs_topic_id = topic_id
        db_verification.hcs_sequence_number = hcs_result['sequence_number']
        await db.save(db_verification)
        
    except Exception as e:
        # Log error but don't fail verification
        logger.error(f"HCS logging failed: {e}")
    
    return db_verification
```

---

**Status**: ✅ Ready to Use  
**Requirements**: FR-5.13, FR-5.14, FR-5.15  
**Task**: 3.5 Complete
