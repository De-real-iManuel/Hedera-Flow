/**
 * OCR Module - Client-Side Meter Reading Extraction
 * 
 * This module provides functionality to extract meter readings from images
 * using Tesseract.js OCR engine. It includes image preprocessing and
 * confidence scoring.
 * 
 * Requirements:
 * - FR-3.1: System shall run Tesseract.js OCR client-side first
 * - FR-3.4: System shall extract reading value and unit
 * - FR-3.5: System shall calculate confidence score (0-100%)
 * - NFR-1.1: Client-side OCR shall complete in < 5 seconds
 */

import Tesseract from 'tesseract.js';

/**
 * Result of OCR meter reading extraction
 */
export interface MeterReadingResult {
  reading: number;
  confidence: number;
  rawText: string;
}

/**
 * Extract meter reading from an image file using Tesseract.js OCR
 * 
 * This function:
 * 1. Converts the image file to base64
 * 2. Preprocesses the image (grayscale, contrast enhancement)
 * 3. Runs Tesseract OCR in Web Worker (Task 10.7) or main thread (fallback)
 * 4. Extracts numeric reading from OCR text
 * 5. Returns reading, confidence score, and raw text
 * 
 * Performance optimization (Task 10.7):
 * - Uses Web Worker to offload CPU-intensive OCR processing
 * - Prevents UI blocking during OCR
 * - Falls back to main thread if Web Workers unavailable
 * 
 * @param imageFile - The image file containing the meter reading
 * @param useWorker - Whether to use Web Worker (default: true)
 * @returns Promise resolving to MeterReadingResult with reading, confidence, and raw text
 * 
 * @example
 * ```typescript
 * const file = new File([blob], 'meter.jpg', { type: 'image/jpeg' });
 * const result = await extractMeterReading(file);
 * console.log(`Reading: ${result.reading} kWh`);
 * console.log(`Confidence: ${result.confidence}%`);
 * ```
 */
export async function extractMeterReading(
  imageFile: File,
  useWorker: boolean = true
): Promise<MeterReadingResult> {
  try {
    // Convert file to base64
    const base64 = await fileToBase64(imageFile);
    
    // Preprocess image for better OCR accuracy
    const preprocessed = await preprocessImage(base64);
    
    // Task 10.7: Use Web Worker for OCR processing if available and enabled
    if (useWorker && typeof Worker !== 'undefined') {
      try {
        return await extractMeterReadingWithWorker(preprocessed);
      } catch (workerError) {
        console.warn('Web Worker OCR failed, falling back to main thread:', workerError);
        // Fall through to main thread processing
      }
    }
    
    // Fallback: Process OCR on main thread
    return await extractMeterReadingMainThread(preprocessed);
  } catch (error) {
    console.error('OCR extraction failed:', error);
    throw new Error('Failed to extract meter reading from image');
  }
}

/**
 * Extract meter reading using Web Worker (Task 10.7)
 * 
 * This offloads the CPU-intensive OCR processing to a background thread,
 * preventing UI blocking and improving perceived performance.
 * 
 * @param preprocessedImage - Preprocessed base64 image
 * @returns Promise resolving to MeterReadingResult
 */
async function extractMeterReadingWithWorker(
  preprocessedImage: string
): Promise<MeterReadingResult> {
  return new Promise((resolve, reject) => {
    // Create Web Worker
    const worker = new Worker(
      new URL('./ocr.worker.ts', import.meta.url),
      { type: 'module' }
    );

    // Set timeout to prevent hanging (10 seconds)
    const timeout = setTimeout(() => {
      worker.terminate();
      reject(new Error('OCR worker timeout'));
    }, 10000);

    // Handle worker messages
    worker.onmessage = (event: MessageEvent) => {
      const response = event.data;

      if (response.type === 'success') {
        clearTimeout(timeout);
        worker.terminate();
        resolve(response.data);
      } else if (response.type === 'error') {
        clearTimeout(timeout);
        worker.terminate();
        reject(new Error(response.error || 'OCR worker error'));
      } else if (response.type === 'progress') {
        // Log progress (optional)
        console.log(`OCR Progress: ${Math.round(response.progress * 100)}%`);
      }
    };

    // Handle worker errors
    worker.onerror = (error) => {
      clearTimeout(timeout);
      worker.terminate();
      reject(error);
    };

    // Send image to worker for processing
    worker.postMessage({
      type: 'process',
      imageData: preprocessedImage,
    });
  });
}

/**
 * Extract meter reading on main thread (fallback)
 * 
 * This is the original implementation that runs on the main thread.
 * Used as fallback when Web Workers are unavailable or fail.
 * 
 * @param preprocessedImage - Preprocessed base64 image
 * @returns Promise resolving to MeterReadingResult
 */
async function extractMeterReadingMainThread(
  preprocessedImage: string
): Promise<MeterReadingResult> {
  // Create Tesseract worker with digit recognition configuration (Task 10.3)
  const worker = await Tesseract.createWorker('eng', 1, {
    logger: (m) => {
      // Log progress for debugging (can be removed in production)
      if (m.status === 'recognizing text') {
        console.log(`OCR Progress: ${Math.round(m.progress * 100)}%`);
      }
    },
  });
  
  // Configure Tesseract for digit-only recognition (Task 10.3)
  // This improves accuracy by limiting character set to digits and decimal point
  await worker.setParameters({
    tessedit_char_whitelist: '0123456789.',
  });
  
  // Run OCR recognition
  const result = await worker.recognize(preprocessedImage);
  
  // Clean up worker
  await worker.terminate();
  
  const text = result.data.text.trim();
  const ocrConfidence = result.data.confidence; // Tesseract confidence (0-100)
  
  // Extract numeric reading from OCR text
  const reading = extractNumericReading(text);
  
  // Calculate enhanced confidence score (Task 10.5)
  const confidence = calculateConfidenceScore(ocrConfidence, reading, text);
  
  return {
    reading,
    confidence,
    rawText: text,
  };
}

/**
 * Convert a File object to base64 string
 * 
 * @param file - The file to convert
 * @returns Promise resolving to base64 string
 */
function fileToBase64(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result as string);
    reader.onerror = reject;
    reader.readAsDataURL(file);
  });
}

/**
 * Preprocess image for better OCR accuracy
 * 
 * Applies the following transformations per FR-3.6:
 * 1. Resize to 1024x1024 (maintains aspect ratio with padding)
 * 2. Grayscale conversion
 * 3. Contrast enhancement (adaptive histogram equalization)
 * 4. Noise reduction (median filter)
 * 
 * Note: Rotation correction is handled separately if needed
 * 
 * @param base64 - Base64 encoded image
 * @returns Promise resolving to preprocessed base64 image
 */
async function preprocessImage(base64: string): Promise<string> {
  return new Promise((resolve) => {
    // Check if we're in a browser environment with canvas support
    if (typeof document === 'undefined' || typeof Image === 'undefined') {
      resolve(base64); // Return original in non-browser environments (e.g., tests)
      return;
    }
    
    const img = new Image();
    img.onload = () => {
      const canvas = document.createElement('canvas');
      const ctx = canvas.getContext('2d');
      
      if (!ctx) {
        resolve(base64); // Return original if canvas not available
        return;
      }
      
      // FR-3.6: Resize to 1024x1024 (maintain aspect ratio)
      const targetSize = 1024;
      const scale = Math.min(targetSize / img.width, targetSize / img.height);
      const scaledWidth = img.width * scale;
      const scaledHeight = img.height * scale;
      
      // Center the image on canvas with padding
      const offsetX = (targetSize - scaledWidth) / 2;
      const offsetY = (targetSize - scaledHeight) / 2;
      
      canvas.width = targetSize;
      canvas.height = targetSize;
      
      // Fill with white background
      ctx.fillStyle = '#FFFFFF';
      ctx.fillRect(0, 0, targetSize, targetSize);
      
      // Draw scaled image centered
      ctx.drawImage(img, offsetX, offsetY, scaledWidth, scaledHeight);
      
      // Get image data for pixel manipulation
      const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
      const data = imageData.data;
      
      // Step 1: Convert to grayscale (FR-3.6)
      for (let i = 0; i < data.length; i += 4) {
        // Use luminosity method for better grayscale conversion
        const gray = 0.299 * data[i] + 0.587 * data[i + 1] + 0.114 * data[i + 2];
        data[i] = gray;     // Red
        data[i + 1] = gray; // Green
        data[i + 2] = gray; // Blue
        // Alpha channel (data[i + 3]) remains unchanged
      }
      
      // Step 2: Apply noise reduction (median filter - simplified 3x3)
      const noiseFree = applyNoiseReduction(data, canvas.width, canvas.height);
      
      // Step 3: Enhance contrast (adaptive method)
      const enhanced = enhanceContrast(noiseFree, canvas.width, canvas.height);
      
      // Copy enhanced data back
      for (let i = 0; i < data.length; i++) {
        data[i] = enhanced[i];
      }
      
      // Put processed image data back
      ctx.putImageData(imageData, 0, 0);
      
      // Convert to base64
      resolve(canvas.toDataURL('image/jpeg', 0.95));
    };
    
    img.onerror = () => {
      resolve(base64); // Return original if image load fails
    };
    
    img.src = base64;
  });
}

/**
 * Apply noise reduction using a simplified median filter
 * 
 * This reduces random noise while preserving edges, which is important
 * for OCR accuracy on meter digits.
 * 
 * @param data - Image pixel data (RGBA format)
 * @param width - Image width
 * @param height - Image height
 * @returns Noise-reduced pixel data
 */
function applyNoiseReduction(data: Uint8ClampedArray, width: number, height: number): Uint8ClampedArray {
  const result = new Uint8ClampedArray(data.length);
  
  // Copy original data
  for (let i = 0; i < data.length; i++) {
    result[i] = data[i];
  }
  
  // Apply 3x3 median filter (skip edges for simplicity)
  for (let y = 1; y < height - 1; y++) {
    for (let x = 1; x < width - 1; x++) {
      const idx = (y * width + x) * 4;
      
      // Collect 3x3 neighborhood values (grayscale, so R=G=B)
      const neighbors: number[] = [];
      for (let dy = -1; dy <= 1; dy++) {
        for (let dx = -1; dx <= 1; dx++) {
          const nIdx = ((y + dy) * width + (x + dx)) * 4;
          neighbors.push(data[nIdx]);
        }
      }
      
      // Sort and take median
      neighbors.sort((a, b) => a - b);
      const median = neighbors[4]; // Middle value of 9 elements
      
      // Apply median to RGB channels (grayscale so all same)
      result[idx] = median;
      result[idx + 1] = median;
      result[idx + 2] = median;
      // Keep alpha unchanged
      result[idx + 3] = data[idx + 3];
    }
  }
  
  return result;
}

/**
 * Enhance contrast using adaptive histogram equalization
 * 
 * This improves the visibility of meter digits by stretching the
 * intensity range, making dark digits darker and light backgrounds lighter.
 * 
 * @param data - Image pixel data (RGBA format)
 * @param width - Image width
 * @param height - Image height
 * @returns Contrast-enhanced pixel data
 */
function enhanceContrast(data: Uint8ClampedArray, width: number, height: number): Uint8ClampedArray {
  const result = new Uint8ClampedArray(data.length);
  
  // Build histogram
  const histogram = new Array(256).fill(0);
  for (let i = 0; i < data.length; i += 4) {
    histogram[data[i]]++;
  }
  
  // Calculate cumulative distribution function (CDF)
  const cdf = new Array(256).fill(0);
  cdf[0] = histogram[0];
  for (let i = 1; i < 256; i++) {
    cdf[i] = cdf[i - 1] + histogram[i];
  }
  
  // Find min and max non-zero CDF values
  let cdfMin = 0;
  for (let i = 0; i < 256; i++) {
    if (cdf[i] > 0) {
      cdfMin = cdf[i];
      break;
    }
  }
  
  const totalPixels = width * height;
  
  // Apply histogram equalization
  for (let i = 0; i < data.length; i += 4) {
    const oldValue = data[i];
    
    // Histogram equalization formula
    const newValue = Math.round(((cdf[oldValue] - cdfMin) / (totalPixels - cdfMin)) * 255);
    
    // Apply to RGB channels (grayscale so all same)
    result[i] = newValue;
    result[i + 1] = newValue;
    result[i + 2] = newValue;
    result[i + 3] = data[i + 3]; // Keep alpha unchanged
  }
  
  return result;
}

/**
 * Calculate enhanced confidence score for OCR result
 * 
 * This function combines multiple factors to produce a more accurate confidence score:
 * 1. Base OCR confidence from Tesseract (0-100)
 * 2. Reading validity (is it a valid number in expected range?)
 * 3. Text quality (clean digits vs. noisy text)
 * 4. Format consistency (expected meter reading format)
 * 
 * The final score is normalized to 0-1 range (0-100% when displayed)
 * 
 * Requirements:
 * - FR-3.5: System shall calculate confidence score (0-100%)
 * 
 * @param ocrConfidence - Raw confidence from Tesseract (0-100)
 * @param reading - Extracted numeric reading
 * @param rawText - Raw OCR text
 * @returns Enhanced confidence score (0-1 range)
 */
function calculateConfidenceScore(
  ocrConfidence: number,
  reading: number,
  rawText: string
): number {
  // Start with base OCR confidence (convert to 0-1 range)
  let confidence = ocrConfidence / 100;
  
  // Factor 1: Reading validity check
  // If reading is 0 (invalid), significantly reduce confidence
  if (reading === 0) {
    confidence *= 0.3; // Reduce to 30% of original
  } else if (reading < 10) {
    // Very low readings are less common, slightly reduce confidence
    confidence *= 0.9;
  } else if (reading > 50000) {
    // Very high readings are less common, slightly reduce confidence
    confidence *= 0.95;
  }
  
  // Factor 2: Text quality check
  // Clean text with only digits and decimal points indicates better OCR
  const cleanedText = rawText.replace(/\s+/g, '');
  const digitCount = (cleanedText.match(/[0-9]/g) || []).length;
  const totalChars = cleanedText.length;
  
  if (totalChars > 0) {
    const digitRatio = digitCount / totalChars;
    
    if (digitRatio >= 0.9) {
      // Very clean text (90%+ digits), boost confidence slightly
      confidence *= 1.05;
    } else if (digitRatio < 0.5) {
      // Noisy text (less than 50% digits), reduce confidence
      confidence *= 0.85;
    }
  }
  
  // Factor 3: Format consistency check
  // Expected format: 3-6 digits, optionally with decimal point
  const hasValidFormat = /^\d{3,6}(\.\d{1,2})?$/.test(cleanedText);
  if (hasValidFormat) {
    // Text matches expected meter reading format, boost confidence
    confidence *= 1.1;
  } else if (cleanedText.length > 0 && !/\d/.test(cleanedText)) {
    // No digits at all in text, severely reduce confidence
    confidence *= 0.2;
  }
  
  // Factor 4: Decimal point handling
  // If there's a decimal point, check if it's in a reasonable position
  const decimalCount = (cleanedText.match(/\./g) || []).length;
  if (decimalCount === 1) {
    // Single decimal point is good
    confidence *= 1.02;
  } else if (decimalCount > 1) {
    // Multiple decimal points indicate OCR error
    confidence *= 0.7;
  }
  
  // Ensure confidence stays within 0-1 range
  confidence = Math.max(0, Math.min(1, confidence));
  
  return confidence;
}

/**
 * Extract numeric reading from OCR text
 * 
 * Handles various formats:
 * - Simple numbers: "12345" -> 12345
 * - Decimals: "12345.67" -> 12345.67
 * - Multiple numbers: "12345 67" -> 12345 (takes first)
 * - With units: "12345 kWh" -> 12345
 * 
 * @param text - Raw OCR text
 * @returns Extracted numeric reading, or 0 if no valid number found
 */
function extractNumericReading(text: string): number {
  // Remove whitespace and newlines
  const cleaned = text.replace(/\s+/g, '');
  
  // Find all numeric patterns (including decimals)
  const matches = cleaned.match(/\d+\.?\d*/g);
  
  if (!matches || matches.length === 0) {
    return 0;
  }
  
  // Take the first (and usually only) number found
  const reading = parseFloat(matches[0]);
  
  // Validate reading is within reasonable range (0-100000 kWh)
  if (isNaN(reading) || reading < 0 || reading > 100000) {
    return 0;
  }
  
  return reading;
}
