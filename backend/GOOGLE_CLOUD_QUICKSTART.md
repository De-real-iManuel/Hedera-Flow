# Google Cloud Vision API - Quick Start

**Task 11.1**: Set up Google Cloud project  
**Time**: 10-15 minutes

---

## TL;DR - Quick Setup

```bash
# 1. Create Google Cloud project
Visit: https://console.cloud.google.com
Create project: "hedera-flow-mvp"

# 2. Enable Vision API
APIs & Services → Library → Search "Vision API" → Enable

# 3. Create Service Account
IAM & Admin → Service Accounts → Create
Name: "hedera-flow-ocr-service"
Role: "Cloud Vision API User"
Create JSON key → Download

# 4. Move credentials
mkdir backend/credentials
move Downloads/hedera-flow-*.json backend/credentials/google-vision-key.json

# 5. Update .env
GOOGLE_APPLICATION_CREDENTIALS=credentials/google-vision-key.json
GOOGLE_CLOUD_PROJECT_ID=hedera-flow-mvp-123456

# 6. Install dependencies
cd backend
pip install google-cloud-vision==3.4.5

# 7. Test setup
python test_google_vision.py
```

---

## Environment Variables

Add to `backend/.env`:

```bash
# Google Cloud Vision API
GOOGLE_APPLICATION_CREDENTIALS=credentials/google-vision-key.json
GOOGLE_CLOUD_PROJECT_ID=your-project-id-here
GOOGLE_VISION_API_ENDPOINT=https://vision.googleapis.com
```

---

## Test Command

```bash
cd backend
python test_google_vision.py
```

**Expected output:**
```
✅ TEST PASSED: Google Cloud Vision API is ready!
```

---

## Free Tier Limits

- **1,000 requests/month** free
- After: $1.50 per 1,000 requests
- MVP usage: ~250 requests (well within free tier)

---

## Troubleshooting

### "Credentials not found"
```bash
# Check file exists
dir backend\credentials\google-vision-key.json

# Check .env has correct path
GOOGLE_APPLICATION_CREDENTIALS=credentials/google-vision-key.json
```

### "Permission denied"
- Verify service account has "Cloud Vision API User" role
- Wait 1-2 minutes for permissions to propagate

### "Module not found"
```bash
pip install google-cloud-vision==3.4.5
```

---

## Security Checklist

- [ ] Credentials file in `backend/credentials/`
- [ ] Added `credentials/` to `.gitignore`
- [ ] Never commit JSON key to Git
- [ ] Set up billing alerts (optional)

---

## Next Tasks

- [x] 11.1 Set up Google Cloud project
- [x] 11.2 Enable Vision API
- [ ] 11.3 Implement OCRService class
- [ ] 11.4 Implement extract_reading method
- [ ] 11.5 Implement detect_meter_type method

---

## Full Documentation

See `GOOGLE_CLOUD_SETUP.md` for detailed step-by-step instructions.

---

**Status**: ✅ Ready for implementation  
**Last Updated**: February 23, 2026
