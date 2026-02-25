# IPFS Service Quick Start Guide

## Setup

### 1. Get Pinata API Credentials

1. Sign up at [Pinata.cloud](https://pinata.cloud)
2. Go to API Keys section
3. Create new API key with permissions:
   - `pinFileToIPFS`
   - `pinByHash`
4. Copy API Key and Secret Key

### 2. Configure Environment

Add to your `.env` file:

```bash
IPFS_API_URL=https://api.pinata.cloud
PINATA_API_KEY=your_api_key_here
PINATA_SECRET_KEY=your_secret_key_here
```

## Usage

### Upload Single Image

```python
from app.services.ipfs_service import get_ipfs_service

# Get service
ipfs = get_ipfs_service()

# Upload image
with open('meter_photo.jpg', 'rb') as f:
    image_bytes = f.read()

result = ipfs.upload_image(image_bytes, 'meter_photo.jpg')

print(f"IPFS Hash: {result['ipfs_hash']}")
print(f"Gateway URL: {result['gateway_url']}")
```

### Upload Multiple Images

```python
images = [
    (image1_bytes, 'photo1.jpg'),
    (image2_bytes, 'photo2.jpg'),
    (image3_bytes, 'photo3.jpg')
]

results = ipfs.upload_multiple_images(images)

for result in results:
    if 'error' in result:
        print(f"Failed: {result['filename']} - {result['error']}")
    else:
        print(f"Success: {result['ipfs_hash']}")
```

### Get Image URL

```python
# HTTP gateway URL (for browsers)
url = ipfs.get_image_url('QmHash123', use_gateway=True)
# Returns: https://gateway.pinata.cloud/ipfs/QmHash123

# IPFS protocol URL (for IPFS clients)
url = ipfs.get_image_url('QmHash123', use_gateway=False)
# Returns: ipfs://QmHash123
```

### Pin Existing Hash

```python
result = ipfs.pin_by_hash('QmExistingHash123')
print(f"Pinned: {result['status']}")
```

## Integration with Verification

The IPFS service is automatically used in the verification endpoint:

```python
# In verify.py
ipfs_service = get_ipfs_service()

ipfs_result = ipfs_service.upload_image(
    image_bytes=image_bytes,
    filename=f"meter_{meter_id}_{timestamp}.jpg"
)

image_ipfs_hash = ipfs_result['ipfs_url']  # ipfs://QmHash...
```

## Accessing Images

### Via HTTP Gateway

```bash
# Pinata gateway (fastest)
https://gateway.pinata.cloud/ipfs/QmHash123

# Public IPFS gateways
https://ipfs.io/ipfs/QmHash123
https://cloudflare-ipfs.com/ipfs/QmHash123
https://gateway.ipfs.io/ipfs/QmHash123
```

### Via IPFS Desktop/CLI

```bash
# Install IPFS Desktop or CLI
ipfs get QmHash123

# Or open in browser
ipfs://QmHash123
```

## Error Handling

```python
try:
    result = ipfs.upload_image(image_bytes, 'photo.jpg')
    print(f"Uploaded: {result['ipfs_hash']}")
except Exception as e:
    if "not configured" in str(e):
        print("Pinata credentials missing")
    elif "401" in str(e):
        print("Invalid credentials")
    elif "Network error" in str(e):
        print("Connection failed")
    else:
        print(f"Upload failed: {e}")
```

## Testing

### Run Unit Tests

```bash
cd backend
python -m pytest tests/test_ipfs_service.py -v
```

### Manual Test

```python
# test_ipfs_manual.py
from app.services.ipfs_service import get_ipfs_service

ipfs = get_ipfs_service()

# Create test image
test_image = b'\xff\xd8\xff\xe0' + b'\x00' * 1000

try:
    result = ipfs.upload_image(test_image, 'test.jpg')
    print(f"✓ Upload successful!")
    print(f"  Hash: {result['ipfs_hash']}")
    print(f"  URL: {result['gateway_url']}")
except Exception as e:
    print(f"✗ Upload failed: {e}")
```

## Best Practices

1. **Filename Convention**: Use descriptive, timestamped filenames
   ```python
   filename = f"meter_{meter_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
   ```

2. **Error Handling**: Always wrap uploads in try-except
   ```python
   try:
       result = ipfs.upload_image(...)
   except Exception as e:
       logger.error(f"IPFS upload failed: {e}")
       # Use fallback or retry
   ```

3. **Image Optimization**: Compress images before upload
   ```python
   from PIL import Image
   import io
   
   img = Image.open(io.BytesIO(image_bytes))
   img = img.resize((1024, 768))
   
   buffer = io.BytesIO()
   img.save(buffer, format='JPEG', quality=85)
   optimized_bytes = buffer.getvalue()
   ```

4. **Metadata**: Add meaningful metadata
   ```python
   # Service automatically adds:
   # - app: hedera-flow
   # - type: meter_image
   # - name: filename
   ```

## Troubleshooting

### "Pinata API credentials not configured"
- Check `.env` file has `PINATA_API_KEY` and `PINATA_SECRET_KEY`
- Restart server after adding credentials

### "401 Unauthorized"
- Verify API key is correct
- Check key hasn't expired
- Ensure key has `pinFileToIPFS` permission

### "Network error"
- Check internet connection
- Verify Pinata API is accessible
- Check firewall settings

### "No IPFS hash returned"
- Check Pinata API response format
- Verify API version compatibility
- Contact Pinata support

## Limits & Pricing

### Free Tier (Pinata)
- 1 GB storage
- 100 GB bandwidth/month
- Unlimited pins

### Paid Tiers
- Picnic: $20/month (100 GB storage)
- Submarine: $100/month (1 TB storage)
- Custom: Enterprise pricing

## Resources

- [Pinata Documentation](https://docs.pinata.cloud/)
- [IPFS Documentation](https://docs.ipfs.tech/)
- [Hedera Flow IPFS Implementation](./TASK_13.6_IPFS_IMPLEMENTATION.md)

---

**Last Updated**: February 23, 2026  
**Version**: 1.0
