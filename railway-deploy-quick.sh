#!/bin/bash

echo "🚂 Quick Railway Deployment for Hedera Flow"
echo "==========================================="

# Check if Railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo "❌ Railway CLI not found. Installing..."
    npm install -g @railway/cli
fi

echo "🔐 Logging in to Railway..."
railway login

echo "📦 Creating Railway project..."
cd backend
railway init

echo "🗄️ Adding database..."
railway add postgresql
railway add redis

echo "⚙️ Setting environment variables..."
railway variables set ENVIRONMENT=production
railway variables set DEBUG=false
railway variables set HEDERA_NETWORK=testnet
railway variables set JWT_SECRET_KEY=hackathon_jwt_secret_2024
railway variables set CORS_ORIGINS=http://localhost:5173,https://*.vercel.app

echo "🚀 Deploying..."
railway up

echo "✅ Deployment complete!"
echo "🔗 Your backend will be available at the Railway-provided URL"
echo "📝 Don't forget to set your Hedera credentials in Railway dashboard"