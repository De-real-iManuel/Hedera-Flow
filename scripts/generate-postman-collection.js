/**
 * Script to generate Postman v3 YAML collection for Hedera Flow API
 * Based on FastAPI backend route analysis
 */

const fs = require('fs');
const path = require('path');

const COLLECTIONS_DIR = path.join(__dirname, '..', 'postman', 'collections');
const COLLECTION_NAME = 'Hedera Flow API';

// Ensure directories exist
function ensureDir(dir) {
  if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir, { recursive: true });
  }
}

// Collection definition
const collectionDefinition = `$kind: collection
name: Hedera Flow API
description: |-
  API collection for Hedera Flow - a blockchain-powered utility payment platform.
  
  ## Authentication
  Most endpoints require JWT Bearer token authentication. Obtain a token via:
  - POST /auth/register - Create new account
  - POST /auth/login - Login with email/password
  - POST /auth/wallet-connect - Connect via Hedera wallet
  
  ## Base URL
  Set the \`base_url\` variable to your API server (default: http://localhost:8000)
  
  ## Supported Countries
  ES (Spain), US (USA), IN (India), BR (Brazil), NG (Nigeria)
variables:
  - key: base_url
    value: 'http://localhost:8000'
    description: API base URL
  - key: auth_token
    value: ''
    description: JWT Bearer token (set after login)
auth:
  type: bearer
  credentials:
    - key: token
      value: '{{auth_token}}'
scripts:
  - type: 'http:afterResponse'
    language: text/javascript
    code: |-
      // Auto-capture auth token from login/register responses
      if (pm.response.code === 200 || pm.response.code === 201) {
        try {
          const json = pm.response.json();
          if (json.token) {
            pm.collectionVariables.set('auth_token', json.token);
            console.log('Auth token captured and saved to collection variables');
          }
        } catch (e) {
          // Response is not JSON, ignore
        }
      }
`;

// Folder definitions
const folders = {
  'health': {
    name: 'Health',
    description: 'Health check endpoints for monitoring API status',
    order: 1000
  },
  'auth': {
    name: 'Authentication',
    description: 'User registration, login, and wallet connection endpoints',
    order: 2000
  },
  'user': {
    name: 'User Management',
    description: 'User profile, preferences, notifications, and security settings',
    order: 3000
  },
  'meters': {
    name: 'Meters',
    description: 'Electricity meter management - add, update, delete meters',
    order: 4000
  },
  'bills': {
    name: 'Bills',
    description: 'Bill retrieval and breakdown endpoints',
    order: 5000
  },
  'payments': {
    name: 'Payments',
    description: 'Payment preparation, confirmation, and receipt endpoints',
    order: 6000
  },
  'prepaid': {
    name: 'Prepaid Tokens',
    description: 'Prepaid electricity token purchase and management',
    order: 7000
  },
  'utility-providers': {
    name: 'Utility Providers',
    description: 'List available utility providers by country and state',
    order: 8000
  },
  'subsidies': {
    name: 'Subsidies',
    description: 'Subsidy eligibility and administration endpoints',
    order: 9000
  },
  'exchange-rates': {
    name: 'Exchange Rates',
    description: 'Currency exchange rate endpoints',
    order: 10000
  }
};

// Request definitions
const requests = [
  // Health endpoints
  {
    folder: 'health',
    filename: 'health check.request.yaml',
    content: `$kind: http-request
method: GET
url: '{{base_url}}/health'
description: Basic health check endpoint
order: 1000
auth:
  type: noauth
`
  },
  {
    folder: 'health',
    filename: 'readiness check.request.yaml',
    content: `$kind: http-request
method: GET
url: '{{base_url}}/health/ready'
description: Kubernetes readiness probe - checks if app can serve traffic
order: 2000
auth:
  type: noauth
`
  },
  {
    folder: 'health',
    filename: 'liveness check.request.yaml',
    content: `$kind: http-request
method: GET
url: '{{base_url}}/health/live'
description: Kubernetes liveness probe - checks if app is running
order: 3000
auth:
  type: noauth
`
  },

  // Auth endpoints
  {
    folder: 'auth',
    filename: 'register.request.yaml',
    content: `$kind: http-request
method: POST
url: '{{base_url}}/auth/register'
description: |-
  Register a new user account.
  
  Password requirements:
  - Minimum 8 characters
  - At least one uppercase letter
  - At least one number
  
  Supported country codes: ES, US, IN, BR, NG
order: 1000
headers:
  - key: Content-Type
    value: application/json
body:
  type: json
  content: |-
    {
      "first_name": "John",
      "last_name": "Doe",
      "email": "john.doe@example.com",
      "password": "SecurePass123",
      "country_code": "NG",
      "hedera_account_id": "0.0.12345"
    }
auth:
  type: noauth
`
  },
  {
    folder: 'auth',
    filename: 'login.request.yaml',
    content: `$kind: http-request
method: POST
url: '{{base_url}}/auth/login'
description: Login with email and password to obtain JWT token
order: 2000
headers:
  - key: Content-Type
    value: application/json
body:
  type: json
  content: |-
    {
      "email": "john.doe@example.com",
      "password": "SecurePass123"
    }
auth:
  type: noauth
`
  },
  {
    folder: 'auth',
    filename: 'wallet connect.request.yaml',
    content: `$kind: http-request
method: POST
url: '{{base_url}}/auth/wallet-connect'
description: |-
  Connect using Hedera wallet (HashPack).
  Requires wallet signature verification.
order: 3000
headers:
  - key: Content-Type
    value: application/json
body:
  type: json
  content: |-
    {
      "hedera_account_id": "0.0.12345",
      "signature": "your-wallet-signature",
      "message": "Sign this message to authenticate"
    }
auth:
  type: noauth
`
  },

  // User endpoints
  {
    folder: 'user',
    filename: 'get profile.request.yaml',
    content: `$kind: http-request
method: GET
url: '{{base_url}}/user/profile'
description: Get current user profile information
order: 1000
`
  },
  {
    folder: 'user',
    filename: 'update profile.request.yaml',
    content: `$kind: http-request
method: PUT
url: '{{base_url}}/user/profile'
description: Update user profile information
order: 2000
headers:
  - key: Content-Type
    value: application/json
body:
  type: json
  content: |-
    {
      "first_name": "John",
      "last_name": "Doe"
    }
`
  },
  {
    folder: 'user',
    filename: 'get preferences.request.yaml',
    content: `$kind: http-request
method: GET
url: '{{base_url}}/user/preferences'
description: Get user preferences (notifications, display settings)
order: 3000
`
  },
  {
    folder: 'user',
    filename: 'update preferences.request.yaml',
    content: `$kind: http-request
method: PUT
url: '{{base_url}}/user/preferences'
description: Update user preferences
order: 4000
headers:
  - key: Content-Type
    value: application/json
body:
  type: json
  content: |-
    {
      "email_notifications": true,
      "push_notifications": true,
      "language": "en"
    }
`
  },
  {
    folder: 'user',
    filename: 'get notifications.request.yaml',
    content: `$kind: http-request
method: GET
url: '{{base_url}}/user/notifications'
description: Get user notifications
order: 5000
queryParams:
  - key: unread_only
    value: 'false'
    description: Filter to show only unread notifications
  - key: limit
    value: '20'
    description: Maximum number of notifications to return
`
  },
  {
    folder: 'user',
    filename: 'get security settings.request.yaml',
    content: `$kind: http-request
method: GET
url: '{{base_url}}/user/security'
description: Get user security settings (2FA status, sessions)
order: 6000
`
  },

  // Meters endpoints
  {
    folder: 'meters',
    filename: 'list meters.request.yaml',
    content: `$kind: http-request
method: GET
url: '{{base_url}}/meters'
description: List all meters for the current user
order: 1000
`
  },
  {
    folder: 'meters',
    filename: 'create meter.request.yaml',
    content: `$kind: http-request
method: POST
url: '{{base_url}}/meters'
description: |-
  Add a new electricity meter.
  
  Meter types: prepaid, postpaid
  Band classification (Nigeria only): A, B, C, D, E
order: 2000
headers:
  - key: Content-Type
    value: application/json
body:
  type: json
  content: |-
    {
      "meter_id": "12345678901",
      "utility_provider_id": "provider-uuid",
      "state_province": "Lagos",
      "utility_provider": "Ikeja Electric",
      "meter_type": "prepaid",
      "band_classification": "B",
      "address": "123 Main Street, Lagos",
      "is_primary": true
    }
`
  },
  {
    folder: 'meters',
    filename: 'get meter.request.yaml',
    content: `$kind: http-request
method: GET
url: '{{base_url}}/meters/:meter_id'
description: Get details of a specific meter
order: 3000
pathVariables:
  - key: meter_id
    value: 'meter-uuid-here'
    description: The meter UUID
`
  },
  {
    folder: 'meters',
    filename: 'update meter.request.yaml',
    content: `$kind: http-request
method: PUT
url: '{{base_url}}/meters/:meter_id'
description: Update meter information
order: 4000
pathVariables:
  - key: meter_id
    value: 'meter-uuid-here'
    description: The meter UUID
headers:
  - key: Content-Type
    value: application/json
body:
  type: json
  content: |-
    {
      "address": "456 New Address, Lagos",
      "is_primary": true
    }
`
  },
  {
    folder: 'meters',
    filename: 'delete meter.request.yaml',
    content: `$kind: http-request
method: DELETE
url: '{{base_url}}/meters/:meter_id'
description: Delete a meter from user account
order: 5000
pathVariables:
  - key: meter_id
    value: 'meter-uuid-here'
    description: The meter UUID
`
  },

  // Bills endpoints
  {
    folder: 'bills',
    filename: 'list bills.request.yaml',
    content: `$kind: http-request
method: GET
url: '{{base_url}}/bills'
description: List all bills for the current user
order: 1000
queryParams:
  - key: meter_id
    value: ''
    description: Filter by meter ID (optional)
    disabled: true
  - key: status
    value: ''
    description: 'Filter by status: pending, paid, overdue (optional)'
    disabled: true
  - key: limit
    value: '20'
    description: Maximum number of bills to return
`
  },
  {
    folder: 'bills',
    filename: 'get bill.request.yaml',
    content: `$kind: http-request
method: GET
url: '{{base_url}}/bills/:bill_id'
description: Get details of a specific bill
order: 2000
pathVariables:
  - key: bill_id
    value: 'bill-uuid-here'
    description: The bill UUID
`
  },
  {
    folder: 'bills',
    filename: 'get bill breakdown.request.yaml',
    content: `$kind: http-request
method: GET
url: '{{base_url}}/bills/:bill_id/breakdown'
description: Get detailed breakdown of bill charges (energy, taxes, fees)
order: 3000
pathVariables:
  - key: bill_id
    value: 'bill-uuid-here'
    description: The bill UUID
`
  },

  // Payments endpoints
  {
    folder: 'payments',
    filename: 'prepare payment.request.yaml',
    content: `$kind: http-request
method: POST
url: '{{base_url}}/payments/prepare'
description: |-
  Prepare a payment for a bill.
  
  Payment methods:
  - hbar: Pay with HBAR on Hedera
  - usdc_hedera: Pay with USDC on Hedera
  - usdc_ethereum: Pay with USDC on Ethereum
  
  Returns transaction details for wallet signing.
order: 1000
headers:
  - key: Content-Type
    value: application/json
body:
  type: json
  content: |-
    {
      "bill_id": "bill-uuid-here",
      "payment_method": "hbar"
    }
`
  },
  {
    folder: 'payments',
    filename: 'confirm payment.request.yaml',
    content: `$kind: http-request
method: POST
url: '{{base_url}}/payments/confirm'
description: |-
  Confirm a payment after wallet transaction is signed.
  
  Hedera transaction ID format: 0.0.{account}@{seconds}.{nanos}
order: 2000
headers:
  - key: Content-Type
    value: application/json
body:
  type: json
  content: |-
    {
      "bill_id": "bill-uuid-here",
      "hedera_tx_id": "0.0.12345@1234567890.123456789"
    }
`
  },
  {
    folder: 'payments',
    filename: 'get receipt.request.yaml',
    content: `$kind: http-request
method: GET
url: '{{base_url}}/payments/:payment_id/receipt'
description: Get payment receipt with PDF download URL
order: 3000
pathVariables:
  - key: payment_id
    value: 'payment-uuid-here'
    description: The payment UUID
`
  },

  // Prepaid endpoints
  {
    folder: 'prepaid',
    filename: 'buy prepaid token.request.yaml',
    content: `$kind: http-request
method: POST
url: '{{base_url}}/prepaid/buy'
description: Purchase prepaid electricity token
order: 1000
headers:
  - key: Content-Type
    value: application/json
body:
  type: json
  content: |-
    {
      "meter_id": "meter-uuid-here",
      "amount_fiat": 5000,
      "payment_method": "hbar"
    }
`
  },
  {
    folder: 'prepaid',
    filename: 'get prepaid balance.request.yaml',
    content: `$kind: http-request
method: GET
url: '{{base_url}}/prepaid/balance'
description: Get prepaid token balance for all meters
order: 2000
queryParams:
  - key: meter_id
    value: ''
    description: Filter by specific meter (optional)
    disabled: true
`
  },
  {
    folder: 'prepaid',
    filename: 'get token details.request.yaml',
    content: `$kind: http-request
method: GET
url: '{{base_url}}/prepaid/tokens/:token_id'
description: Get details of a specific prepaid token purchase
order: 3000
pathVariables:
  - key: token_id
    value: 'token-uuid-here'
    description: The prepaid token UUID
`
  },

  // Utility Providers endpoints
  {
    folder: 'utility-providers',
    filename: 'list providers.request.yaml',
    content: `$kind: http-request
method: GET
url: '{{base_url}}/utility-providers'
description: List all utility providers, optionally filtered by country
order: 1000
queryParams:
  - key: country_code
    value: 'NG'
    description: 'Filter by country code: ES, US, IN, BR, NG'
auth:
  type: noauth
`
  },
  {
    folder: 'utility-providers',
    filename: 'list states.request.yaml',
    content: `$kind: http-request
method: GET
url: '{{base_url}}/utility-providers/states'
description: List available states/provinces for a country
order: 2000
queryParams:
  - key: country_code
    value: 'NG'
    description: 'Country code: ES, US, IN, BR, NG'
auth:
  type: noauth
`
  },

  // Subsidies endpoints
  {
    folder: 'subsidies',
    filename: 'check eligibility.request.yaml',
    content: `$kind: http-request
method: GET
url: '{{base_url}}/users/me/subsidy-eligibility'
description: Check current user subsidy eligibility status
order: 1000
`
  },
  {
    folder: 'subsidies',
    filename: 'admin - list subsidies.request.yaml',
    content: `$kind: http-request
method: GET
url: '{{base_url}}/admin/subsidies'
description: '[Admin] List all subsidy applications'
order: 2000
queryParams:
  - key: status
    value: ''
    description: 'Filter by status: pending, approved, rejected'
    disabled: true
`
  },
  {
    folder: 'subsidies',
    filename: 'admin - approve subsidy.request.yaml',
    content: `$kind: http-request
method: POST
url: '{{base_url}}/admin/subsidies/:subsidy_id/approve'
description: '[Admin] Approve a subsidy application'
order: 3000
pathVariables:
  - key: subsidy_id
    value: 'subsidy-uuid-here'
    description: The subsidy application UUID
`
  },

  // Exchange Rates endpoints
  {
    folder: 'exchange-rates',
    filename: 'get exchange rate.request.yaml',
    content: `$kind: http-request
method: GET
url: '{{base_url}}/exchange-rate/:currency'
description: |-
  Get current HBAR exchange rate for a currency.
  
  Supported currencies: NGN, USD, EUR, INR, BRL
order: 1000
pathVariables:
  - key: currency
    value: 'NGN'
    description: 'Currency code: NGN, USD, EUR, INR, BRL'
auth:
  type: noauth
`
  }
];

// Main execution
function main() {
  const collectionDir = path.join(COLLECTIONS_DIR, COLLECTION_NAME);
  const resourcesDir = path.join(collectionDir, '.resources');

  console.log('Creating Hedera Flow API collection...\n');

  // Create collection directory
  ensureDir(collectionDir);
  ensureDir(resourcesDir);

  // Write collection definition
  fs.writeFileSync(path.join(resourcesDir, 'definition.yaml'), collectionDefinition);
  console.log('✓ Created collection definition');

  // Create folders and their definitions
  for (const [folderName, folderDef] of Object.entries(folders)) {
    const folderDir = path.join(collectionDir, folderDef.name);
    const folderResourcesDir = path.join(folderDir, '.resources');
    
    ensureDir(folderDir);
    ensureDir(folderResourcesDir);

    const folderDefinition = `$kind: collection
name: ${folderDef.name}
description: ${folderDef.description}
order: ${folderDef.order}
`;
    fs.writeFileSync(path.join(folderResourcesDir, 'definition.yaml'), folderDefinition);
    console.log(`✓ Created folder: ${folderDef.name}`);
  }

  // Create requests
  for (const request of requests) {
    const folderDef = folders[request.folder];
    const requestPath = path.join(collectionDir, folderDef.name, request.filename);
    fs.writeFileSync(requestPath, request.content);
    console.log(`  ✓ ${request.filename}`);
  }

  console.log('\n✅ Collection created successfully!');
  console.log(`   Location: postman/collections/${COLLECTION_NAME}/`);
  console.log(`   Total requests: ${requests.length}`);
  console.log(`   Total folders: ${Object.keys(folders).length}`);
}

main();
