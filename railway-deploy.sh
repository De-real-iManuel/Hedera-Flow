#!/bin/bash

# Railway CLI Deployment Script for Hedera Flow Backend
echo "🚀 Starting Railway deployment for Hedera Flow Backend..."

# Check if Railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo "❌ Railway CLI not found. Installing..."
    npm install -g @railway/cli
fi

# Login to Railway (will open browser for authentication)
echo "🔐 Logging into Railway..."
railway login

# Create new project
echo "📦 Creating Railway project..."
railway init

# Set environment variables
echo "⚙️ Setting environment variables..."
railway variables set HEDERA_NETWORK=testnet
railway variables set HEDERA_OPERATOR_ID=0.0.7942957
railway variables set JWT_ALGORITHM=HS256
railway variables set JWT_EXPIRATION_DAYS=30
railway variables set JWT_REFRESH_EXPIRATION_DAYS=90
railway variables set ENVIRONMENT=production
railway variables set PYTHONPATH=/app

# Add PostgreSQL database
echo "🗄️ Adding PostgreSQL database..."
railway add postgresql

# Add Redis database
echo "🔴 Adding Redis database..."
railway add redis

# Deploy the application
echo "🚀 Deploying application..."
cd backend
railway up

echo "✅ Deployment initiated! Check Railway dashboard for status."
echo "🌐 Your app will be available at the URL shown in Railway dashboard."