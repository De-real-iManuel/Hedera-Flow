const fs = require('fs');

// Fix 1: bills.py - rename status import and parameter
let billsContent = fs.readFileSync('app/api/endpoints/bills.py', 'utf8');

// Replace the import line
billsContent = billsContent.replace(
  'from fastapi import APIRouter, Depends, HTTPException, status, Query',
  'from fastapi import APIRouter, Depends, HTTPException, Query\nfrom fastapi import status as http_status'
);

// Replace the status parameter with bill_status (using alias to keep API compatible)
billsContent = billsContent.replace(
  'status: Optional[str] = Query(None, description="Filter by status")',
  'bill_status: Optional[str] = Query(None, alias="status", description="Filter by status")'
);

// Replace all status.HTTP_ with http_status.HTTP_
billsContent = billsContent.replace(/status\.HTTP_/g, 'http_status.HTTP_');

// Replace 'if status:' with 'if bill_status:'
billsContent = billsContent.replace(/if status:/g, 'if bill_status:');

// Replace 'if status not in' with 'if bill_status not in'
billsContent = billsContent.replace(/if status not in/g, 'if bill_status not in');

// Replace 'Bill.status == status' with 'Bill.status == bill_status'
billsContent = billsContent.replace(/Bill\.status == status/g, 'Bill.status == bill_status');

fs.writeFileSync('app/api/endpoints/bills.py', billsContent);
console.log('Fixed bills.py - status shadowing issue resolved');

// Fix 2: bill.py model - comment out columns not in DB
let modelContent = fs.readFileSync('app/models/bill.py', 'utf8');

// Comment out payment_method column
modelContent = modelContent.replace(
  "    payment_method = Column(String(20), default='hbar', nullable=False)  # 'hbar', 'usdc_hedera', 'usdc_ethereum'",
  "    # payment_method = Column(String(20), default='hbar', nullable=False)  # NOT IN DB YET - needs migration"
);

// Comment out amount_usdc column
modelContent = modelContent.replace(
  "    amount_usdc = Column(DECIMAL(20, 6), nullable=True)  # USDC amount (for USDC payments)",
  "    # amount_usdc = Column(DECIMAL(20, 6), nullable=True)  # NOT IN DB YET - needs migration"
);

// Comment out usdc_token_id column
modelContent = modelContent.replace(
  "    usdc_token_id = Column(String(100), nullable=True)  # Token ID (Hedera) or contract address (Ethereum)",
  "    # usdc_token_id = Column(String(100), nullable=True)  # NOT IN DB YET - needs migration"
);

// Comment out payment_network column
modelContent = modelContent.replace(
  "    payment_network = Column(String(20), nullable=True)  # 'hedera' or 'ethereum'",
  "    # payment_network = Column(String(20), nullable=True)  # NOT IN DB YET - needs migration"
);

// Comment out ethereum_tx_hash column
modelContent = modelContent.replace(
  '    ethereum_tx_hash = Column(String(66), nullable=True)  # Ethereum transaction hash',
  '    # ethereum_tx_hash = Column(String(66), nullable=True)  # NOT IN DB YET - needs migration'
);

// Comment out payment_method constraint - handle CRLF
modelContent = modelContent.replace(
  /CheckConstraint\(\r?\n\s+"payment_method IN \('hbar', 'usdc_hedera', 'usdc_ethereum'\)",\r?\n\s+name="check_payment_method"\r?\n\s+\),/g,
  `# CheckConstraint(
        #     "payment_method IN ('hbar', 'usdc_hedera', 'usdc_ethereum')",
        #     name="check_payment_method"
        # ),  # NOT IN DB YET`
);

// Comment out payment_network constraint - handle CRLF
modelContent = modelContent.replace(
  /CheckConstraint\(\r?\n\s+"payment_network IS NULL OR payment_network IN \('hedera', 'ethereum'\)",\r?\n\s+name="check_payment_network"\r?\n\s+\),/g,
  `# CheckConstraint(
        #     "payment_network IS NULL OR payment_network IN ('hedera', 'ethereum')",
        #     name="check_payment_network"
        # ),  # NOT IN DB YET`
);

fs.writeFileSync('app/models/bill.py', modelContent);
console.log('Fixed bill.py model - commented out columns not in DB');

console.log('\nDone! Both files have been patched.');
