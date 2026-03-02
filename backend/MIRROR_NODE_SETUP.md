# Hedera Mirror Node Integration

## Overview

The Mirror Node integration provides access to historical Hedera blockchain data through the Mirror Node REST API. This enables querying of past HCS messages, transactions, and account information.

## What is a Mirror Node?

Hedera Mirror Nodes store the history of transactions and provide a REST API to query this data. Unlike the main Hedera network which focuses on consensus and real-time operations, Mirror Nodes are optimized for historical queries and analytics.

**Key Features:**
- Query historical HCS topic messages
- Retrieve transaction details
- Get account information and balances
- Search and filter blockchain data
- Pagination support for large datasets

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Application Layer                         │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  FastAPI Backend                                     │  │
│  │  - Verification Service                              │  │
│  │  - Payment Service                                   │  │
│  │  - Dispute Service                                   │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                         │
                         ↓
┌─────────────────────────────────────────────────────────────┐
│                    Hedera Client Layer                       │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  hedera_client.py                                    │  │
│  │  - Real-time operations (submit messages)           │  │
│  │  - Account management                                │  │
│  │  - Transaction submission                            │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  mirror_node_client.py                               │  │
│  │  - Historical queries                                │  │
│  │  - Message retrieval                                 │  │
│  │  - Transaction lookup                                │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                         │
                         ↓
┌─────────────────────────────────────────────────────────────┐
│                    Hedera Network                            │
│                                                              │
│  ┌──────────────────┐         ┌──────────────────┐         │
│  │  Consensus       │         │  Mirror Node     │         │
│  │  Nodes           │────────▶│  REST API        │         │
│  │  (Real-time)     │         │  (Historical)    │         │
│  └──────────────────┘         └──────────────────┘         │
│                                                              │
│  Testnet: https://testnet.mirrornode.hedera.com            │
│  Mainnet: https://mainnet-public.mirrornode.hedera.com     │
└─────────────────────────────────────────────────────────────┘
```

## Configuration

### Environment Variables

Add to your `.env` file:

```bash
# Mirror Node Configuration
HEDERA_MIRROR_NODE_URL=https://testnet.mirrornode.hedera.com

# For mainnet (production):
# HEDERA_MIRROR_NODE_URL=https://mainnet-public.mirrornode.hedera.com
```

### HCS Topics

Configure your regional HCS topics:

```bash
HCS_TOPIC_EU=0.0.xxxxx      # Europe topic
HCS_TOPIC_US=0.0.xxxxx      # USA topic
HCS_TOPIC_ASIA=0.0.xxxxx    # Asia topic
HCS_TOPIC_SA=0.0.xxxxx      # South America topic
HCS_TOPIC_AFRICA=0.0.xxxxx  # Africa topic
```

## Usage Examples

### 1. Query Recent HCS Messages

```python
from app.utils.mirror_node_client import mirror_node_client

# Get last 10 messages from a topic
messages = await mirror_node_client.get_topic_messages(
    topic_id="0.0.12345",
    limit=10,
    order="desc"
)

for msg in messages["messages"]:
    print(f"Sequence: {msg['sequence_number']}")
    print(f"Timestamp: {msg['consensus_timestamp']}")
    print(f"Message: {msg['message_decoded']}")
```

### 2. Get Specific Message by Sequence Number

```python
# Get message #42 from topic
message = await mirror_node_client.get_topic_message_by_sequence(
    topic_id="0.0.12345",
    sequence_number=42
)

print(f"Message data: {message['message_decoded']}")
```

### 3. Search Verification Logs

```python
# Search for verified bills for a specific meter
verifications = await mirror_node_client.search_verification_logs(
    topic_id="0.0.12345",
    meter_id="ESP-12345678",
    status="VERIFIED",
    limit=20
)

for log in verifications:
    data = log["data"]
    print(f"Reading: {data['reading']} kWh")
    print(f"Confidence: {data['confidence']}")
    print(f"Status: {data['status']}")
```

### 4. Search Payment Logs

```python
# Find payment for a specific bill
payments = await mirror_node_client.search_payment_logs(
    topic_id="0.0.12345",
    bill_id="BILL-ES-2024-001",
    limit=10
)

for payment in payments:
    data = payment["data"]
    print(f"Amount: {data['amountHbar']} HBAR")
    print(f"Fiat: {data['amountFiat']} {data['currencyFiat']}")
    print(f"TX ID: {data['txId']}")
```

### 5. Get Transaction Details

```python
# Look up a specific transaction
tx_id = "0.0.12345@1234567890.123456789"
transaction = await mirror_node_client.get_transaction(tx_id)

print(f"Type: {transaction['name']}")
print(f"Result: {transaction['result']}")
print(f"Fee: {transaction['charged_tx_fee']}")
```

### 6. Get Account Information

```python
# Get account balance and info
account = await mirror_node_client.get_account_info("0.0.12345")

balance_hbar = account["balance"]["balance"] / 100000000
print(f"Balance: {balance_hbar} HBAR")
print(f"Created: {account['created_timestamp']}")
```

### 7. Get Account Transactions

```python
# Get recent transactions for an account
transactions = await mirror_node_client.get_account_transactions(
    account_id="0.0.12345",
    limit=20,
    order="desc",
    transaction_type="CRYPTOTRANSFER"
)

for tx in transactions["transactions"]:
    print(f"TX: {tx['transaction_id']}")
    print(f"Type: {tx['name']}")
    print(f"Time: {tx['consensus_timestamp']}")
```

## API Endpoints Reference

### Mirror Node REST API

Base URL: `https://testnet.mirrornode.hedera.com/api/v1`

#### Topic Messages

```
GET /topics/{topicId}/messages
GET /topics/{topicId}/messages/{sequenceNumber}
```

**Query Parameters:**
- `limit`: Max results (1-100, default: 25)
- `order`: Sort order (`asc` or `desc`)
- `sequencenumber`: Filter by sequence number
- `timestamp`: Filter by timestamp (format: `gte:seconds.nanos` or `lte:seconds.nanos`)

#### Transactions

```
GET /transactions
GET /transactions/{transactionId}
```

**Query Parameters:**
- `account.id`: Filter by account
- `limit`: Max results
- `order`: Sort order
- `transactiontype`: Filter by type (e.g., `CRYPTOTRANSFER`, `CONSENSUSSUBMITMESSAGE`)

#### Accounts

```
GET /accounts/{accountId}
```

## Message Format

### Verification Log

```json
{
  "type": "VERIFICATION",
  "timestamp": 1710789600,
  "userId": "uuid-anonymized",
  "meterId": "ESP-12345678",
  "reading": 5142.7,
  "utilityReading": 5089.2,
  "confidence": 0.96,
  "fraudScore": 0.12,
  "status": "VERIFIED",
  "imageHash": "ipfs://Qm..."
}
```

### Payment Log

```json
{
  "type": "PAYMENT",
  "timestamp": 1710789700,
  "billId": "BILL-ES-2024-001",
  "amountFiat": 85.40,
  "currencyFiat": "EUR",
  "amountHbar": 251.17,
  "exchangeRate": 0.34,
  "txId": "0.0.123456@1710789700.123",
  "status": "SUCCESS"
}
```

### Dispute Log

```json
{
  "type": "DISPUTE_CREATED",
  "timestamp": 1710789800,
  "disputeId": "DISP-ES-2024-001",
  "billId": "BILL-ES-2024-001",
  "reason": "OVERCHARGE",
  "evidenceHashes": ["ipfs://Qm1...", "ipfs://Qm2..."],
  "escrowAmountHbar": 251.17,
  "status": "PENDING"
}
```

## Testing

### Run Mirror Node Tests

```bash
cd backend
python test_mirror_node.py
```

This will test:
1. Account information queries
2. Transaction retrieval
3. HCS topic message queries
4. Pagination
5. Search functionality

### Manual Testing with curl

```bash
# Get account info
curl "https://testnet.mirrornode.hedera.com/api/v1/accounts/0.0.12345"

# Get topic messages
curl "https://testnet.mirrornode.hedera.com/api/v1/topics/0.0.12345/messages?limit=5&order=desc"

# Get specific message
curl "https://testnet.mirrornode.hedera.com/api/v1/topics/0.0.12345/messages/42"

# Get transaction
curl "https://testnet.mirrornode.hedera.com/api/v1/transactions/0.0.12345@1234567890.123456789"
```

## Integration with Application

### Verification Service

```python
from app.utils.mirror_node_client import mirror_node_client

async def get_verification_history(meter_id: str, limit: int = 20):
    """Get verification history for a meter"""
    
    # Determine topic based on meter's country
    topic_id = get_topic_for_meter(meter_id)
    
    # Query Mirror Node
    verifications = await mirror_node_client.search_verification_logs(
        topic_id=topic_id,
        meter_id=meter_id,
        limit=limit
    )
    
    return verifications
```

### Payment Service

```python
async def verify_payment_on_chain(bill_id: str, tx_id: str):
    """Verify payment was recorded on blockchain"""
    
    # Get transaction from Mirror Node
    tx = await mirror_node_client.get_transaction(tx_id)
    
    # Verify transaction succeeded
    if tx["result"] != "SUCCESS":
        raise Exception("Transaction failed")
    
    # Search for payment log in HCS
    topic_id = get_topic_for_bill(bill_id)
    payments = await mirror_node_client.search_payment_logs(
        topic_id=topic_id,
        bill_id=bill_id
    )
    
    # Verify payment was logged
    if not payments:
        raise Exception("Payment not found in HCS logs")
    
    return True
```

### Audit Trail

```python
async def generate_audit_trail(user_id: str):
    """Generate complete audit trail for user"""
    
    audit_trail = {
        "verifications": [],
        "payments": [],
        "disputes": []
    }
    
    # Get all user's meters
    meters = get_user_meters(user_id)
    
    # Query verifications for each meter
    for meter in meters:
        topic_id = get_topic_for_meter(meter.id)
        verifications = await mirror_node_client.search_verification_logs(
            topic_id=topic_id,
            meter_id=meter.meter_id,
            limit=100
        )
        audit_trail["verifications"].extend(verifications)
    
    return audit_trail
```

## Performance Considerations

### Rate Limits

Mirror Node API has rate limits:
- **Testnet**: ~100 requests/second
- **Mainnet**: ~100 requests/second

Implement caching for frequently accessed data:

```python
from functools import lru_cache
import asyncio

@lru_cache(maxsize=100)
async def get_cached_topic_messages(topic_id: str, limit: int):
    """Cache topic messages for 5 minutes"""
    return await mirror_node_client.get_topic_messages(
        topic_id=topic_id,
        limit=limit
    )
```

### Pagination

For large datasets, use pagination:

```python
async def get_all_messages(topic_id: str):
    """Get all messages using pagination"""
    
    all_messages = []
    next_link = None
    
    while True:
        response = await mirror_node_client.get_topic_messages(
            topic_id=topic_id,
            limit=100
        )
        
        all_messages.extend(response["messages"])
        
        next_link = response.get("links", {}).get("next")
        if not next_link:
            break
    
    return all_messages
```

## Troubleshooting

### Common Issues

**1. Connection Timeout**
```
Error: Connection timeout to Mirror Node
```
Solution: Check network connectivity, verify Mirror Node URL is correct

**2. Topic Not Found**
```
Error: 404 - Topic not found
```
Solution: Verify topic ID exists and is correctly formatted (e.g., "0.0.12345")

**3. Message Decoding Failed**
```
Warning: Failed to decode message
```
Solution: Ensure messages are valid JSON and base64 encoded correctly

**4. Rate Limit Exceeded**
```
Error: 429 - Too Many Requests
```
Solution: Implement rate limiting and caching in your application

## Best Practices

1. **Cache Frequently Accessed Data**: Use Redis to cache Mirror Node responses
2. **Implement Retry Logic**: Handle transient failures with exponential backoff
3. **Use Pagination**: Don't fetch all data at once for large datasets
4. **Filter at API Level**: Use query parameters to filter data server-side
5. **Monitor Rate Limits**: Track API usage to avoid hitting limits
6. **Handle Errors Gracefully**: Provide fallbacks when Mirror Node is unavailable

## Resources

- [Hedera Mirror Node Documentation](https://docs.hedera.com/hedera/sdks-and-apis/rest-api)
- [Mirror Node REST API Spec](https://testnet.mirrornode.hedera.com/api/v1/docs/)
- [Hedera Explorer (HashScan)](https://hashscan.io/testnet)

## Summary

The Mirror Node integration provides:
- ✅ Historical HCS message queries
- ✅ Transaction verification
- ✅ Account information lookup
- ✅ Audit trail generation
- ✅ Search and filter capabilities
- ✅ Pagination support

This enables the Hedera Flow MVP to provide complete transparency and auditability for all blockchain operations.
