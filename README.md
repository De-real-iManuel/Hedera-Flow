<div align="center">

<img src="public/logo.png" alt="Hedera Flow Logo" width="200"/>

# Hedera Flow

### Blockchain-Powered Smart Utility Management Platform

[![Hedera](https://img.shields.io/badge/Hedera-Hashgraph-00D4AA?style=for-the-badge&logo=hedera&logoColor=white)](https://hedera.com)
[![React](https://img.shields.io/badge/React-18-61DAFB?style=for-the-badge&logo=react&logoColor=black)](https://react.dev)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0-3178C6?style=for-the-badge&logo=typescript&logoColor=white)](https://www.typescriptlang.org)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](LICENSE)

**A decentralized platform for prepaid electricity management, smart meter integration, and transparent utility payments using Hedera Hashgraph blockchain technology.**

[Features](#-features) • [Quick Start](#-quick-start) • [Documentation](#-documentation) • [Tech Stack](#-tech-stack) • [Contributing](#-contributing)

</div>

---

## 🌟 Overview

Hedera Flow revolutionizes utility management by combining blockchain transparency with smart meter technology. Built on Hedera Hashgraph, it provides:

- 🔐 **Secure Payments** - HBAR/USDC payments with MetaMask integration
- 📊 **Real-time Monitoring** - Smart meter data with consumption tracking
- 💰 **Prepaid Tokens** - Buy electricity tokens with cryptocurrency
- 🌍 **Multi-region Support** - Regional HCS topics for compliance
- 📱 **Mobile-first Design** - Progressive Web App with offline support
- 🔍 **Transparent Auditing** - Immutable blockchain records

## ✨ Features

### Implemented ✅

#### Authentication & User Management
- ✅ Email/password registration and login
- ✅ MetaMask wallet connection (EVM address support)
- ✅ JWT-based authentication
- ✅ User profile management
- ✅ Session management

#### Meter Management
- ✅ Meter registration (prepaid/postpaid)
- ✅ Band classification (A-E for Nigeria)
- ✅ Meter validation and verification
- ✅ Multiple meters per user
- ✅ Primary meter selection

#### Prepaid Token System
- ✅ Token purchase with HBAR
- ✅ Real-time exchange rate calculation
- ✅ kWh units calculation based on tariff
- ✅ Token ID generation (TOKEN-{COUNTRY}-{YEAR}-{SEQ})
- ✅ FIFO token deduction
- ✅ Low balance alerts (< 10 kWh)
- ✅ Token expiry management (1 year)

#### Payment Integration
- ✅ MetaMask wallet integration
- ✅ HBAR balance checking
- ✅ Transaction signing
- ✅ Payment confirmation
- ✅ Transaction verification
- ✅ HCS logging for audit trail

#### Smart Meter Integration
- ✅ End-to-end encryption (AES-256-GCM)
- ✅ Digital signatures (Ed25519)
- ✅ Consumption logging
- ✅ Tamper detection
- ✅ Offline operation support

#### Blockchain Integration
- ✅ Hedera Consensus Service (HCS) logging
- ✅ Regional HCS topics (EU, US, Asia, SA, Africa)
- ✅ Immutable audit trail
- ✅ Transaction verification
- ✅ HashScan integration

### In Progress ⏳

- ⏳ USDC payment support
- ⏳ Bill generation and management
- ⏳ Dispute resolution system
- ⏳ OCR meter scanning
- ⏳ Email notifications
- ⏳ Push notifications

### Planned 📋

- 📋 Mobile app (React Native)
- 📋 Admin dashboard
- 📋 Analytics and reporting
- 📋 Multi-currency support
- 📋 Subsidy management
- 📋 Fraud detection AI

## 🚀 Quick Start

### Prerequisites

- **Node.js** 18+ ([Download](https://nodejs.org))
- **Python** 3.9+ ([Download](https://python.org))
- **PostgreSQL** ([Download](https://postgresql.org))
- **Redis** ([Download](https://redis.io))
- **MetaMask** browser extension ([Install](https://metamask.io))

### Installation

#### 1. Clone Repository
```bash
git clone https://github.com/yourusername/hedera-flow.git
cd hedera-flow
```

#### 2. Backend Setup
```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration

# Run database migrations
alembic upgrade head

# Start backend server
python run.py
```

Backend runs on: **http://localhost:8000**

API Documentation: **http://localhost:8000/docs**

#### 3. Frontend Setup
```bash
# From project root
npm install

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration

# Start development server
npm run dev
```

Frontend runs on: **http://localhost:8080**

### Quick Test

1. **Test Backend**: Visit http://localhost:8000/health
2. **Test Frontend**: Visit http://localhost:8080
3. **Test API**: Visit http://localhost:8080/api-test

## 📁 Project Structure

```
hedera-flow/
├── backend/                           # FastAPI backend
│   ├── app/
│   │   ├── api/
│   │   │   ├── endpoints/            # API route handlers
│   │   │   │   ├── auth.py          # Authentication
│   │   │   │   ├── meters.py        # Meter management
│   │   │   │   ├── prepaid.py       # Prepaid tokens
│   │   │   │   ├── bills.py         # Bill management
│   │   │   │   └── payments.py      # Payment processing
│   │   │   └── routes.py            # Route registration
│   │   ├── core/
│   │   │   ├── app.py               # FastAPI app instance
│   │   │   ├── database.py          # Database connection
│   │   │   ├── dependencies.py      # Dependency injection
│   │   │   └── middleware.py        # CORS, logging, etc.
│   │   ├── models/                   # SQLAlchemy models
│   │   │   ├── user.py
│   │   │   ├── meter.py
│   │   │   ├── prepaid_token.py
│   │   │   └── bill.py
│   │   ├── schemas/                  # Pydantic schemas
│   │   │   ├── auth.py
│   │   │   ├── meters.py
│   │   │   └── payments.py
│   │   ├── services/                 # Business logic
│   │   │   ├── prepaid_token_service.py
│   │   │   ├── hedera_service.py
│   │   │   ├── smart_meter_service.py
│   │   │   └── exchange_rate_service.py
│   │   └── utils/                    # Utilities
│   │       ├── auth.py
│   │       ├── hedera_client.py
│   │       └── redis_client.py
│   ├── migrations/                   # Alembic migrations
│   ├── tests/                        # Backend tests
│   └── config.py                     # Configuration
│
├── src/                              # Frontend source
│   ├── components/                   # React components
│   │   ├── ui/                      # shadcn-ui components
│   │   ├── WalletConnect.tsx        # Wallet connection
│   │   ├── PrepaidTokenPurchase.tsx # Token purchase
│   │   └── MeterRegistrationForm.tsx
│   ├── pages/                        # Page components
│   │   ├── HomePage.tsx
│   │   ├── PrepaidPage.tsx
│   │   ├── ProfilePage.tsx
│   │   └── AuthPage.tsx
│   ├── hooks/                        # Custom React hooks
│   │   ├── useAuth.ts
│   │   ├── useMetaMaskHedera.ts
│   │   ├── useMeters.ts
│   │   └── usePrepaid.ts
│   ├── lib/                          # Utilities
│   │   ├── api/                     # API client
│   │   │   ├── prepaid.ts
│   │   │   └── index.ts
│   │   └── api-client.ts            # Axios instance
│   └── types/                        # TypeScript types
│       └── api.ts
│
├── public/                           # Static assets
├── docs/                             # Documentation
├── scripts/                          # Utility scripts
└── .github/                          # GitHub workflows
```

## 🛠️ Tech Stack

### Frontend

| Technology | Purpose | Version |
|-----------|---------|---------|
| **React** | UI Framework | 18.2 |
| **TypeScript** | Type Safety | 5.0 |
| **Vite** | Build Tool | 5.0 |
| **TailwindCSS** | Styling | 3.4 |
| **shadcn-ui** | UI Components | Latest |
| **TanStack Query** | Data Fetching | 5.0 |
| **React Router** | Routing | 6.21 |
| **Framer Motion** | Animations | 11.0 |
| **Axios** | HTTP Client | 1.6 |
| **Sonner** | Notifications | 1.3 |

### Backend

| Technology | Purpose | Version |
|-----------|---------|---------|
| **FastAPI** | Web Framework | 0.109 |
| **Python** | Language | 3.9+ |
| **PostgreSQL** | Database | 15+ |
| **Redis** | Cache | 7+ |
| **SQLAlchemy** | ORM | 2.0 |
| **Alembic** | Migrations | 1.13 |
| **Pydantic** | Validation | 2.5 |
| **JWT** | Authentication | - |

### Blockchain

| Technology | Purpose |
|-----------|---------|
| **Hedera Hashgraph** | Blockchain Platform |
| **HCS** | Consensus Service |
| **HBAR** | Native Cryptocurrency |
| **MetaMask** | Wallet Integration |

## 🔌 API Documentation

### Authentication

#### Register User
```http
POST /api/auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "SecurePass123!",
  "first_name": "John",
  "last_name": "Doe",
  "country_code": "NG"
}
```

#### Login
```http
POST /api/auth/login
Content-Type: application/x-www-form-urlencoded

username=user@example.com&password=SecurePass123!
```

#### Wallet Connect
```http
POST /api/auth/wallet-connect
Content-Type: application/json

{
  "hedera_account_id": "0x1234...abcd",
  "signature": "0xabcd...1234",
  "message": "Hedera Flow Authentication..."
}
```

### Prepaid Tokens

#### Preview Token Purchase
```http
POST /api/prepaid/preview
Content-Type: application/json

{
  "meter_id": "uuid",
  "amount_fiat": 50.00,
  "currency": "NGN",
  "payment_method": "HBAR"
}
```

#### Buy Token
```http
POST /api/prepaid/buy
Content-Type: application/json

{
  "meter_id": "uuid",
  "amount_fiat": 50.00,
  "currency": "NGN",
  "payment_method": "HBAR"
}
```

#### Confirm Payment
```http
POST /api/prepaid/confirm
Content-Type: application/json

{
  "meter_id": "uuid",
  "hedera_tx_id": "0.0.123456@1234567890.123"
}
```

### Meters

#### Register Meter
```http
POST /api/meters
Content-Type: application/json

{
  "meter_id": "ESP-12345678",
  "meter_type": "prepaid",
  "utility_provider": "Port Harcourt Electricity Distribution",
  "band_classification": "A"
}
```

See full API documentation at: **http://localhost:8000/docs**

## 🔐 Environment Variables

### Frontend (.env)
```env
# API Configuration
VITE_API_BASE_URL=http://localhost:8000
VITE_API_TIMEOUT=30000

# Hedera Configuration
VITE_HEDERA_NETWORK=testnet
VITE_HEDERA_TREASURY_ACCOUNT=0.0.123456

# WalletConnect (if using)
VITE_WALLETCONNECT_PROJECT_ID=your-project-id
```

### Backend (backend/.env)
```env
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/hedera_flow

# Redis Cache
REDIS_URL=redis://localhost:6379

# JWT Authentication
JWT_SECRET_KEY=your-super-secret-key-change-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=1440

# Hedera Configuration
HEDERA_NETWORK=testnet
HEDERA_OPERATOR_ID=0.0.xxxxx
HEDERA_OPERATOR_KEY=302e...

# HCS Topics (Regional)
HCS_TOPIC_EU=0.0.8052384
HCS_TOPIC_US=0.0.8052396
HCS_TOPIC_ASIA=0.0.8052389
HCS_TOPIC_SA=0.0.8052390
HCS_TOPIC_AFRICA=0.0.8052391

# CORS
CORS_ORIGINS=http://localhost:5173,http://localhost:8080

# Exchange Rate API
EXCHANGE_RATE_API_KEY=your-api-key
```

## 🧪 Testing

### Backend Tests
```bash
cd backend

# Run all tests
python -m pytest

# Run with coverage
python -m pytest --cov=app --cov-report=html

# Run specific test file
python -m pytest tests/test_prepaid_token.py

# Run with verbose output
python -m pytest -v
```

### Frontend Tests
```bash
# Run all tests
npm run test

# Run in watch mode
npm run test:watch

# Run with coverage
npm run test:coverage

# Run specific test
npm run test PrepaidTokenPurchase
```

### Integration Tests
```bash
# Test API connectivity
curl http://localhost:8000/health

# Test authentication
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=test@example.com&password=test123"
```

## 🌐 Live HCS Topics

View real-time blockchain logs on HashScan:

| Region | Topic ID | HashScan Link |
|--------|----------|---------------|
| 🇪🇺 Europe | 0.0.8052384 | [View](https://hashscan.io/testnet/topic/0.0.8052384) |
| 🇺🇸 United States | 0.0.8052396 | [View](https://hashscan.io/testnet/topic/0.0.8052396) |
| 🌏 Asia | 0.0.8052389 | [View](https://hashscan.io/testnet/topic/0.0.8052389) |
| 🌎 South America | 0.0.8052390 | [View](https://hashscan.io/testnet/topic/0.0.8052390) |
| 🌍 Africa | 0.0.8052391 | [View](https://hashscan.io/testnet/topic/0.0.8052391) |

All token purchases, payments, and consumption logs are recorded immutably on these regional HCS topics.

## 📚 Documentation

- **[Quick Start Guide](QUICK_START.md)** - Get up and running quickly
- **[MetaMask Integration](METAMASK_INTEGRATION.md)** - Wallet connection guide
- **[MetaMask Payment Integration](METAMASK_PAYMENT_INTEGRATION.md)** - Payment flow details
- **[Wallet Integration Status](WALLET_INTEGRATION_STATUS.md)** - Current implementation status
- **[API Integration Guide](BACKEND_FRONTEND_SYNC.md)** - Frontend-backend sync
- **[Database Schema](backend/DATABASE.md)** - Database structure
- **[Smart Meter Integration](backend/SMART_METER_INTEGRATION.md)** - IoT device integration

## 🚢 Deployment

### Frontend (Vercel/Netlify)

```bash
# Build for production
npm run build

# Preview production build
npm run preview

# Deploy to Vercel
vercel deploy --prod

# Deploy to Netlify
netlify deploy --prod --dir=dist
```

### Backend (Docker)

```bash
# Build Docker image
docker build -t hedera-flow-backend ./backend

# Run container
docker run -p 8000:8000 \
  -e DATABASE_URL=$DATABASE_URL \
  -e REDIS_URL=$REDIS_URL \
  hedera-flow-backend

# Or use docker-compose
docker-compose up -d
```

### Database Migrations

```bash
cd backend

# Create new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

## 🤝 Contributing

We welcome contributions! Please follow these steps:

1. **Fork the repository**
2. **Create a feature branch**
   ```bash
   git checkout -b feature/amazing-feature
   ```
3. **Make your changes**
4. **Run tests**
   ```bash
   npm run test
   cd backend && python -m pytest
   ```
5. **Commit your changes**
   ```bash
   git commit -m "Add amazing feature"
   ```
6. **Push to branch**
   ```bash
   git push origin feature/amazing-feature
   ```
7. **Open a Pull Request**

### Code Style

- **Frontend**: ESLint + Prettier
- **Backend**: Black + isort + flake8
- **Commits**: Conventional Commits

### Development Guidelines

- Write tests for new features
- Update documentation
- Follow existing code patterns
- Keep PRs focused and small
- Add comments for complex logic

## 📊 Project Status

| Component | Status | Coverage |
|-----------|--------|----------|
| Backend API | ✅ Stable | 75% |
| Frontend UI | ✅ Stable | 60% |
| Authentication | ✅ Complete | 85% |
| Prepaid Tokens | ✅ Complete | 80% |
| Smart Meters | ✅ Complete | 70% |
| Payments | ✅ Complete | 75% |
| HCS Logging | ✅ Complete | 90% |
| Mobile App | ⏳ Planned | - |

## 🐛 Known Issues

- [ ] USDC payment not yet implemented
- [ ] OCR scanning needs improvement
- [ ] Email notifications pending
- [ ] Mobile app in development

See [Issues](https://github.com/yourusername/hedera-flow/issues) for full list.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Hedera Hashgraph** - For the amazing blockchain platform
- **FastAPI** - For the excellent Python web framework
- **shadcn-ui** - For the beautiful UI components
- **Vercel** - For hosting and deployment
- **Supabase** - For PostgreSQL database
- **Upstash** - For Redis cache

## 📞 Support

- **Documentation**: Check the `/docs` folder
- **Issues**: [GitHub Issues](https://github.com/yourusername/hedera-flow/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/hedera-flow/discussions)
- **Email**: support@hederaflow.com

## 🔗 Links

- **Website**: https://hederaflow.com
- **Documentation**: https://docs.hederaflow.com
- **API Docs**: https://api.hederaflow.com/docs
- **Hedera**: https://hedera.com
- **HashScan**: https://hashscan.io

## 🌟 Star History

[![Star History Chart](https://api.star-history.com/svg?repos=yourusername/hedera-flow&type=Date)](https://star-history.com/#yourusername/hedera-flow&Date)

---

<div align="center">

**Built by De real iManuel using Hedera Hashgraph**

[⬆ Back to Top](#-hedera-flow)

</div>
