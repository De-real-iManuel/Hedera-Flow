@echo off
REM Hedera Flow - Hackathon Demo Startup Script (Windows)
REM This script starts both backend and frontend for demo purposes

echo ========================================
echo Starting Hedera Flow for Hackathon Demo
echo ========================================

REM Get local IP address
echo.
echo Detecting local IP address...
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /c:"IPv4 Address"') do (
    set LOCAL_IP=%%a
    goto :found_ip
)
:found_ip
set LOCAL_IP=%LOCAL_IP:~1%
echo Local IP: %LOCAL_IP%
echo Mobile Access: http://%LOCAL_IP%:5173
echo Desktop Access: http://localhost:5173

REM Check if backend .env exists
if not exist "backend\.env" (
    echo.
    echo backend\.env not found!
    echo Creating from backend\.env.example...
    copy backend\.env.example backend\.env
    echo Please edit backend\.env with your database credentials
    pause
    exit /b 1
)

REM Check if frontend .env exists
if not exist ".env" (
    echo.
    echo .env not found, creating from .env.example...
    copy .env.example .env
)

REM Start backend
echo.
echo Starting Backend Server...
cd backend

if not exist "venv" (
    echo Creating Python virtual environment...
    python -m venv venv
)

call venv\Scripts\activate.bat

echo Installing Python dependencies...
pip install -q -r requirements.txt

echo Backend starting on http://0.0.0.0:8000
start "Hedera Flow Backend" cmd /k "uvicorn app.core.app:app --reload --host 0.0.0.0 --port 8000"

cd ..

REM Wait for backend to start
echo Waiting for backend to be ready...
timeout /t 5 /nobreak > nul

REM Start frontend
echo.
echo Starting Frontend Server...

if not exist "node_modules" (
    echo Installing Node dependencies...
    call npm install
)

echo Frontend starting on http://0.0.0.0:5173
start "Hedera Flow Frontend" cmd /k "npm run dev -- --host"

REM Display access information
echo.
echo ========================================
echo Hedera Flow is running!
echo ========================================
echo.
echo Access URLs:
echo   Desktop:  http://localhost:5173
echo   Mobile:   http://%LOCAL_IP%:5173
echo   API Docs: http://localhost:8000/docs
echo.
echo Press any key to stop all servers...
pause > nul

REM Cleanup
taskkill /FI "WindowTitle eq Hedera Flow Backend*" /F
taskkill /FI "WindowTitle eq Hedera Flow Frontend*" /F
