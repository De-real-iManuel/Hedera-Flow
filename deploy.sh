#!/bin/bash

# Deployment script for Hedera Flow

echo "🚀 Starting deployment process..."

# Check if environment is specified
if [ -z "$1" ]; then
    echo "Usage: ./deploy.sh [railway|vercel|docker]"
    exit 1
fi

PLATFORM=$1

case $PLATFORM in
    "railway")
        echo "📡 Deploying to Railway..."
        railway login
        railway up
        ;;
    "vercel")
        echo "▲ Deploying frontend to Vercel..."
        npm run build
        vercel --prod
        ;;
    "docker")
        echo "🐳 Building and running with Docker..."
        docker-compose up --build -d
        echo "Application running at http://localhost:8000"
        ;;
    *)
        echo "❌ Unknown platform: $PLATFORM"
        echo "Available platforms: railway, vercel, docker"
        exit 1
        ;;
esac

echo "✅ Deployment completed!"