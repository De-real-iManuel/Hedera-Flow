/**
 * OCR Web Worker - Offload OCR processing to background thread
 * 
 * This worker handles the CPU-intensive OCR processing in a separate thread,
 * preventing UI blocking and improving performance.
 * 
 * Requirements:
 * - NFR-1.1: Client-side OCR shall complete in < 5 seconds
 * - Task 10.7: Optimize performance using Web Workers
 */

import Tesseract from 'tesseract.js';

/**
 * Message types for worker communication
 */
interface WorkerRequest {
  type: 'process';
  imageData: string; // Base64 encoded image
}

interface WorkerResponse {
  type: 'success' | 'error' | 'progress';
  data?: {
    reading: number;
    confidence: number;
    rawText: string;
  };
  error?: string;
  progress?: number;
}

/**
 * Process OCR in Web Worker
 */
self.onmessage = async (event: MessageEvent<WorkerRequest>) => {
  const { type, imageData } = event.data;

  if (type !== 'process') {
    postMessage({
      type: 'error',
      error: 'Invalid message type',
    } as WorkerResponse);
    return;
  }

  try {
    // Create Tesseract worker with digit recognition configuration
    const worker = await Tesseract.createWorker('eng', 1, {
      logger: (m) => {
        // Send progress updates to main thread
        if (m.status === 'recognizing text') {
          postMessage({
            type: 'progress',
            progress: m.progress,
          } as WorkerResponse);
        }
      },
    });

    // Configure Tesseract for digit-only recognition
    await worker.setParameters({
      tessedit_char_whitelist: '0123456789.',
    });

    // Run OCR recognition
    const result = await worker.recognize(imageData);

    // Clean up worker
    await worker.terminate();

    const text = result.data.text.trim();
    const ocrConfidence = result.data.confidence;

    // Extract numeric reading
    const reading = extractNumericReading(text);

    // Calculate enhanced confidence score
    const confidence = calculateConfidenceScore(ocrConfidence, reading, text);

    // Send success response
    postMessage({
      type: 'success',
      data: {
        reading,
        confidence,
        rawText: text,
      },
    } as WorkerResponse);
  } catch (error) {
    // Send error response
    postMessage({
      type: 'error',
      error: error instanceof Error ? error.message : 'OCR processing failed',
    } as WorkerResponse);
  }
};

/**
 * Extract numeric reading from OCR text
 * (Same logic as main thread for consistency)
 */
function extractNumericReading(text: string): number {
  const cleaned = text.replace(/\s+/g, '');
  const matches = cleaned.match(/\d+\.?\d*/g);

  if (!matches || matches.length === 0) {
    return 0;
  }

  const reading = parseFloat(matches[0]);

  if (isNaN(reading) || reading < 0 || reading > 100000) {
    return 0;
  }

  return reading;
}

/**
 * Calculate enhanced confidence score
 * (Same logic as main thread for consistency)
 */
function calculateConfidenceScore(
  ocrConfidence: number,
  reading: number,
  rawText: string
): number {
  let confidence = ocrConfidence / 100;

  // Factor 1: Reading validity
  if (reading === 0) {
    confidence *= 0.3;
  } else if (reading < 10) {
    confidence *= 0.9;
  } else if (reading > 50000) {
    confidence *= 0.95;
  }

  // Factor 2: Text quality
  const cleanedText = rawText.replace(/\s+/g, '');
  const digitCount = (cleanedText.match(/[0-9]/g) || []).length;
  const totalChars = cleanedText.length;

  if (totalChars > 0) {
    const digitRatio = digitCount / totalChars;

    if (digitRatio >= 0.9) {
      confidence *= 1.05;
    } else if (digitRatio < 0.5) {
      confidence *= 0.85;
    }
  }

  // Factor 3: Format consistency
  const hasValidFormat = /^\d{3,6}(\.\d{1,2})?$/.test(cleanedText);
  if (hasValidFormat) {
    confidence *= 1.1;
  } else if (cleanedText.length > 0 && !/\d/.test(cleanedText)) {
    confidence *= 0.2;
  }

  // Factor 4: Decimal point handling
  const decimalCount = (cleanedText.match(/\./g) || []).length;
  if (decimalCount === 1) {
    confidence *= 1.02;
  } else if (decimalCount > 1) {
    confidence *= 0.7;
  }

  return Math.max(0, Math.min(1, confidence));
}
