#!/bin/bash

# Create a minimal backend deployment package

echo "🧹 Creating minimal backend deployment..."

# Create temporary deployment directory
mkdir -p deploy-temp/backend

# Copy only essential backend files
cp -r backend/app deploy-temp/backend/
cp backend/requirements.txt deploy-temp/backend/
cp backend/alembic.ini deploy-temp/backend/
cp -r backend/migrations deploy-temp/backend/ 2>/dev/null || echo "No migrations folder"

# Copy environment template
cp backend/.env.example deploy-temp/backend/.env.example 2>/dev/null || echo "No .env.example"

# Create railway config in temp directory
cat > deploy-temp/backend/railway.toml << EOF
[build]
builder = "nixpacks"

[deploy]
startCommand = "uvicorn app.core.app:app --host 0.0.0.0 --port \$PORT"
healthcheckPath = "/health"

[env]
PORT = "8000"
EOF

echo "📦 Deployment package created in deploy-temp/"
echo "📁 Size: $(du -sh deploy-temp/ | cut -f1)"
echo ""
echo "Next steps:"
echo "1. cd deploy-temp/backend"
echo "2. railway up"