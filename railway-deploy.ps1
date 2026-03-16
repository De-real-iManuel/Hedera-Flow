# Railway CLI Deployment Script for Hedera Flow Backend (PowerShell)
Write-Host "🚀 Starting Railway deployment for Hedera Flow Backend..." -ForegroundColor Green

# Check if Railway CLI is installed
if (!(Get-Command railway -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Railway CLI not found. Installing..." -ForegroundColor Yellow
    npm install -g @railway/cli
}

# Login to Railway (will open browser for authentication)
Write-Host "🔐 Logging into Railway..." -ForegroundColor Blue
railway login

# Create new project
Write-Host "📦 Creating Railway project..." -ForegroundColor Blue
railway init

# Set environment variables
Write-Host "⚙️ Setting environment variables..." -ForegroundColor Blue
railway variables set HEDERA_NETWORK=testnet
railway variables set HEDERA_OPERATOR_ID=0.0.7942957
railway variables set JWT_ALGORITHM=HS256
railway variables set JWT_EXPIRATION_DAYS=30
railway variables set JWT_REFRESH_EXPIRATION_DAYS=90
railway variables set ENVIRONMENT=production
railway variables set PYTHONPATH=/app

# Add PostgreSQL database
Write-Host "🗄️ Adding PostgreSQL database..." -ForegroundColor Blue
railway add postgresql

# Add Redis database
Write-Host "🔴 Adding Redis database..." -ForegroundColor Blue
railway add redis

# Deploy the application
Write-Host "🚀 Deploying application..." -ForegroundColor Green
Set-Location backend
railway up

Write-Host "✅ Deployment initiated! Check Railway dashboard for status." -ForegroundColor Green
Write-Host "🌐 Your app will be available at the URL shown in Railway dashboard." -ForegroundColor Cyan