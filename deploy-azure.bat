@echo off
echo 🚀 Azure Deployment for Hedera Flow
echo ===================================

REM Check Azure CLI
az --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Azure CLI not found. Install with: winget install Microsoft.AzureCLI
    pause
    exit /b 1
)

echo 🔐 Logging in to Azure...
az login

REM Set variables
set RESOURCE_GROUP=hedera-flow-rg
set APP_NAME=hedera-flow-api-%RANDOM%
set LOCATION=East US

echo.
echo 📦 Deployment Configuration:
echo Resource Group: %RESOURCE_GROUP%
echo App Name: %APP_NAME%
echo Location: %LOCATION%
echo.

REM Get Hedera credentials
set /p HEDERA_ID="Enter your Hedera Account ID (0.0.xxxxx): "
set /p HEDERA_KEY="Enter your Hedera Private Key: "

echo.
echo 🔧 Creating Azure resources...

REM Create resource group
az group create --name %RESOURCE_GROUP% --location "%LOCATION%"

REM Create App Service plan
az appservice plan create --name %APP_NAME%-plan --resource-group %RESOURCE_GROUP% --sku F1 --is-linux

REM Create Web App
az webapp create --resource-group %RESOURCE_GROUP% --plan %APP_NAME%-plan --name %APP_NAME% --runtime "PYTHON|3.11"

REM Set environment variables
echo ⚙️ Setting environment variables...
az webapp config appsettings set --resource-group %RESOURCE_GROUP% --name %APP_NAME% --settings ^
  ENVIRONMENT=production ^
  DEBUG=false ^
  HEDERA_NETWORK=testnet ^
  HEDERA_OPERATOR_ID=%HEDERA_ID% ^
  HEDERA_OPERATOR_KEY=%HEDERA_KEY% ^
  JWT_SECRET_KEY=hackathon_jwt_secret_2024 ^
  DATABASE_URL=sqlite:///./hedera_flow.db ^
  REDIS_URL=redis://localhost:6379 ^
  CORS_ORIGINS=http://localhost:5173,https://*.vercel.app

REM Deploy code
echo 📤 Deploying backend code...
cd backend
powershell -Command "Compress-Archive -Path * -DestinationPath '../backend-deploy.zip' -Force"
cd ..
az webapp deployment source config-zip --resource-group %RESOURCE_GROUP% --name %APP_NAME% --src backend-deploy.zip

REM Get app URL
for /f %%i in ('az webapp show --resource-group %RESOURCE_GROUP% --name %APP_NAME% --query "defaultHostName" --output tsv') do set APP_URL=%%i

echo.
echo ✅ DEPLOYMENT COMPLETE!
echo ========================
echo 🔗 Backend API: https://%APP_URL%
echo 📚 API Docs: https://%APP_URL%/docs
echo 🔍 Health Check: https://%APP_URL%/health
echo.
echo 📝 Next Steps:
echo 1. Test your API: https://%APP_URL%/health
echo 2. Update your frontend VITE_API_BASE_URL to: https://%APP_URL%
echo 3. Deploy your frontend to Vercel with: npx vercel --prod
echo.
echo 🗑️ To delete resources after hackathon:
echo    az group delete --name %RESOURCE_GROUP% --yes --no-wait
echo.

REM Clean up
if exist backend-deploy.zip del backend-deploy.zip

pause