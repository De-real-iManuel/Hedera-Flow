/**
 * Fix Backend Issues Script
 * 
 * Issue 1: bills.payment_method missing column error
 * Issue 2: fastapi.status shadowing by query param named 'status'
 */

const fs = require('fs');
const path = require('path');

// Fix 1: backend/app/models/bill.py - Comment out missing columns
const billModelPath = path.join(__dirname, '..', 'backend', 'app', 'models', 'bill.py');
let billModel = fs.readFileSync(billModelPath, 'utf8');

// Comment out payment_method column
billModel = billModel.replace(
  /payment_method = Column\(String\(20\), default='hbar', nullable=False\)  # 'hbar', 'usdc_hedera', 'usdc_ethereum'/,
  "# FIX: Column doesn't exist in database migration - commented out\n    # payment_method = Column(String(20), default='hbar', nullable=False)  # 'hbar', 'usdc_hedera', 'usdc_ethereum'"
);

// Comment out amount_usdc column
billModel = billModel.replace(
  /amount_usdc = Column\(DECIMAL\(20, 6\), nullable=True\)  # USDC amount \(for USDC payments\)/,
  "# amount_usdc = Column(DECIMAL(20, 6), nullable=True)  # USDC amount (for USDC payments) - NOT IN DATABASE"
);

// Comment out usdc_token_id column
billModel = billModel.replace(
  /usdc_token_id = Column\(String\(100\), nullable=True\)  # Token ID \(Hedera\) or contract address \(Ethereum\)/,
  "# usdc_token_id = Column(String(100), nullable=True)  # Token ID (Hedera) or contract address (Ethereum) - NOT IN DATABASE"
);

// Comment out payment_network column
billModel = billModel.replace(
  /payment_network = Column\(String\(20\), nullable=True\)  # 'hedera' or 'ethereum'/,
  "# payment_network = Column(String(20), nullable=True)  # 'hedera' or 'ethereum' - NOT IN DATABASE"
);

// Comment out ethereum_tx_hash column
billModel = billModel.replace(
  /ethereum_tx_hash = Column\(String\(66\), nullable=True\)  # Ethereum transaction hash/,
  "# ethereum_tx_hash = Column(String(66), nullable=True)  # Ethereum transaction hash - NOT IN DATABASE"
);

// Comment out payment_method constraint
billModel = billModel.replace(
  /CheckConstraint\(\s*"payment_method IN \('hbar', 'usdc_hedera', 'usdc_ethereum'\)",\s*name="check_payment_method"\s*\),/gs,
  "# FIX: Commented out - payment_method column doesn't exist in database\n        # CheckConstraint(\n        #     \"payment_method IN ('hbar', 'usdc_hedera', 'usdc_ethereum')\",\n        #     name=\"check_payment_method\"\n        # ),"
);

// Comment out payment_network constraint
billModel = billModel.replace(
  /CheckConstraint\(\s*"payment_network IS NULL OR payment_network IN \('hedera', 'ethereum'\)",\s*name="check_payment_network"\s*\),/gs,
  "# FIX: Commented out - payment_network column doesn't exist in database\n        # CheckConstraint(\n        #     \"payment_network IS NULL OR payment_network IN ('hedera', 'ethereum')\",\n        #     name=\"check_payment_network\"\n        # ),"
);

fs.writeFileSync(billModelPath, billModel);
console.log('✅ Fixed backend/app/models/bill.py');

// Fix 2: backend/app/api/endpoints/bills.py - Fix status shadowing
const billsEndpointPath = path.join(__dirname, '..', 'backend', 'app', 'api', 'endpoints', 'bills.py');
let billsEndpoint = fs.readFileSync(billsEndpointPath, 'utf8');

// Fix import - rename status to http_status
billsEndpoint = billsEndpoint.replace(
  /from fastapi import APIRouter, Depends, HTTPException, status, Query/,
  '# FIX: Import status as http_status to avoid shadowing by query parameter named "status"\nfrom fastapi import APIRouter, Depends, HTTPException, status as http_status, Query'
);

// Fix query parameter - rename to bill_status with alias
billsEndpoint = billsEndpoint.replace(
  /status: Optional\[str\] = Query\(None, description="Filter by status"\),/,
  '# FIX: Renamed parameter to bill_status with alias to avoid shadowing fastapi.status\n    bill_status: Optional[str] = Query(None, alias="status", description="Filter by status"),'
);

// Replace all status.HTTP_ with http_status.HTTP_
billsEndpoint = billsEndpoint.replace(/status\.HTTP_/g, 'http_status.HTTP_');

// Fix the status filter check (if status: -> if bill_status:)
billsEndpoint = billsEndpoint.replace(
  /if status:\r?\n\s*if status not in \['pending', 'paid', 'disputed', 'refunded'\]:/,
  "if bill_status:\n            if bill_status not in ['pending', 'paid', 'disputed', 'refunded']:"
);

// Fix the query filter (Bill.status == status -> Bill.status == bill_status)
billsEndpoint = billsEndpoint.replace(
  /query = query\.filter\(Bill\.status == status\)/,
  'query = query.filter(Bill.status == bill_status)'
);

fs.writeFileSync(billsEndpointPath, billsEndpoint);
console.log('✅ Fixed backend/app/api/endpoints/bills.py');

console.log('\n✅ Both files patched successfully!');
