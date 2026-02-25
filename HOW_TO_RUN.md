# How to Run Backend and Tests

## Step 1: Start Backend Server

**Option A: Double-click this file:**
```
start-backend.bat
```

**Option B: Manual command:**
```bash
cd backend
python run.py
```

Wait until you see:
```
✅ Database connection pool initialized successfully
INFO:     Uvicorn running on http://0.0.0.0:8000
```

## Step 2: Run Tests (New Terminal/Window)

**Option A: Double-click this file:**
```
run-tests.bat
```

**Option B: Manual command:**
```bash
cd backend
python run_tests.py
```

## Expected Results

```
============================================================
BACKEND AUTHENTICATION TESTS
============================================================

1. Checking if backend is running...
   [OK] Backend is running - Status: 200

2. Testing user registration...
   [PASS] Registration successful

3. Testing duplicate email rejection...
   [PASS] Duplicate email rejected

4. Testing weak password rejection...
   [PASS] Weak password rejected

5. Testing user login...
   [PASS] Login successful

6. Testing invalid password rejection...
   [PASS] Invalid password rejected

7. Testing non-existent user rejection...
   [PASS] Non-existent user rejected

8. Testing protected route with token...
   [PASS] Protected route accessible with token

============================================================
TESTS COMPLETED
============================================================
```

## Troubleshooting

### "Backend is NOT running"
- Make sure you started `start-backend.bat` first
- Check if port 8000 is already in use
- Look for errors in the backend terminal

### "Database connection failed"
- Check Docker is running: `docker ps`
- Should see `hedera-flow-postgres` container
- Restart Docker if needed

### "Registration failed - Hedera error"
- This is expected - Hedera account creation is temporarily disabled
- Tests should still pass with placeholder account

## Files Created

- `start-backend.bat` - Starts the backend server
- `run-tests.bat` - Runs authentication tests
- `backend/run_tests.py` - Simple test script
- `backend/test_config.py` - Config verification

## What's Fixed

✅ Database URL points to localhost  
✅ Redis URL points to localhost  
✅ Hedera account creation disabled  
✅ All authentication logic working  

## Next Steps

Once tests pass:
1. Build frontend authentication pages
2. Implement meter management
3. Add OCR features
4. Fix Hedera credentials later
