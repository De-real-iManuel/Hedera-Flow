import { motion } from "framer-motion";
import { Check, AlertTriangle, Info, Shield, RotateCcw, XCircle, Eye, ExternalLink } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { useState } from "react";

export interface VerificationResultData {
  // Reading Data
  reading: number;
  previousReading?: number;
  consumption?: number;
  confidence: number;
  
  // Status
  status: 'VERIFIED' | 'WARNING' | 'DISCREPANCY' | 'FRAUD_DETECTED';
  
  // Fraud Detection
  fraudScore: number;
  fraudFlags?: string[];
  
  // OCR Details (for modal)
  ocrEngine?: 'tesseract' | 'google_vision';
  rawOcrText?: string;
  
  // Image Details (for modal)
  imageIpfsHash?: string;
  imageMetadata?: {
    gpsCoordinates?: string;
    timestamp?: string;
    deviceId?: string;
  };
  
  // Billing Data (optional)
  bill?: {
    baseCharge: number;
    taxes: number;
    serviceCharge?: number;
    total: number;
    currency: string;
    breakdown?: Array<{
      description: string;
      amount: number;
    }>;
  };
  
  // Blockchain Data
  hcsSequenceNumber?: number;
  hcsTopicId?: string;
  
  // Utility Reading (for comparison)
  utilityReading?: number;
}

interface VerificationResultProps {
  data: VerificationResultData;
  onRetry?: () => void;
  onPay?: () => void;
}

export function VerificationResult({ data, onRetry, onPay }: VerificationResultProps) {
  const [isDetailsOpen, setIsDetailsOpen] = useState(false);
  
  const getStatusConfig = () => {
    switch (data.status) {
      case 'VERIFIED':
        return {
          icon: Check,
          color: 'text-green-600',
          bgColor: 'bg-green-50',
          borderColor: 'border-green-200',
          title: 'Reading Verified',
          badge: 'VERIFIED ✓',
          badgeVariant: 'default' as const,
        };
      case 'WARNING':
        return {
          icon: AlertTriangle,
          color: 'text-yellow-600',
          bgColor: 'bg-yellow-50',
          borderColor: 'border-yellow-200',
          title: 'Warning Detected',
          badge: 'WARNING ⚠',
          badgeVariant: 'secondary' as const,
        };
      case 'DISCREPANCY':
        return {
          icon: XCircle,
          color: 'text-red-600',
          bgColor: 'bg-red-50',
          borderColor: 'border-red-200',
          title: 'Discrepancy Found',
          badge: 'DISCREPANCY ❌',
          badgeVariant: 'destructive' as const,
        };
      case 'FRAUD_DETECTED':
        return {
          icon: Shield,
          color: 'text-red-600',
          bgColor: 'bg-red-50',
          borderColor: 'border-red-200',
          title: 'Fraud Detected',
          badge: 'FRAUD DETECTED',
          badgeVariant: 'destructive' as const,
        };
      default:
        return {
          icon: Check,
          color: 'text-gray-600',
          bgColor: 'bg-gray-50',
          borderColor: 'border-gray-200',
          title: 'Verification Complete',
          badge: 'COMPLETE',
          badgeVariant: 'outline' as const,
        };
    }
  };

  const statusConfig = getStatusConfig();
  const StatusIcon = statusConfig.icon;
  
  const getFraudScoreColor = () => {
    if (data.fraudScore < 0.3) return 'bg-green-500';
    if (data.fraudScore < 0.7) return 'bg-yellow-500';
    return 'bg-red-500';
  };
  
  const getFraudScoreLabel = () => {
    if (data.fraudScore < 0.3) return 'Low Risk';
    if (data.fraudScore < 0.7) return 'Medium Risk';
    return 'High Risk';
  };

  const formatCurrency = (amount: number, currency: string) => {
    const symbols: Record<string, string> = {
      EUR: '€',
      USD: '$',
      INR: '₹',
      BRL: 'R$',
      NGN: '₦',
    };
    return `${symbols[currency] || currency}${amount.toLocaleString()}`;
  };

  const calculateDifference = () => {
    if (!data.utilityReading) return null;
    const diff = ((data.reading - data.utilityReading) / data.utilityReading) * 100;
    return diff.toFixed(1);
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0 }}
      className="space-y-5"
    >
      {/* Status Header */}
      <div className="flex flex-col items-center py-6 space-y-3">
        <div className={`w-16 h-16 rounded-full ${statusConfig.bgColor} flex items-center justify-center`}>
          <StatusIcon className={`w-8 h-8 ${statusConfig.color}`} />
        </div>
        <div className="text-center">
          <h2 className="text-2xl font-bold text-foreground">{statusConfig.title}</h2>
          <p className="text-sm text-muted-foreground mt-1">
            Confidence: {(data.confidence * 100).toFixed(0)}%
          </p>
        </div>
        <Badge variant={statusConfig.badgeVariant}>{statusConfig.badge}</Badge>
      </div>

      {/* Verification Details Card */}
      <Card className="border-2">
        <CardContent className="p-5 space-y-4">
          {/* Meter Reading */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-muted-foreground">Meter Reading</span>
              <span className="text-2xl font-bold text-foreground">
                {data.reading.toLocaleString()} kWh
              </span>
            </div>
            
            {data.previousReading && (
              <div className="flex items-center justify-between text-sm">
                <span className="text-muted-foreground">Previous Reading</span>
                <span className="text-foreground">{data.previousReading.toLocaleString()} kWh</span>
              </div>
            )}
            
            {data.utilityReading && (
              <div className="flex items-center justify-between text-sm">
                <span className="text-muted-foreground">Utility's Reading</span>
                <div className="flex items-center gap-2">
                  <span className="text-foreground">{data.utilityReading.toLocaleString()} kWh</span>
                  {calculateDifference() && (
                    <Badge variant={Math.abs(parseFloat(calculateDifference()!)) > 10 ? 'destructive' : 'secondary'}>
                      {parseFloat(calculateDifference()!) > 0 ? '+' : ''}{calculateDifference()}%
                    </Badge>
                  )}
                </div>
              </div>
            )}
          </div>

          {data.consumption !== undefined && (
            <>
              <Separator />
              
              {/* Consumption */}
              <div className="flex justify-between items-center">
                <span className="text-sm text-muted-foreground">Usage This Period</span>
                <span className="text-xl font-semibold text-primary">
                  {data.consumption.toLocaleString()} kWh
                </span>
              </div>
            </>
          )}

          {/* Bill Breakdown */}
          {data.bill && (
            <>
              <Separator />
              
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                    Tariff Breakdown
                  </p>
                  <button className="text-xs text-primary hover:underline flex items-center gap-1">
                    <Info className="w-3 h-3" />
                    Details
                  </button>
                </div>
                
                {data.bill.breakdown && (
                  <div className="space-y-2">
                    {data.bill.breakdown.map((item, index) => (
                      <div key={index} className="flex justify-between text-sm">
                        <span className="text-muted-foreground">{item.description}</span>
                        <span className="text-foreground">
                          {formatCurrency(item.amount, data.bill!.currency)}
                        </span>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              <Separator />

              {/* Total Bill */}
              <div className="flex justify-between items-center pt-2">
                <span className="text-base font-semibold text-foreground">Total Bill</span>
                <span className="text-3xl font-bold text-primary">
                  {formatCurrency(data.bill.total, data.bill.currency)}
                </span>
              </div>
            </>
          )}
        </CardContent>
      </Card>

      {/* Fraud Score Indicator - Show if applicable */}
      {(data.fraudScore > 0 || (data.fraudFlags && data.fraudFlags.length > 0) || 
        ['WARNING', 'DISCREPANCY', 'FRAUD_DETECTED'].includes(data.status)) && (
        <Card className="border-2">
          <CardContent className="p-4 space-y-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Shield className={`w-4 h-4 ${data.fraudScore < 0.3 ? 'text-green-600' : data.fraudScore < 0.7 ? 'text-yellow-600' : 'text-red-600'}`} />
                <span className="text-sm font-medium text-foreground">Fraud Score</span>
              </div>
              <span className={`text-sm font-semibold ${data.fraudScore < 0.3 ? 'text-green-600' : data.fraudScore < 0.7 ? 'text-yellow-600' : 'text-red-600'}`}>
                {data.fraudScore.toFixed(2)} ({getFraudScoreLabel()})
              </span>
            </div>
            
            <div className="w-full h-2 bg-muted rounded-full overflow-hidden">
              <div 
                className={`h-full ${getFraudScoreColor()} rounded-full transition-all duration-500`}
                style={{ width: `${data.fraudScore * 100}%` }}
              />
            </div>
            
            {data.fraudFlags && data.fraudFlags.length > 0 ? (
              <div className="space-y-1">
                <p className="text-xs font-medium text-muted-foreground">Detected Issues:</p>
                <ul className="text-xs text-muted-foreground space-y-0.5">
                  {data.fraudFlags.map((flag, index) => (
                    <li key={index} className="flex items-start gap-1">
                      <span className="text-red-500">•</span>
                      <span>{flag}</span>
                    </li>
                  ))}
                </ul>
              </div>
            ) : (
              <p className="text-xs text-muted-foreground">
                All validation checks passed. No anomalies detected.
              </p>
            )}
          </CardContent>
        </Card>
      )}

      {/* Usage Alert (if consumption is higher than average) */}
      {data.consumption && data.previousReading && data.consumption > (data.reading - data.previousReading) * 1.1 && (
        <Card className="border-2 border-yellow-200 bg-yellow-50">
          <CardContent className="p-4">
            <div className="flex items-start gap-3">
              <AlertTriangle className="w-5 h-5 text-yellow-600 shrink-0 mt-0.5" />
              <div className="flex-1">
                <p className="text-sm font-medium text-yellow-900 mb-1">Higher Than Average</p>
                <p className="text-xs text-yellow-800">
                  Usage appears higher than typical. Consider checking your appliances.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* View Details Modal */}
      <Dialog open={isDetailsOpen} onOpenChange={setIsDetailsOpen}>
        <DialogTrigger asChild>
          <Button variant="outline" className="w-full" size="lg">
            <Eye className="w-4 h-4 mr-2" />
            View Details
          </Button>
        </DialogTrigger>
        <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Verification Details</DialogTitle>
            <DialogDescription>
              Complete information about this verification including OCR analysis, fraud detection, and blockchain proof.
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-6 mt-4">
            {/* OCR Analysis Section */}
            <div className="space-y-3">
              <h3 className="text-sm font-semibold text-foreground uppercase tracking-wider">OCR Analysis</h3>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Engine Used:</span>
                  <span className="font-medium text-foreground">
                    {data.ocrEngine === 'tesseract' ? 'Tesseract.js (Client-side)' : 
                     data.ocrEngine === 'google_vision' ? 'Google Vision API (Server-side)' : 
                     'Not specified'}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Confidence Score:</span>
                  <span className="font-medium text-foreground">{(data.confidence * 100).toFixed(1)}%</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Extracted Reading:</span>
                  <span className="font-medium text-foreground">{data.reading.toLocaleString()} kWh</span>
                </div>
                {data.rawOcrText && (
                  <div className="pt-2">
                    <span className="text-muted-foreground block mb-1">Raw OCR Text:</span>
                    <div className="bg-muted p-3 rounded-md font-mono text-xs">
                      {data.rawOcrText}
                    </div>
                  </div>
                )}
              </div>
            </div>

            <Separator />

            {/* Fraud Detection Section */}
            <div className="space-y-3">
              <h3 className="text-sm font-semibold text-foreground uppercase tracking-wider">Fraud Detection</h3>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between items-center">
                  <span className="text-muted-foreground">Fraud Score:</span>
                  <div className="flex items-center gap-2">
                    <span className={`font-semibold ${data.fraudScore < 0.3 ? 'text-green-600' : data.fraudScore < 0.7 ? 'text-yellow-600' : 'text-red-600'}`}>
                      {data.fraudScore.toFixed(2)}
                    </span>
                    <Badge variant={data.fraudScore < 0.3 ? 'default' : data.fraudScore < 0.7 ? 'secondary' : 'destructive'}>
                      {getFraudScoreLabel()}
                    </Badge>
                  </div>
                </div>
                <div className="w-full h-2 bg-muted rounded-full overflow-hidden">
                  <div 
                    className={`h-full ${getFraudScoreColor()} rounded-full transition-all duration-500`}
                    style={{ width: `${data.fraudScore * 100}%` }}
                  />
                </div>
                {data.fraudFlags && data.fraudFlags.length > 0 ? (
                  <div className="pt-2">
                    <span className="text-muted-foreground block mb-2">Detected Issues:</span>
                    <ul className="space-y-1">
                      {data.fraudFlags.map((flag, index) => (
                        <li key={index} className="flex items-start gap-2 text-xs">
                          <span className="text-red-500 mt-0.5">•</span>
                          <span className="text-foreground">{flag}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                ) : (
                  <p className="text-xs text-muted-foreground pt-2">
                    ✓ All validation checks passed. No anomalies detected.
                  </p>
                )}
              </div>
            </div>

            <Separator />

            {/* Image Metadata Section */}
            {data.imageMetadata && (
              <>
                <div className="space-y-3">
                  <h3 className="text-sm font-semibold text-foreground uppercase tracking-wider">Image Metadata</h3>
                  <div className="space-y-2 text-sm">
                    {data.imageMetadata.timestamp && (
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Capture Time:</span>
                        <span className="font-medium text-foreground">
                          {new Date(data.imageMetadata.timestamp).toLocaleString()}
                        </span>
                      </div>
                    )}
                    {data.imageMetadata.gpsCoordinates && (
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">GPS Coordinates:</span>
                        <span className="font-medium text-foreground font-mono text-xs">
                          {data.imageMetadata.gpsCoordinates}
                        </span>
                      </div>
                    )}
                    {data.imageMetadata.deviceId && (
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Device ID:</span>
                        <span className="font-medium text-foreground font-mono text-xs">
                          {data.imageMetadata.deviceId}
                        </span>
                      </div>
                    )}
                    {data.imageIpfsHash && (
                      <div className="pt-2">
                        <span className="text-muted-foreground block mb-1">IPFS Hash:</span>
                        <div className="bg-muted p-2 rounded-md font-mono text-xs break-all flex items-center justify-between gap-2">
                          <span>{data.imageIpfsHash}</span>
                          <a 
                            href={`https://ipfs.io/ipfs/${data.imageIpfsHash}`}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-primary hover:underline shrink-0"
                          >
                            <ExternalLink className="w-3 h-3" />
                          </a>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
                <Separator />
              </>
            )}

            {/* Blockchain Proof Section */}
            {(data.hcsSequenceNumber || data.hcsTopicId) && (
              <>
                <div className="space-y-3">
                  <h3 className="text-sm font-semibold text-foreground uppercase tracking-wider">Blockchain Proof</h3>
                  <div className="space-y-2 text-sm">
                    {data.hcsTopicId && (
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">HCS Topic ID:</span>
                        <span className="font-medium text-foreground font-mono text-xs">
                          {data.hcsTopicId}
                        </span>
                      </div>
                    )}
                    {data.hcsSequenceNumber && (
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Sequence Number:</span>
                        <span className="font-medium text-foreground">
                          #{data.hcsSequenceNumber}
                        </span>
                      </div>
                    )}
                    <div className="pt-2">
                      <a 
                        href={`https://hashscan.io/testnet/topic/${data.hcsTopicId}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-primary hover:underline text-xs flex items-center gap-1"
                      >
                        View on HashScan
                        <ExternalLink className="w-3 h-3" />
                      </a>
                    </div>
                    <p className="text-xs text-muted-foreground pt-2">
                      This verification has been permanently logged to the Hedera Consensus Service, 
                      providing immutable proof of the meter reading and timestamp.
                    </p>
                  </div>
                </div>
                <Separator />
              </>
            )}

            {/* Billing Breakdown Section */}
            {data.bill && data.bill.breakdown && (
              <div className="space-y-3">
                <h3 className="text-sm font-semibold text-foreground uppercase tracking-wider">Billing Breakdown</h3>
                <div className="space-y-2">
                  {data.bill.breakdown.map((item, index) => (
                    <div key={index} className="flex justify-between text-sm">
                      <span className="text-muted-foreground">{item.description}</span>
                      <span className="font-medium text-foreground">
                        {formatCurrency(item.amount, data.bill!.currency)}
                      </span>
                    </div>
                  ))}
                  <Separator className="my-2" />
                  <div className="flex justify-between text-base font-semibold">
                    <span className="text-foreground">Total</span>
                    <span className="text-primary">
                      {formatCurrency(data.bill.total, data.bill.currency)}
                    </span>
                  </div>
                </div>
              </div>
            )}
          </div>
        </DialogContent>
      </Dialog>

      {/* Action Buttons */}
      <div className="grid grid-cols-2 gap-3 pt-2">
        {onRetry && (
          <Button
            variant="outline"
            size="lg"
            onClick={onRetry}
            className="w-full"
          >
            <RotateCcw className="w-4 h-4 mr-2" />
            Rescan
          </Button>
        )}
        
        {onPay && data.bill && data.status === 'VERIFIED' && (
          <Button
            size="lg"
            onClick={onPay}
            className="w-full"
          >
            Pay {formatCurrency(data.bill.total, data.bill.currency)}
          </Button>
        )}
      </div>

      {/* Blockchain Proof */}
      {data.hcsSequenceNumber && (
        <div className="text-center pt-2">
          <p className="text-xs text-muted-foreground">
            Verification logged to Hedera
            {data.hcsTopicId && ` • Topic ${data.hcsTopicId}`}
            {data.hcsSequenceNumber && ` • Sequence #${data.hcsSequenceNumber}`}
          </p>
        </div>
      )}
    </motion.div>
  );
}
