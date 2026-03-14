# Hedera Flow Backend

FastAPI backend for the Hedera Flow utility management platform.

## 🚀 Quick Start

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Edit .env with your configuration

# Run migrations
alembic upgrade head

# Start development server
uvicorn app.core.app:app --reload --host 0.0.0.0 --port 8000
```

### Production Deployment
```bash
# Using Railway
railway up

# Using Docker
docker build -t hedera-flow-backend .
docker run -p 8000:8000 hedera-flow-backend
```

## 📚 API Documentation

Once running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## 🔧 Configuration

Required environment variables:
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `HEDERA_ACCOUNT_ID`: Your Hedera account ID
- `HEDERA_PRIVATE_KEY`: Your Hedera private key
- `GOOGLE_CLOUD_CREDENTIALS`: Path to Google Cloud credentials JSON
- `JWT_SECRET`: Secret for JWT token signing

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test file
pytest tests/test_auth.py
```