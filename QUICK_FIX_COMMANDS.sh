#!/bin/bash

# Quick Fix Commands for Wallet Connect Errors
# Run these commands to fix all issues

echo "🔧 Fixing Wallet Connect Errors..."
echo ""

# Step 1: Install buffer package
echo "📦 Step 1: Installing buffer package..."
npm install buffer

echo ""
echo "✅ Buffer package installed!"
echo ""

# Step 2: Instructions for restart
echo "🔄 Step 2: Restart development servers"
echo ""
echo "In Terminal 1 (Frontend):"
echo "  npm run dev"
echo ""
echo "In Terminal 2 (Backend):"
echo "  cd backend"
echo "  python -m uvicorn main:app --reload --port 8000"
echo ""

echo "✨ All fixes applied! Restart your servers to see the changes."
echo ""
echo "📖 For detailed information, see:"
echo "  - COMPLETE_FIX_GUIDE.md"
echo "  - WALLET_CONNECT_FIXES.md"
