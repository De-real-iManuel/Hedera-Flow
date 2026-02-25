# Hedera Flow - Quick Start Guide

## Prerequisites
- Node.js 18+ and npm
- Python 3.9+
- PostgreSQL (or use Docker)
- Redis (or use Upstash)

## 1. Backend Setup

### Start Backend Server
```bash
cd backend

# Activate virtual environment (if not already activated)
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# Install dependencies (if not already installed)
pip install -r requirements.txt

# Run migrations (if needed)
python run_migration.py

# Start the server
python run.py
```

Backend will run on: **http://localhost:8000**

API Documentation: **http://localhost:8000/docs**

## 2. Frontend Setup

### Install Dependencies & Start Dev Server
```bash
# From project root
npm install

# Start Vite dev server
npm run dev
```

Frontend will run on: **http://localhost:5173**

## 3. Verify Connection

### Test Backend Health
Open browser: http://localhost:8000/health

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "2026-01-15T10:30:00Z"
}
```

### Test Frontend
Open browser: http://localhost:5173

You should see the Hedera Flow splash screen and home page.

## 4. Test API Integration

### Open Browser Console
1. Go to http://localhost:5173
2. Open Developer Tools (F12)
3. Go to Network tab
4. Refresh the page
5. Look for API calls to `localhost:8000`

### Check CORS
If you see CORS errors:
1. Verify backend is running
2. Check `backend/.env` has: `CORS_ORIGINS=http://localhost:5173`
3. Restart backend server

## 5. Available Scripts

### Frontend
```bash
npm run dev          # Start dev server
npm run build        # Build for production
npm run preview      # Preview production build
npm run lint         # Run ESLint
npm run test         # Run tests
```

### Backend
```bash
python run.py                    # Start server
python run_migration.py          # Run migrations
python -m pytest                 # Run tests
python -m pytest -v              # Run tests (verbose)
```

## 6. Project Structure

```
/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── api/            # API endpoints
│   │   ├── core/           # Core functionality
│   │   ├── models/         # Database models
│   │   ├── schemas/        # Pydantic schemas
│   │   └── services/       # Business logic
│   ├── migrations/         # Database migrations
│   └── tests/              # Backend tests
│
├── src/                    # Frontend source
│   ├── components/         # React components
│   ├── pages/              # Page components
│   ├── hooks/              # Custom hooks
│   ├── lib/                # Utilities & API client
│   └── types/              # TypeScript types
│
├── public/                 # Static assets
└── .env                    # Frontend environment variables
```

## 7. Environment Variables

### Frontend (.env)
```env
VITE_API_BASE_URL=http://localhost:8000
VITE_API_TIMEOUT=30000
VITE_HEDERA_NETWORK=testnet
```

### Backend (backend/.env)
Key variables:
- `DATABASE_URL` - PostgreSQL connection string
- `REDIS_URL` - Redis connection string
- `JWT_SECRET_KEY` - JWT signing key
- `HEDERA_OPERATOR_ID` - Hedera account ID
- `HEDERA_OPERATOR_KEY` - Hedera private key
- `CORS_ORIGINS` - Allowed frontend origins

## 8. Common Issues

### Backend won't start
- Check if PostgreSQL is running
- Verify `DATABASE_URL` in `backend/.env`
- Check if port 8000 is available

### Frontend can't connect to backend
- Verify backend is running on port 8000
- Check `VITE_API_BASE_URL` in `.env`
- Check browser console for CORS errors

### CORS errors
- Ensure `CORS_ORIGINS` in `backend/.env` includes `http://localhost:5173`
- Restart backend after changing CORS settings

### Database connection errors
- Verify PostgreSQL is running
- Check database credentials in `backend/.env`
- Try running migrations: `python run_migration.py`

## 9. Next Steps

### For Development
1. Create login/register pages
2. Update pages to use real API data
3. Implement authentication flow
4. Add error handling and loading states

### Backend Tasks
- Implement remaining endpoints (bills, payments, verification)
- Add more meter endpoints (list, get, update, delete)
- Implement OCR scanning
- Add payment processing

### Frontend Tasks
- Create auth pages (login/register)
- Connect HomePage to real data
- Connect BillsPage to real data
- Connect HistoryPage to real data
- Implement meter scanning with OCR

## 10. Documentation

- **API Docs**: http://localhost:8000/docs (when backend is running)
- **Backend-Frontend Sync**: See `BACKEND_FRONTEND_SYNC.md`
- **Frontend Migration**: See `FRONTEND_MIGRATION_COMPLETE.md`
- **Spec Tasks**: See `.kiro/specs/hedera-flow-mvp/tasks.md`

## 11. Support

If you encounter issues:
1. Check the console/terminal for error messages
2. Review the documentation files
3. Check the backend logs in `backend/backend.log`
4. Verify all environment variables are set correctly

## 12. Production Deployment

### Frontend
```bash
npm run build
# Deploy dist/ folder to Vercel, Netlify, etc.
```

### Backend
```bash
# Set production environment variables
# Run migrations
python run_migration.py

# Start with production server
uvicorn app.core.app:app --host 0.0.0.0 --port 8000 --workers 4
```

Remember to:
- Use HTTPS in production
- Set secure JWT secret
- Configure production database
- Update CORS origins to production domain
- Enable rate limiting
- Set up monitoring and logging
