/**
 * OCR Web Worker Usage Example (Task 10.7)
 * 
 * This example demonstrates how to use the Web Worker-optimized OCR
 * for better performance and UI responsiveness.
 */

import React, { useState } from 'react';
import { extractMeterReading, MeterReadingResult } from './ocr';

export function OCRWebWorkerExample() {
  const [result, setResult] = useState<MeterReadingResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleImageUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      // Default: Uses Web Worker (non-blocking)
      const ocrResult = await extractMeterReading(file);
      
      // Alternative: Force main thread (for debugging)
      // const ocrResult = await extractMeterReading(file, false);
      
      setResult(ocrResult);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'OCR failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-6 max-w-md mx-auto">
      <h2 className="text-2xl font-bold mb-4">OCR Web Worker Demo</h2>
      
      <div className="mb-4">
        <label className="block mb-2 font-medium">
          Upload Meter Image
        </label>
        <input
          type="file"
          accept="image/*"
          onChange={handleImageUpload}
          className="block w-full text-sm text-gray-500
            file:mr-4 file:py-2 file:px-4
            file:rounded-lg file:border-0
            file:text-sm file:font-semibold
            file:bg-blue-50 file:text-blue-700
            hover:file:bg-blue-100"
        />
      </div>

      {loading && (
        <div className="p-4 bg-blue-50 rounded-lg">
          <p className="text-blue-700 font-medium">
            Processing OCR in background...
          </p>
          <p className="text-sm text-blue-600 mt-1">
            UI remains responsive thanks to Web Workers! 🚀
          </p>
        </div>
      )}

      {error && (
        <div className="p-4 bg-red-50 rounded-lg">
          <p className="text-red-700 font-medium">Error</p>
          <p className="text-sm text-red-600 mt-1">{error}</p>
        </div>
      )}

      {result && (
        <div className="p-4 bg-green-50 rounded-lg">
          <h3 className="text-green-700 font-bold mb-2">OCR Result</h3>
          <div className="space-y-2 text-sm">
            <div>
              <span className="font-medium">Reading:</span>{' '}
              <span className="text-green-700">{result.reading} kWh</span>
            </div>
            <div>
              <span className="font-medium">Confidence:</span>{' '}
              <span className="text-green-700">
                {(result.confidence * 100).toFixed(1)}%
              </span>
            </div>
            <div>
              <span className="font-medium">Raw Text:</span>{' '}
              <span className="text-gray-600">{result.rawText}</span>
            </div>
          </div>
        </div>
      )}

      <div className="mt-6 p-4 bg-gray-50 rounded-lg">
        <h3 className="font-bold mb-2">Performance Benefits</h3>
        <ul className="text-sm space-y-1 text-gray-700">
          <li>✅ Non-blocking UI (Web Worker)</li>
          <li>✅ Automatic fallback to main thread</li>
          <li>✅ 10-second timeout protection</li>
          <li>✅ Progress updates (check console)</li>
          <li>✅ Same accuracy as before</li>
        </ul>
      </div>

      <div className="mt-4 p-4 bg-yellow-50 rounded-lg">
        <h3 className="font-bold mb-2">Try This</h3>
        <p className="text-sm text-gray-700">
          While OCR is processing, try clicking around the page.
          Notice how the UI stays responsive? That's the Web Worker
          doing its job! 🎉
        </p>
      </div>
    </div>
  );
}

/**
 * Advanced Usage: Custom Progress Tracking
 */
export function OCRWithProgressTracking() {
  const [progress, setProgress] = useState(0);
  const [result, setResult] = useState<MeterReadingResult | null>(null);

  const handleImageUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setProgress(0);
    setResult(null);

    // Note: Progress tracking would require extending the worker
    // to send progress updates back to the main thread
    // For now, we simulate progress
    const progressInterval = setInterval(() => {
      setProgress(prev => Math.min(prev + 10, 90));
    }, 200);

    try {
      const ocrResult = await extractMeterReading(file);
      setProgress(100);
      setResult(ocrResult);
    } catch (err) {
      console.error('OCR failed:', err);
    } finally {
      clearInterval(progressInterval);
    }
  };

  return (
    <div className="p-6 max-w-md mx-auto">
      <h2 className="text-2xl font-bold mb-4">OCR with Progress</h2>
      
      <input
        type="file"
        accept="image/*"
        onChange={handleImageUpload}
        className="block w-full mb-4"
      />

      {progress > 0 && progress < 100 && (
        <div className="mb-4">
          <div className="flex justify-between mb-1">
            <span className="text-sm font-medium">Processing...</span>
            <span className="text-sm font-medium">{progress}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className="bg-blue-600 h-2 rounded-full transition-all duration-300"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>
      )}

      {result && (
        <div className="p-4 bg-green-50 rounded-lg">
          <p className="font-bold text-green-700">
            Reading: {result.reading} kWh
          </p>
          <p className="text-sm text-green-600">
            Confidence: {(result.confidence * 100).toFixed(1)}%
          </p>
        </div>
      )}
    </div>
  );
}

/**
 * Performance Comparison: Worker vs Main Thread
 */
export function OCRPerformanceComparison() {
  const [workerTime, setWorkerTime] = useState<number | null>(null);
  const [mainThreadTime, setMainThreadTime] = useState<number | null>(null);

  const testPerformance = async (file: File, useWorker: boolean) => {
    const start = performance.now();
    await extractMeterReading(file, useWorker);
    const end = performance.now();
    return end - start;
  };

  const handleImageUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    // Test with Web Worker
    const workerDuration = await testPerformance(file, true);
    setWorkerTime(workerDuration);

    // Test with main thread
    const mainThreadDuration = await testPerformance(file, false);
    setMainThreadTime(mainThreadDuration);
  };

  return (
    <div className="p-6 max-w-md mx-auto">
      <h2 className="text-2xl font-bold mb-4">Performance Comparison</h2>
      
      <input
        type="file"
        accept="image/*"
        onChange={handleImageUpload}
        className="block w-full mb-4"
      />

      {workerTime && mainThreadTime && (
        <div className="space-y-4">
          <div className="p-4 bg-blue-50 rounded-lg">
            <p className="font-bold text-blue-700">Web Worker</p>
            <p className="text-2xl font-bold text-blue-900">
              {workerTime.toFixed(0)}ms
            </p>
            <p className="text-sm text-blue-600">Non-blocking UI ✅</p>
          </div>

          <div className="p-4 bg-gray-50 rounded-lg">
            <p className="font-bold text-gray-700">Main Thread</p>
            <p className="text-2xl font-bold text-gray-900">
              {mainThreadTime.toFixed(0)}ms
            </p>
            <p className="text-sm text-gray-600">Blocks UI ❌</p>
          </div>

          <div className="p-4 bg-green-50 rounded-lg">
            <p className="font-bold text-green-700">Key Difference</p>
            <p className="text-sm text-green-600">
              Both take similar time, but Web Worker keeps UI responsive!
              The perceived performance is much better.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
