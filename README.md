# Hedera Flow - Utility Bill Management Platform

A comprehensive utility bill management platform built on Hedera Hashgraph, featuring smart meter integration, OCR bill scanning, and blockchain-based payments.

## 🚀 Features

- **Smart Meter Integration**: Real-time consumption tracking with cryptographic verification
- **OCR Bill Scanning**: Automated bill data extraction using Google Vision API
- **Blockchain Payments**: Secure USDC payments via Hedera network
- **Prepaid Token System**: STS-compliant token generation for prepaid meters
- **Multi-Utility Support**: Support for electricity, water, and gas utilities
- **Real-time Analytics**: Consumption patterns and billing insights

## 🏗️ Architecture

### Frontend (React + TypeScript)
- **Framework**: Vite + React 18
- **UI**: Tailwind CSS + Radix UI components
- **State Management**: Zustand
- **Blockchain**: Hedera SDK integration
- **Camera**: Native device camera for bill scanning

### Backend (Python FastAPI)
- **Framework**: FastAPI with async support
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Cache**: Redis for session management
- **OCR**: Google Cloud Vision API
- **Blockchain**: Hedera SDK for payments
- **Authentication**: JWT with bcrypt hashing

## 🛠️ Tech Stack

**Frontend:**
- React 18 + TypeScript
- Vite build system
- Tailwind CSS + Radix UI
- Hedera Wallet Connect
- Zustand state management

**Backend:**
- Python 3.11 + FastAPI
- PostgreSQL + SQLAlchemy
- Redis caching
- Google Cloud Vision
- Hedera SDK

**Infrastructure:**
- Docker containerization
- Railway/Vercel deployment
- IPFS for receipt storage

## 🚀 Quick Start

### Prerequisites
- Node.js 18+
- Python 3.11+
- PostgreSQL
- Redis
- Google Cloud Vision API key
- Hedera testnet account

### Environment Setup

1. **Clone the repository**
```bash
git clone <repository-url>
cd hedera-flow
```

2. **Frontend setup**
```bash
npm install
cp .env.example .env.local
# Configure your environment variables
npm run dev
```

3. **Backend setup**
```bash
cd backend
pip install -r requirements.txt
cp .env.example .env
# Configure your environment variables
uvicorn app.core.app:app --reload
```

### Environment Variables

**Frontend (.env.local):**
```
VITE_API_BASE_URL=http://localhost:8000
VITE_HEDERA_NETWORK=testnet
```

**Backend (.env):**
```
DATABASE_URL=postgresql://user:password@localhost/hedera_flow
REDIS_URL=redis://localhost:6379
HEDERA_ACCOUNT_ID=your_account_id
HEDERA_PRIVATE_KEY=your_private_key
GOOGLE_CLOUD_CREDENTIALS=path_to_credentials.json
JWT_SECRET=your_jwt_secret
```

## 📦 Deployment

### Vercel (Frontend)
```bash
npm run build
vercel --prod
```

### Railway (Backend)
```bash
cd backend
railway up
```

### Docker
```bash
docker-compose up --build
```

## 🔧 Development

### Running Tests
```bash
# Frontend
npm run test

# Backend
cd backend
pytest
```

### Code Quality
```bash
# Frontend linting
npm run lint

# Backend formatting
cd backend
black . && isort .
```

## 📱 Mobile Support

The application is fully responsive and supports:
- Progressive Web App (PWA) capabilities
- Native camera access for bill scanning
- Touch-optimized interface
- Offline functionality for core features

## 🔐 Security Features

- JWT-based authentication
- Rate limiting on all endpoints
- Input validation and sanitization
- Secure file upload handling
- Blockchain transaction verification
- Encrypted smart meter communications

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Create an issue on GitHub
- Check the documentation in `/docs`
- Review the API documentation at `/docs` endpoint

## 🎯 Roadmap

- [ ] Multi-language support
- [ ] Advanced analytics dashboard
- [ ] Mobile app (React Native)
- [ ] Integration with more utility providers
- [ ] AI-powered consumption predictions
- [ ] Carbon footprint tracking