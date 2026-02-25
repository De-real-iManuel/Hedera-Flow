# Hedera Flow - Blockchain-Powered Utility Verification Platform

A decentralized AI platform for electricity bill verification and payment using Hedera Hashgraph.

## 🚀 Quick Start

### Prerequisites
- Node.js 18+
- Python 3.9+
- PostgreSQL
- Redis

### Start Backend
```bash
cd backend
venv\Scripts\activate  # Windows: venv\Scripts\activate
python run.py
```
Backend runs on: http://localhost:8000

### Start Frontend
```bash
npm install
npm run dev
```
Frontend runs on: http://localhost:8080

### Test API Connection
Visit: http://localhost:8000/api-test

## 📁 Project Structure

```
hedera-flow/
├── backend/                    # FastAPI backend
│   ├── app/
│   │   ├── api/               # API endpoints
│   │   ├── core/              # Core functionality
│   │   ├── models/            # Database models
│   │   ├── schemas/           # Pydantic schemas
│   │   └── services/          # Business logic
│   ├── migrations/            # Database migrations
│   └── tests/                 # Backend tests
│
├── src/                       # Frontend source (Vite + React)
│   ├── components/            # React components
│   │   └── ui/               # shadcn-ui components
│   ├── pages/                # Page components
│   ├── hooks/                # Custom React hooks
│   ├── lib/                  # Utilities & API client
│   └── types/                # TypeScript types
│
├── public/                    # Static assets
├── .env                       # Frontend environment variables
└── backend/.env              # Backend environment variables
```

## 🛠️ Tech Stack

### Frontend
- **Framework**: React 18 + Vite
- **UI Library**: shadcn-ui (Radix UI + Tailwind CSS)
- **Routing**: React Router v6
- **State Management**: TanStack Query
- **Animations**: Framer Motion
- **HTTP Client**: Axios
- **Language**: TypeScript

### Backend
- **Framework**: FastAPI
- **Database**: PostgreSQL (Supabase)
- **Cache**: Redis (Upstash)
- **Authentication**: JWT
- **Blockchain**: Hedera Hashgraph
- **ORM**: SQLAlchemy
- **Language**: Python 3.9+

## 🔌 API Integration

### API Client
The frontend uses Axios with automatic JWT token injection:
```typescript
import { authApi, metersApi, billsApi } from '@/lib/api';

// Login
const response = await authApi.login({ email, password });

// Fetch bills
const bills = await billsApi.list();
```

### React Hooks
TanStack Query hooks for data fetching:
```typescript
import { useAuth, useBills, useMeters } from '@/hooks';

const { user, login, logout } = useAuth();
const { data: bills, isLoading } = useBills();
const { meters, createMeter } = useMeters();
```

## 📚 Documentation

- **[Quick Start Guide](QUICK_START.md)** - Get up and running
- **[Backend-Frontend Sync](BACKEND_FRONTEND_SYNC.md)** - API integration details
- **[Frontend Migration](FRONTEND_MIGRATION_COMPLETE.md)** - Migration from Next.js to Vite
- **[Sync Summary](SYNC_COMPLETE_SUMMARY.md)** - Current status and next steps

## 🎯 Features

### Implemented ✅
- User authentication (register, login)
- Meter registration
- JWT-based API authentication
- CORS configuration
- Health check endpoint
- Modern UI with shadcn-ui components

### In Progress ⏳
- Bill management endpoints
- Payment processing with Hedera
- OCR meter scanning
- Payment history
- Bill breakdown and tariff calculation

### Planned 📋
- Dispute management
- Multi-currency support
- Email notifications
- Mobile app (React Native)
- Admin dashboard

## 🔐 Environment Variables

### Frontend (.env)
```env
VITE_API_BASE_URL=http://localhost:8000
VITE_API_TIMEOUT=30000
VITE_HEDERA_NETWORK=testnet
```

### Backend (backend/.env)
```env
DATABASE_URL=postgresql://...
REDIS_URL=rediss://...
JWT_SECRET_KEY=your-secret-key
HEDERA_OPERATOR_ID=0.0.xxxxx
HEDERA_OPERATOR_KEY=302e...
CORS_ORIGINS=http://localhost:5173
```

## 🧪 Testing

### Backend Tests
```bash
cd backend
python -m pytest
python -m pytest -v  # Verbose
```

### Frontend Tests
```bash
npm run test
npm run test:watch
```

### API Test Page
Visit http://localhost:5173/api-test to test backend connectivity.

## 📱 Pages

- **/** - Home page with current bill and usage
- **/scan** - Meter scanning with OCR
- **/bills** - Bill details and payment
- **/history** - Payment history
- **/profile** - User profile and settings
- **/api-test** - API connection test (development only)

## 🔄 API Endpoints

### Implemented
- `POST /auth/register` - User registration
- `POST /auth/login` - User login
- `GET /auth/me` - Get current user
- `POST /meters` - Create meter
- `GET /health` - Health check

### To Be Implemented
- `GET /meters` - List meters
- `GET /bills` - List bills
- `POST /payments/prepare` - Prepare payment
- `POST /payments/confirm` - Confirm payment
- `POST /verify/scan` - OCR scanning

See [BACKEND_FRONTEND_SYNC.md](BACKEND_FRONTEND_SYNC.md) for complete API documentation.

## 🚢 Deployment

### Frontend
```bash
npm run build
# Deploy dist/ folder to Vercel, Netlify, etc.
```

### Backend
```bash
# Set production environment variables
python run_migration.py
uvicorn app.core.app:app --host 0.0.0.0 --port 8000 --workers 4
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests
5. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details

## 🆘 Support

- **Documentation**: See docs in project root
- **API Docs**: http://localhost:8000/docs (when running)
- **Issues**: Check backend logs in `backend/backend.log`

## 🎨 UI Components

Built with shadcn-ui, includes:
- Buttons, Cards, Dialogs
- Forms, Inputs, Selects
- Toasts, Tooltips, Modals
- Navigation, Tabs, Accordions
- And 40+ more components

## 🔗 Links

- **Hedera**: https://hedera.com
- **FastAPI**: https://fastapi.tiangolo.com
- **React**: https://react.dev
- **shadcn-ui**: https://ui.shadcn.com
- **TanStack Query**: https://tanstack.com/query

## 📊 Status

- **Backend**: ✅ Running (partial implementation)
- **Frontend**: ✅ Running (mock data)
- **API Integration**: ✅ Configured
- **Authentication**: ⏳ Backend ready, frontend pages needed
- **Payments**: ⏳ To be implemented
- **OCR**: ⏳ To be implemented

---

**Built by De real iManuel using Hedera Hashgraph**
