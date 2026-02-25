# Meter Registration Form - Quick Start Guide

## 🚀 Setup Instructions

### 1. Run Database Migration
```bash
cd backend
alembic upgrade head
```

### 2. Seed Utility Providers
```bash
python scripts/seed_utility_providers.py
```

Expected output:
```
Seeding 80+ utility providers...
[OK] ES - Madrid: i-DE (Iberdrola)
[OK] ES - Madrid: UFD (Naturgy)
...
✓ Successfully seeded 80 utility providers!
```

### 3. Start Backend
```bash
uvicorn main:app --reload
```

### 4. Start Frontend
```bash
cd ..
npm run dev
```

---

## 📍 Accessing the Form

### Option 1: Direct URL
Navigate to: `http://localhost:5173/register-meter`

### Option 2: Add Navigation Button
Add to HomePage.tsx or ProfilePage.tsx:
```typescript
<button onClick={() => navigate('/register-meter')}>
  Register Meter
</button>
```

---

## 🧪 Testing the Form

### Test Case 1: Spain User
1. Login as user with country_code = 'ES'
2. Navigate to /register-meter
3. State dropdown should show: Madrid, Valencia, Catalonia, etc.
4. Select "Madrid"
5. Provider dropdown should show: i-DE (Iberdrola), UFD (Naturgy), E-Redes (EDP)
6. Fill meter ID: ESP-12345678
7. Select meter type: Postpaid
8. Submit
9. Should see success message

### Test Case 2: Nigeria User
1. Login as user with country_code = 'NG'
2. Navigate to /register-meter
3. State dropdown should show: Lagos, FCT, Kano, etc.
4. Select "Lagos"
5. Provider dropdown should show: Ikeja Electric (IKEDP), Eko Electricity (EKEDP)
6. Fill meter ID: NG-LAG-12345678
7. Select meter type: Postpaid
8. **Band Classification dropdown appears** (Nigeria-specific)
9. Select band: C
10. Submit
11. Should see success message

### Test Case 3: USA User
1. Login as user with country_code = 'US'
2. Navigate to /register-meter
3. State dropdown should show: California, Texas, New York, Florida, Illinois
4. Select "California"
5. Provider dropdown should show: PG&E, SCE, SDG&E
6. Fill meter ID: US-CA-12345678
7. Select meter type: Postpaid
8. Submit
9. Should see success message

---

## 🔍 API Testing

### List States for Spain
```bash
curl http://localhost:8000/api/utility-providers/states?country_code=ES
```

Expected response:
```json
["Andalusia", "Asturias", "Basque Country", "Cantabria", "Catalonia", "Galicia", "Madrid", "Valencia"]
```

### List Providers for Madrid
```bash
curl http://localhost:8000/api/utility-providers?country_code=ES&state_province=Madrid
```

Expected response:
```json
[
  {
    "id": "uuid-1",
    "country_code": "ES",
    "state_province": "Madrid",
    "provider_name": "i-DE (Iberdrola)",
    "provider_code": "IDE_IBERDROLA",
    "service_areas": ["Madrid City", "Alcalá de Henares", "Getafe"],
    "is_active": true
  },
  ...
]
```

### List Providers for Lagos, Nigeria
```bash
curl http://localhost:8000/api/utility-providers?country_code=NG&state_province=Lagos
```

Expected response:
```json
[
  {
    "id": "uuid-2",
    "country_code": "NG",
    "state_province": "Lagos",
    "provider_name": "Ikeja Electric (IKEDP)",
    "provider_code": "IKEDP",
    "service_areas": ["Ikeja", "Agege", "Mushin", "Oshodi"],
    "is_active": true
  },
  {
    "id": "uuid-3",
    "country_code": "NG",
    "state_province": "Lagos",
    "provider_name": "Eko Electricity (EKEDP)",
    "provider_code": "EKEDP",
    "service_areas": ["Lagos Island", "Victoria Island", "Lekki", "Ikoyi"],
    "is_active": true
  }
]
```

---

## 🐛 Troubleshooting

### Issue: State dropdown is empty
**Solution**: 
1. Check if utility providers are seeded: `SELECT COUNT(*) FROM utility_providers;`
2. Re-run seeding script: `python scripts/seed_utility_providers.py`

### Issue: Provider dropdown doesn't load after selecting state
**Solution**:
1. Check browser console for API errors
2. Verify backend is running on port 8000
3. Check CORS configuration in backend

### Issue: Form submission fails
**Solution**:
1. Check if user is authenticated
2. Verify meter ID format is valid
3. Check backend logs for error details
4. Ensure utility_provider_id is valid UUID

### Issue: Band classification not showing for Nigeria
**Solution**:
1. Verify user's country_code is 'NG'
2. Check useAuth hook returns correct user data
3. Verify form component checks `user?.country_code === 'NG'`

---

## 📊 Database Verification

### Check Utility Providers
```sql
-- Count providers by country
SELECT country_code, COUNT(*) 
FROM utility_providers 
GROUP BY country_code;

-- List providers for Madrid
SELECT provider_name, provider_code 
FROM utility_providers 
WHERE country_code = 'ES' AND state_province = 'Madrid';
```

### Check Registered Meters
```sql
-- List all meters with provider info
SELECT 
  m.meter_id,
  m.state_province,
  m.utility_provider,
  up.provider_name,
  m.meter_type,
  m.band_classification
FROM meters m
LEFT JOIN utility_providers up ON m.utility_provider_id = up.id;
```

---

## 🎯 Expected Behavior

### Cascading Dropdowns
1. **Initial State**: State dropdown enabled, Provider dropdown disabled
2. **After State Selection**: Provider dropdown enables and loads providers
3. **After Provider Selection**: Submit button enables

### Loading States
- State dropdown shows "Loading..." while fetching states
- Provider dropdown shows "Loading..." while fetching providers
- Submit button shows "Registering..." during submission

### Success Flow
1. Form submits successfully
2. Success message displays for 2 seconds
3. User redirected to home page
4. Meter appears in meters list

### Error Handling
- Invalid meter ID: Shows validation error
- Network error: Shows error alert
- Duplicate meter: Shows error from backend
- Missing required fields: Submit button disabled

---

## 📝 Form Fields Reference

| Field | Required | Type | Notes |
|-------|----------|------|-------|
| Meter ID | Yes | Text | Format validated per region |
| State/Province | Yes | Dropdown | Filtered by user's country |
| Utility Provider | Yes | Dropdown | Filtered by selected state |
| Meter Type | Yes | Select | Prepaid or Postpaid |
| Band Classification | Nigeria only | Select | A, B, C, D, or E |
| Address | No | Text | Optional installation address |

---

## 🌍 Supported Regions

| Country | States | Providers | Special Fields |
|---------|--------|-----------|----------------|
| Spain (ES) | 11 | 11 | None |
| Nigeria (NG) | 11 | 11 | Band Classification |
| USA (US) | 5 | 11 | None |
| India (IN) | 5 | 11 | None |
| Brazil (BR) | 10 | 10 | None |

---

## ✅ Success Checklist

- [ ] Migration applied successfully
- [ ] Utility providers seeded (80+ records)
- [ ] Backend running on port 8000
- [ ] Frontend running on port 5173
- [ ] Can access /register-meter page
- [ ] State dropdown loads correctly
- [ ] Provider dropdown loads after state selection
- [ ] Form submits successfully
- [ ] Success message displays
- [ ] Meter appears in database
- [ ] Meter appears in meters list

---

**Ready to use!** 🎉
