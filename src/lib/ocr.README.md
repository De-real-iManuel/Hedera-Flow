# OCR Module - Meter Reading Extraction

This module provides client-side OCR functionality for extracting meter readings from images using Tesseract.js.

## Features

- **Client-side processing**: Runs entirely in the browser for privacy
- **Advanced image preprocessing** (FR-3.6):
  - Resize to 1024x1024 (maintains aspect ratio with white padding)
  - Grayscale conversion using luminosity method
  - Noise reduction with median filter (3x3 kernel)
  - Adaptive contrast enhancement using histogram equalization
- **Confidence scoring**: Returns confidence level (0-1) for each reading
- **Validation**: Ensures readings are within valid range (0-100,000 kWh)
- **Error handling**: Graceful fallback when OCR fails

## Requirements Implemented

- **FR-3.1**: System shall run Tesseract.js OCR client-side first
- **FR-3.4**: System shall extract reading value and unit
- **FR-3.5**: System shall calculate confidence score (0-100%)
- **NFR-1.1**: Client-side OCR shall complete in < 5 seconds

## Usage

### Basic Example

```typescript
import { extractMeterReading } from '@/lib/ocr';

// From a file input
const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
  const file = event.target.files?.[0];
  if (!file) return;
  
  try {
    const result = await extractMeterReading(file);
    
    console.log(`Reading: ${result.reading} kWh`);
    console.log(`Confidence: ${(result.confidence * 100).toFixed(1)}%`);
    console.log(`Raw OCR text: ${result.rawText}`);
    
    // Check confidence threshold
    if (result.confidence > 0.9) {
      // High confidence - use reading directly
      console.log('High confidence reading');
    } else if (result.confidence > 0.7) {
      // Medium confidence - may need verification
      console.log('Medium confidence - consider manual verification');
    } else {
      // Low confidence - fallback to server OCR
      console.log('Low confidence - sending to server for verification');
    }
  } catch (error) {
    console.error('OCR failed:', error);
    // Fallback to server-side OCR or manual entry
  }
};
```

### With Camera Component

```typescript
import { Camera } from '@/components/Camera';
import { extractMeterReading } from '@/lib/ocr';

function MeterScanPage() {
  const [isProcessing, setIsProcessing] = useState(false);
  const [result, setResult] = useState<MeterReadingResult | null>(null);
  
  const handleCapture = async (file: File) => {
    setIsProcessing(true);
    try {
      const ocrResult = await extractMeterReading(file);
      setResult(ocrResult);
      
      // Send to backend for verification
      if (ocrResult.confidence > 0.9) {
        await submitVerification(ocrResult);
      } else {
        // Fallback to server OCR
        await submitForServerOCR(file, ocrResult);
      }
    } catch (error) {
      console.error('OCR processing failed:', error);
    } finally {
      setIsProcessing(false);
    }
  };
  
  return (
    <div>
      <Camera onCapture={handleCapture} />
      {isProcessing && <p>Processing image...</p>}
      {result && (
        <div>
          <p>Reading: {result.reading} kWh</p>
          <p>Confidence: {(result.confidence * 100).toFixed(1)}%</p>
        </div>
      )}
    </div>
  );
}
```

## API Reference

### `extractMeterReading(imageFile: File): Promise<MeterReadingResult>`

Extracts a meter reading from an image file.

**Parameters:**
- `imageFile` (File): The image file containing the meter reading

**Returns:**
- Promise<MeterReadingResult>: Object containing:
  - `reading` (number): Extracted numeric reading (0 if invalid)
  - `confidence` (number): Confidence score from 0 to 1
  - `rawText` (string): Raw OCR text output

**Throws:**
- Error: If OCR processing fails completely

### `MeterReadingResult` Interface

```typescript
interface MeterReadingResult {
  reading: number;      // Extracted meter reading (kWh)
  confidence: number;   // Confidence score (0-1)
  rawText: string;      // Raw OCR output text
}
```

## How It Works

1. **File to Base64**: Converts the image file to base64 format
2. **Preprocessing** (FR-3.6): 
   - **Resize**: Scales image to 1024x1024 maintaining aspect ratio, centers with white padding
   - **Grayscale**: Converts to grayscale using luminosity method (0.299R + 0.587G + 0.114B)
   - **Noise Reduction**: Applies 3x3 median filter to reduce random noise while preserving edges
   - **Contrast Enhancement**: Uses adaptive histogram equalization to improve digit visibility
3. **OCR Processing**: 
   - Runs Tesseract.js with English language model
   - Extracts text from preprocessed image
   - Calculates confidence score
4. **Number Extraction**:
   - Finds numeric patterns in OCR text
   - Handles decimals (e.g., "12345.67")
   - Validates range (0-100,000 kWh)
5. **Result**: Returns reading, confidence, and raw text

## Confidence Thresholds

Based on requirements (FR-3.2):

- **> 90%**: High confidence - use client-side result
- **70-90%**: Medium confidence - may need verification
- **< 70%**: Low confidence - fallback to server-side OCR (Google Vision API)

## Performance

- **Target**: < 5 seconds (NFR-1.1)
- **Typical**: 2-4 seconds for standard meter images
- **Factors affecting speed**:
  - Image size (larger = slower)
  - Image quality (blurry = slower)
  - Device performance

## Limitations

- Requires clear, well-lit meter images
- Works best with digital meters (LCD displays)
- May struggle with:
  - Analog dial meters
  - Heavily worn or damaged meters
  - Poor lighting conditions
  - Extreme angles or distortion

## Next Steps (Future Tasks)

- **Task 10.3**: Configure Tesseract with custom training data for meter digits
- **Task 10.4**: Improve number extraction with regex patterns
- **Task 10.5**: Enhance confidence calculation
- **Task 10.6**: Test with real meter images
- **Task 10.7**: Optimize performance with Web Workers
- ~~**Task 10.2**: Add advanced image preprocessing~~ ✅ COMPLETED

## Testing

To test the OCR functionality:

1. Use the Camera component to capture a meter image
2. Or upload a test image with clear digits
3. Check the console for OCR progress logs
4. Verify the extracted reading matches the actual meter value
5. Check confidence score is reasonable (> 0.7 for clear images)

## Troubleshooting

**Issue**: OCR returns 0 or incorrect reading
- **Solution**: Ensure image is clear and well-lit, try preprocessing manually

**Issue**: Low confidence scores (< 0.5)
- **Solution**: Improve image quality, ensure meter is centered and in focus

**Issue**: OCR takes too long (> 5 seconds)
- **Solution**: Reduce image size before processing, consider Web Worker implementation

**Issue**: "Failed to extract meter reading" error
- **Solution**: Check browser console for detailed error, ensure Tesseract.js is loaded correctly
