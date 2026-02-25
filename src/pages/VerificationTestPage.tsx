import { useState } from "react";
import { motion } from "framer-motion";
import AppHeader from "@/components/AppHeader";
import { VerificationResult, VerificationResultData } from "@/components/VerificationResult";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

// Mock data for different verification statuses
const mockVerificationData: Record<string, VerificationResultData> = {
  VERIFIED: {
    reading: 5142.7,
    previousReading: 4894.3,
    consumption: 248.4,
    confidence: 0.96,
    status: 'VERIFIED',
    fraudScore: 0.12,
    fraudFlags: [],
    ocrEngine: 'tesseract',
    rawOcrText: '5142.7 kWh',
    imageIpfsHash: 'QmX7Y8Z9...',
    imageMetadata: {
      gpsCoordinates: '6.5244, 3.3792',
      timestamp: new Date().toISOString(),
      deviceId: 'iPhone 14 Pro',
    },
    bill: {
      baseCharge: 10500,
      taxes: 1575,
      serviceCharge: 375,
      total: 12450,
      currency: 'NGN',
      breakdown: [
        { description: 'Energy Charge (248.4 kWh @ ₦40/kWh)', amount: 9936 },
        { description: 'Service Charge', amount: 375 },
        { description: 'VAT (7.5%)', amount: 773 },
        { description: 'Distribution Charge', amount: 1366 },
      ],
    },
    hcsSequenceNumber: 12345,
    hcsTopicId: '0.0.TOPIC_AFRICA',
    utilityReading: 5089.2,
  },
  
  WARNING: {
    reading: 5142.7,
    previousReading: 4894.3,
    consumption: 248.4,
    confidence: 0.78,
    status: 'WARNING',
    fraudScore: 0.45,
    fraudFlags: [
      'Confidence score below 90% threshold',
      'Image quality could be improved',
    ],
    ocrEngine: 'google_vision',
    rawOcrText: '5142.7 kWh (low confidence)',
    imageIpfsHash: 'QmA1B2C3...',
    imageMetadata: {
      gpsCoordinates: '6.5244, 3.3792',
      timestamp: new Date().toISOString(),
      deviceId: 'Samsung Galaxy S21',
    },
    bill: {
      baseCharge: 10500,
      taxes: 1575,
      serviceCharge: 375,
      total: 12450,
      currency: 'NGN',
      breakdown: [
        { description: 'Energy Charge (248.4 kWh @ ₦40/kWh)', amount: 9936 },
        { description: 'Service Charge', amount: 375 },
        { description: 'VAT (7.5%)', amount: 773 },
        { description: 'Distribution Charge', amount: 1366 },
      ],
    },
    hcsSequenceNumber: 12346,
    hcsTopicId: '0.0.TOPIC_AFRICA',
    utilityReading: 5089.2,
  },
  
  DISCREPANCY: {
    reading: 5142.7,
    previousReading: 4894.3,
    consumption: 248.4,
    confidence: 0.92,
    status: 'DISCREPANCY',
    fraudScore: 0.68,
    fraudFlags: [
      'Reading differs from utility by >10%',
      'Consumption pattern unusual for this period',
    ],
    ocrEngine: 'tesseract',
    rawOcrText: '5142.7 kWh',
    imageIpfsHash: 'QmD4E5F6...',
    imageMetadata: {
      gpsCoordinates: '6.5244, 3.3792',
      timestamp: new Date().toISOString(),
      deviceId: 'iPhone 13',
    },
    bill: {
      baseCharge: 10500,
      taxes: 1575,
      serviceCharge: 375,
      total: 12450,
      currency: 'NGN',
      breakdown: [
        { description: 'Energy Charge (248.4 kWh @ ₦40/kWh)', amount: 9936 },
        { description: 'Service Charge', amount: 375 },
        { description: 'VAT (7.5%)', amount: 773 },
        { description: 'Distribution Charge', amount: 1366 },
      ],
    },
    hcsSequenceNumber: 12347,
    hcsTopicId: '0.0.TOPIC_AFRICA',
    utilityReading: 4523.1, // Significant difference
  },
  
  FRAUD_DETECTED: {
    reading: 5142.7,
    previousReading: 4894.3,
    consumption: 248.4,
    confidence: 0.88,
    status: 'FRAUD_DETECTED',
    fraudScore: 0.89,
    fraudFlags: [
      'Image metadata missing or tampered',
      'GPS coordinates do not match registered meter location',
      'Timestamp inconsistency detected',
      'Error Level Analysis indicates photo manipulation',
      'Reading pattern suggests meter tampering',
    ],
    ocrEngine: 'google_vision',
    rawOcrText: '5142.7 kWh',
    imageIpfsHash: 'QmG7H8I9...',
    imageMetadata: {
      gpsCoordinates: 'Unknown',
      timestamp: new Date(Date.now() - 86400000 * 7).toISOString(), // 7 days ago
      deviceId: 'Unknown Device',
    },
    bill: {
      baseCharge: 10500,
      taxes: 1575,
      serviceCharge: 375,
      total: 12450,
      currency: 'NGN',
      breakdown: [
        { description: 'Energy Charge (248.4 kWh @ ₦40/kWh)', amount: 9936 },
        { description: 'Service Charge', amount: 375 },
        { description: 'VAT (7.5%)', amount: 773 },
        { description: 'Distribution Charge', amount: 1366 },
      ],
    },
    hcsSequenceNumber: 12348,
    hcsTopicId: '0.0.TOPIC_AFRICA',
    utilityReading: 5089.2,
  },
};

const VerificationTestPage = () => {
  const [selectedStatus, setSelectedStatus] = useState<keyof typeof mockVerificationData>('VERIFIED');
  const [showResult, setShowResult] = useState(false);

  const handleStatusSelect = (status: keyof typeof mockVerificationData) => {
    setSelectedStatus(status);
    setShowResult(true);
  };

  const handleRetry = () => {
    setShowResult(false);
  };

  const handlePay = () => {
    alert('Payment flow would be triggered here');
  };

  return (
    <div className="min-h-screen bg-background pb-24">
      <AppHeader title="Verification Status Testing" />

      <div className="px-5 py-6 space-y-6">
        {/* Instructions Card */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Test Verification UI</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <p className="text-sm text-muted-foreground">
              This page allows you to test the verification result UI with different statuses.
              Select a status below to see how the UI renders for each scenario.
            </p>
            <div className="space-y-2">
              <p className="text-xs font-semibold text-muted-foreground uppercase">Test Scenarios:</p>
              <ul className="text-xs text-muted-foreground space-y-1">
                <li>• <strong>VERIFIED</strong>: Reading verified successfully (green)</li>
                <li>• <strong>WARNING</strong>: Low confidence or minor issues (yellow)</li>
                <li>• <strong>DISCREPANCY</strong>: Significant difference from utility reading (red)</li>
                <li>• <strong>FRAUD_DETECTED</strong>: Multiple fraud indicators detected (red)</li>
              </ul>
            </div>
          </CardContent>
        </Card>

        {/* Status Selection Buttons */}
        {!showResult && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-3"
          >
            <h3 className="text-sm font-semibold text-foreground">Select Status to Test:</h3>
            
            <div className="grid grid-cols-1 gap-3">
              <Button
                variant="outline"
                size="lg"
                onClick={() => handleStatusSelect('VERIFIED')}
                className="justify-start h-auto py-4"
              >
                <div className="flex items-center gap-3 w-full">
                  <div className="w-10 h-10 rounded-full bg-green-100 flex items-center justify-center">
                    <span className="text-green-600 text-lg">✓</span>
                  </div>
                  <div className="flex-1 text-left">
                    <p className="font-semibold text-foreground">VERIFIED</p>
                    <p className="text-xs text-muted-foreground">High confidence, no issues detected</p>
                  </div>
                  <Badge variant="default">Success</Badge>
                </div>
              </Button>

              <Button
                variant="outline"
                size="lg"
                onClick={() => handleStatusSelect('WARNING')}
                className="justify-start h-auto py-4"
              >
                <div className="flex items-center gap-3 w-full">
                  <div className="w-10 h-10 rounded-full bg-yellow-100 flex items-center justify-center">
                    <span className="text-yellow-600 text-lg">⚠</span>
                  </div>
                  <div className="flex-1 text-left">
                    <p className="font-semibold text-foreground">WARNING</p>
                    <p className="text-xs text-muted-foreground">Low confidence or minor issues</p>
                  </div>
                  <Badge variant="secondary">Warning</Badge>
                </div>
              </Button>

              <Button
                variant="outline"
                size="lg"
                onClick={() => handleStatusSelect('DISCREPANCY')}
                className="justify-start h-auto py-4"
              >
                <div className="flex items-center gap-3 w-full">
                  <div className="w-10 h-10 rounded-full bg-red-100 flex items-center justify-center">
                    <span className="text-red-600 text-lg">✕</span>
                  </div>
                  <div className="flex-1 text-left">
                    <p className="font-semibold text-foreground">DISCREPANCY</p>
                    <p className="text-xs text-muted-foreground">Significant difference detected</p>
                  </div>
                  <Badge variant="destructive">Error</Badge>
                </div>
              </Button>

              <Button
                variant="outline"
                size="lg"
                onClick={() => handleStatusSelect('FRAUD_DETECTED')}
                className="justify-start h-auto py-4"
              >
                <div className="flex items-center gap-3 w-full">
                  <div className="w-10 h-10 rounded-full bg-red-100 flex items-center justify-center">
                    <span className="text-red-600 text-lg">🛡</span>
                  </div>
                  <div className="flex-1 text-left">
                    <p className="font-semibold text-foreground">FRAUD_DETECTED</p>
                    <p className="text-xs text-muted-foreground">Multiple fraud indicators found</p>
                  </div>
                  <Badge variant="destructive">Fraud</Badge>
                </div>
              </Button>
            </div>
          </motion.div>
        )}

        {/* Verification Result Display */}
        {showResult && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
          >
            <VerificationResult
              data={mockVerificationData[selectedStatus]}
              onRetry={handleRetry}
              onPay={handlePay}
            />
          </motion.div>
        )}
      </div>
    </div>
  );
};

export default VerificationTestPage;
