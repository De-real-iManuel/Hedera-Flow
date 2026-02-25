/**
 * Example: Integrating OCR with ScanPage
 * 
 * This file shows how to integrate the extractMeterReading function
 * into the ScanPage component for real OCR processing.
 */

import { useState } from "react";
import { Camera } from "@/components/Camera";
import { extractMeterReading, type MeterReadingResult } from "@/lib/ocr";

export function ScanPageWithOCR() {
  const [phase, setPhase] = useState<"ready" | "scanning" | "result">("ready");
  const [ocrResult, setOcrResult] = useState<MeterReadingResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleCapture = async (file: File) => {
    setPhase("scanning");
    setError(null);
    
    try {
      // Run client-side OCR
      const result = await extractMeterReading(file);
      
      console.log('OCR Result:', result);
      console.log(`Reading: ${result.reading} kWh`);
      console.log(`Confidence: ${(result.confidence * 100).toFixed(1)}%`);
      
      setOcrResult(result);
      
      // Check confidence threshold (FR-3.2)
      if (result.confidence > 0.9) {
        // High confidence - proceed with client result
        console.log('High confidence - using client-side OCR result');
        setPhase("result");
      } else if (result.confidence > 0.7) {
        // Medium confidence - show result but may need verification
        console.log('Medium confidence - showing result with warning');
        setPhase("result");
      } else {
        // Low confidence - fallback to server OCR
        console.log('Low confidence - falling back to server OCR');
        await sendToServerOCR(file, result);
      }
    } catch (err) {
      console.error('OCR failed:', err);
      setError('Failed to read meter. Please try again or enter manually.');
      setPhase("ready");
    }
  };

  const sendToServerOCR = async (file: File, clientResult: MeterReadingResult) => {
    // This would be implemented in Task 11 (Server-Side OCR)
    // For now, just log and show the client result
    console.log('Would send to server OCR:', {
      file: file.name,
      clientReading: clientResult.reading,
      clientConfidence: clientResult.confidence,
    });
    
    // Show result anyway for MVP
    setPhase("result");
  };

  return (
    <div className="space-y-6">
      {phase === "ready" && (
        <div>
          <Camera onCapture={handleCapture} />
          {error && (
            <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg">
              <p className="text-sm text-red-800">{error}</p>
            </div>
          )}
        </div>
      )}

      {phase === "scanning" && (
        <div className="flex flex-col items-center justify-center py-20 space-y-6">
          <div className="relative w-20 h-20">
            <div className="absolute inset-0 rounded-full border-4 border-accent/20" />
            <div className="absolute inset-0 rounded-full border-4 border-transparent border-t-accent animate-spin" />
          </div>
          <div className="text-center">
            <p className="text-lg font-semibold">AI Verifying Reading...</p>
            <p className="text-sm text-muted-foreground mt-1">
              Analyzing meter display with Tesseract.js
            </p>
          </div>
        </div>
      )}

      {phase === "result" && ocrResult && (
        <div className="space-y-4">
          <div className="glass-card-elevated p-5 space-y-4">
            <div className="flex justify-between items-center">
              <span className="text-sm text-muted-foreground">Meter Reading</span>
              <span className="text-lg font-bold">{ocrResult.reading} kWh</span>
            </div>
            
            <div className="flex justify-between items-center">
              <span className="text-sm text-muted-foreground">Confidence</span>
              <span className={`text-sm font-semibold ${
                ocrResult.confidence > 0.9 ? 'text-green-600' :
                ocrResult.confidence > 0.7 ? 'text-yellow-600' :
                'text-red-600'
              }`}>
                {(ocrResult.confidence * 100).toFixed(1)}%
              </span>
            </div>
            
            {ocrResult.confidence < 0.9 && (
              <div className="p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
                <p className="text-xs text-yellow-800">
                  {ocrResult.confidence < 0.7 
                    ? 'Low confidence - please verify reading manually'
                    : 'Medium confidence - please double-check the reading'}
                </p>
              </div>
            )}
            
            <div className="text-xs text-muted-foreground">
              <p>Raw OCR: {ocrResult.rawText}</p>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <button
              onClick={() => setPhase("ready")}
              className="py-3 rounded-lg border border-border font-medium"
            >
              Rescan
            </button>
            <button 
              className="py-3 rounded-lg bg-accent text-white font-semibold"
              disabled={ocrResult.reading === 0}
            >
              Continue
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

/**
 * Alternative: Simpler integration for testing
 */
export function SimpleOCRTest() {
  const [result, setResult] = useState<MeterReadingResult | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setIsProcessing(true);
    try {
      const ocrResult = await extractMeterReading(file);
      setResult(ocrResult);
    } catch (error) {
      console.error('OCR failed:', error);
      alert('Failed to process image');
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className="p-6 space-y-4">
      <h2 className="text-xl font-bold">OCR Test</h2>
      
      <input
        type="file"
        accept="image/*"
        onChange={handleFileUpload}
        disabled={isProcessing}
        className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-accent file:text-white hover:file:bg-accent/90"
      />

      {isProcessing && <p>Processing image...</p>}

      {result && (
        <div className="p-4 border rounded-lg space-y-2">
          <p><strong>Reading:</strong> {result.reading} kWh</p>
          <p><strong>Confidence:</strong> {(result.confidence * 100).toFixed(1)}%</p>
          <p><strong>Raw Text:</strong> {result.rawText}</p>
        </div>
      )}
    </div>
  );
}
