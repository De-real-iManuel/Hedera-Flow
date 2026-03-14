#!/bin/bash

# Hedera Flow - Setup Verification Script
# Checks if all prerequisites are met for hackathon demo

echo "🔍 Hedera Flow - Setup Verification"
echo "===================================="

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

ERRORS=0

# Check Python
echo -e "\n${YELLOW}Checking Python...${NC}"
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo -e "${GREEN}✅ $PYTHON_VERSION${NC}"
else
    echo -e "${RED}❌ Python 3 not found${NC}"
    ERRORS=$((ERRORS + 1))
fi

# Check Node.js
echo -e "\n${YELLOW}Checking Node.js...${NC}"
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version)
    echo -e "${GREEN}✅ Node.js $NODE_VERSION${NC}"
else
    echo -e "${RED}❌ Node.js not found${NC}"
    ERRORS=$((ERRORS + 1))
fi

# Check npm
echo -e "\n${YELLOW}Checking npm...${NC}"
if command -v npm &> /dev/null; then
    NPM_VERSION=$(npm --version)
    echo -e "${GREEN}✅ npm $NPM_VERSION${NC}"
else
    echo -e "${RED}❌ npm not found${NC}"
    ERRORS=$((ERRORS + 1))
fi

# Check backend .env
echo -e "\n${YELLOW}Checking backend configuration...${NC}"
if [ -f "backend/.env" ]; then
    echo -e "${GREEN}✅ backend/.env exists${NC}"
    
    # Check critical variables
    if grep -q "DATABASE_URL=" backend/.env && ! grep -q "DATABASE_URL=$" backend/.env; then
        echo -e "${GREEN}✅ DATABASE_URL configured${NC}"
    else
        echo -e "${RED}❌ DATABASE_URL not configured${NC}"
        ERRORS=$((ERRORS + 1))
    fi
    
    if grep -q "JWT_SECRET_KEY=" backend/.env && ! grep -q "JWT_SECRET_KEY=$" backend/.env; then
        echo -e "${GREEN}✅ JWT_SECRET_KEY configured${NC}"
    else
        echo -e "${RED}❌ JWT_SECRET_KEY not configured${NC}"
        ERRORS=$((ERRORS + 1))
    fi
    
    if grep -q "HEDERA_OPERATOR_ID=" backend/.env && ! grep -q "HEDERA_OPERATOR_ID=$" backend/.env; then
        echo -e "${GREEN}✅ HEDERA_OPERATOR_ID configured${NC}"
    else
        echo -e "${YELLOW}⚠️  HEDERA_OPERATOR_ID not configured (optional for demo)${NC}"
    fi
else
    echo -e "${RED}❌ backend/.env not found${NC}"
    echo -e "${YELLOW}   Run: cp backend/.env.example backend/.env${NC}"
    ERRORS=$((ERRORS + 1))
fi

# Check frontend .env
echo -e "\n${YELLOW}Checking frontend configuration...${NC}"
if [ -f ".env" ]; then
    echo -e "${GREEN}✅ .env exists${NC}"
    
    if grep -q "VITE_WALLETCONNECT_PROJECT_ID=a410efc0d43c137138330074a67cdf07" .env; then
        echo -e "${GREEN}✅ WalletConnect Project ID configured${NC}"
    else
        echo -e "${YELLOW}⚠️  WalletConnect Project ID may need updating${NC}"
    fi
else
    echo -e "${RED}❌ .env not found${NC}"
    echo -e "${YELLOW}   Run: cp .env.example .env${NC}"
    ERRORS=$((ERRORS + 1))
fi

# Check Python dependencies
echo -e "\n${YELLOW}Checking Python dependencies...${NC}"
if [ -f "backend/requirements.txt" ]; then
    echo -e "${GREEN}✅ requirements.txt exists${NC}"
else
    echo -e "${RED}❌ requirements.txt not found${NC}"
    ERRORS=$((ERRORS + 1))
fi

# Check Node dependencies
echo -e "\n${YELLOW}Checking Node dependencies...${NC}"
if [ -f "package.json" ]; then
    echo -e "${GREEN}✅ package.json exists${NC}"
else
    echo -e "${RED}❌ package.json not found${NC}"
    ERRORS=$((ERRORS + 1))
fi

# Check if node_modules exists
if [ -d "node_modules" ]; then
    echo -e "${GREEN}✅ node_modules installed${NC}"
else
    echo -e "${YELLOW}⚠️  node_modules not found${NC}"
    echo -e "${YELLOW}   Run: npm install${NC}"
fi

# Check database connection (if backend is running)
echo -e "\n${YELLOW}Checking backend API...${NC}"
if curl -s http://localhost:8000/api/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Backend is running${NC}"
else
    echo -e "${YELLOW}⚠️  Backend not running (this is OK if you haven't started it yet)${NC}"
fi

# Summary
echo -e "\n===================================="
if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}✅ Setup verification passed!${NC}"
    echo -e "${GREEN}You're ready to start the demo.${NC}"
    echo -e "\n${YELLOW}To start:${NC}"
    echo -e "  ./start-hackathon-demo.sh"
else
    echo -e "${RED}❌ Found $ERRORS error(s)${NC}"
    echo -e "${YELLOW}Please fix the errors above before starting.${NC}"
fi
echo -e "====================================\n"

exit $ERRORS
