#!/bin/bash

# Hedera Flow - Hackathon Demo Startup Script
# This script starts both backend and frontend for demo purposes

echo "🚀 Starting Hedera Flow for Hackathon Demo"
echo "=========================================="

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Get local IP address
echo -e "\n${YELLOW}📡 Detecting local IP address...${NC}"
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    LOCAL_IP=$(ifconfig | grep "inet " | grep -v 127.0.0.1 | awk '{print $2}' | head -n 1)
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux
    LOCAL_IP=$(hostname -I | awk '{print $1}')
else
    # Windows (Git Bash)
    LOCAL_IP=$(ipconfig | grep "IPv4" | awk '{print $NF}' | head -n 1)
fi

echo -e "${GREEN}✅ Local IP: $LOCAL_IP${NC}"
echo -e "${YELLOW}📱 Mobile Access: http://$LOCAL_IP:5173${NC}"
echo -e "${YELLOW}💻 Desktop Access: http://localhost:5173${NC}"

# Check if backend .env exists
if [ ! -f "backend/.env" ]; then
    echo -e "\n${RED}❌ backend/.env not found!${NC}"
    echo -e "${YELLOW}Creating from backend/.env.example...${NC}"
    cp backend/.env.example backend/.env
    echo -e "${RED}⚠️  Please edit backend/.env with your database credentials${NC}"
    exit 1
fi

# Check if frontend .env exists
if [ ! -f ".env" ]; then
    echo -e "\n${YELLOW}⚠️  .env not found, creating from .env.example...${NC}"
    cp .env.example .env
fi

# Start backend
echo -e "\n${YELLOW}🔧 Starting Backend Server...${NC}"
cd backend
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Creating Python virtual environment...${NC}"
    python3 -m venv venv
fi

source venv/bin/activate 2>/dev/null || source venv/Scripts/activate 2>/dev/null

echo -e "${YELLOW}Installing Python dependencies...${NC}"
pip install -q -r requirements.txt

echo -e "${GREEN}✅ Backend starting on http://0.0.0.0:8000${NC}"
uvicorn app.core.app:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

cd ..

# Wait for backend to start
echo -e "${YELLOW}⏳ Waiting for backend to be ready...${NC}"
sleep 5

# Start frontend
echo -e "\n${YELLOW}🎨 Starting Frontend Server...${NC}"

if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}Installing Node dependencies...${NC}"
    npm install
fi

echo -e "${GREEN}✅ Frontend starting on http://0.0.0.0:5173${NC}"
npm run dev -- --host &
FRONTEND_PID=$!

# Display access information
echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}✅ Hedera Flow is running!${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "\n${YELLOW}Access URLs:${NC}"
echo -e "  Desktop:  ${GREEN}http://localhost:5173${NC}"
echo -e "  Mobile:   ${GREEN}http://$LOCAL_IP:5173${NC}"
echo -e "  API Docs: ${GREEN}http://localhost:8000/docs${NC}"
echo -e "\n${YELLOW}Backend PID: $BACKEND_PID${NC}"
echo -e "${YELLOW}Frontend PID: $FRONTEND_PID${NC}"
echo -e "\n${RED}Press Ctrl+C to stop all servers${NC}\n"

# Trap Ctrl+C and cleanup
trap "echo -e '\n${YELLOW}🛑 Stopping servers...${NC}'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT

# Wait for processes
wait
