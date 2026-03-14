/**
 * Smart Meter Verification Component
 * 
 * Displays consumption details with cryptographic signature verification.
 * Features:
 * - Consumption data display
 * - Signature status (verified/invalid)
 * - Manual signature verification
 * - Verification details (hash, algorithm)
 * - Consumption history list
 * 
 * Requirements: US-17, FR-9.10
 */

import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { Alert, AlertDescription } from '@/components/ui/alert';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import {
  Shield,
  CheckCircle,
  XCircle,
  Loader2,
  Eye,
  Zap,
  Clock,
  Hash,
  Key,
  ExternalLink,
  AlertCircle,
} from 'lucide-react';
import { toast } from 'sonner';

export interface ConsumptionLog {
  id: string;
  meter_id: string;
  consumption_kwh: number;
  reading_before: number;
  reading_after: number;
  timestamp: number;
  signature: string;
  public_key: string;
  signature_valid: boolean;
  units_deducted?: number;
  units_remaining?: number;
  token_id?: string;
  hcs_topic_id?: string;
  hcs_sequence_number?: number;
  created_at: string;
}

export interface VerificationDetails {
  valid: boolean;
  message_hash: string;
  algorithm: string;
}

interface SmartMeterVerificationProps {
  consumptionLog: ConsumptionLog;
  onVerify?: (result: VerificationDetails) => void;
}

export function SmartMeterVerification({
  consumptionLog,
  onVerify,
}: SmartMeterVerificationProps) {
  const [verifying, setVerifying] = useState(false);
  const [verificationResult, setVerificationResult] = useState<VerificationDetails | null>(null);
  const [isDetailsOpen, setIsDetailsOpen] = useState(false);

  const verifySignature = async () => {
    setVerifying(true);
    
    try {
      toast.info('🔐 Verifying Signature...', {
        description: 'Checking cryptographic proof of consumption data...',
        duration: 3000,
        className: 'bg-blue-50 border-blue-500',
      });

      const response = await fetch('/api/smart-meter/verify-signature', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          meter_id: consumptionLog.meter_id,
          consumption_kwh: consumptionLog.consumption_kwh,
          timestamp: consumptionLog.timestamp,
          signature: consumptionLog.signature,
          public_key: consumptionLog.public_key,
        }),
      });

      if (!response.ok) {
        throw new Error('Verification request failed');
      }

      const data: VerificationDetails = await response.json();
      setVerificationResult(data);

      if (data.valid) {
        toast.success('✓ Signature Verified', {
          description: 'Consumption data is authentic and tamper-proof.',
          duration: 4000,
          className: 'bg-green-50 border-green-500',
        });
      } else {
        toast.error('❌ Invalid Signature', {
          description: 'Signature verification failed. Data may be tampered.',
          duration: 5000,
          className: 'bg-red-50 border-red-500',
        });
      }

      if (onVerify) {
        onVerify(data);
      }
    } catch (error) {
      console.error('Verification failed:', error);
      toast.error('⚠️ Verification Error', {
        description: error instanceof Error ? error.message : 'Failed to verify signature',
        duration: 4000,
        className: 'bg-red-50 border-red-500',
      });
    } finally {
      setVerifying(false);
    }
  };

  const formatTimestamp = (timestamp: number) => {
    return new Date(timestamp * 1000).toLocaleString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    });
  };

  const truncateHash = (hash: string, length: number = 16) => {
    if (hash.length <= length) return hash;
    return `${hash.substring(0, length)}...`;
  };

  const getSignatureStatusConfig = () => {
    if (consumptionLog.signature_valid) {
      return {
        icon: CheckCircle,
        color: 'text-green-600',
        bgColor: 'bg-green-50',
        borderColor: 'border-green-500',
        badge: 'VERIFIED ✓',
        badgeVariant: 'default' as const,
      };
    } else {
      return {
        icon: XCircle,
        color: 'text-red-600',
        bgColor: 'bg-red-50',
        borderColor: 'border-red-500',
        badge: 'INVALID ❌',
        badgeVariant: 'destructive' as const,
      };
    }
  };

  const statusConfig = getSignatureStatusConfig();
  const StatusIcon = statusConfig.icon;

  return (
    <Card className="w-full">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className={`p-2 ${statusConfig.bgColor} rounded-lg`}>
              <Shield className={`w-6 h-6 ${statusConfig.color}`} />
            </div>
            <div>
              <CardTitle className="text-xl">Consumption Verification</CardTitle>
              <CardDescription>
                Cryptographically signed meter reading
              </CardDescription>
            </div>
          </div>
          <Badge variant={statusConfig.badgeVariant} className="text-sm">
            {statusConfig.badge}
          </Badge>
        </div>
      </CardHeader>

      <CardContent className="space-y-6">
        {/* Consumption Details */}
        <div className={`border-2 ${statusConfig.borderColor} ${statusConfig.bgColor} rounded-lg p-4 space-y-3`}>
          <div className="flex items-center gap-2 mb-2">
            <StatusIcon className={`w-5 h-5 ${statusConfig.color}`} />
            <h3 className="font-semibold text-base">Consumption Data</h3>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="text-xs text-muted-foreground mb-1">Consumption</p>
              <div className="flex items-center gap-2">
                <Zap className="w-4 h-4 text-purple-600" />
                <p className="text-lg font-bold">{consumptionLog.consumption_kwh.toFixed(2)} kWh</p>
              </div>
            </div>

            <div>
              <p className="text-xs text-muted-foreground mb-1">Timestamp</p>
              <div className="flex items-center gap-2">
                <Clock className="w-4 h-4 text-blue-600" />
                <p className="text-sm font-medium">
                  {formatTimestamp(consumptionLog.timestamp)}
                </p>
              </div>
            </div>
          </div>

          <Separator />

          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <p className="text-xs text-muted-foreground mb-1">Reading Before</p>
              <p className="font-medium">{consumptionLog.reading_before.toFixed(2)} kWh</p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground mb-1">Reading After</p>
              <p className="font-medium">{consumptionLog.reading_after.toFixed(2)} kWh</p>
            </div>
          </div>

          {consumptionLog.token_id && (
            <>
              <Separator />
              <div className="space-y-2">
                <p className="text-xs text-muted-foreground">Prepaid Token</p>
                <div className="flex items-center justify-between">
                  <p className="text-sm font-mono bg-white px-2 py-1 rounded border">
                    {consumptionLog.token_id}
                  </p>
                  {consumptionLog.units_remaining !== undefined && (
                    <Badge variant="secondary">
                      {consumptionLog.units_remaining.toFixed(2)} kWh remaining
                    </Badge>
                  )}
                </div>
              </div>
            </>
          )}
        </div>

        {/* Signature Information */}
        <div className="space-y-3">
          <h3 className="font-semibold text-sm text-muted-foreground uppercase tracking-wider">
            Cryptographic Signature
          </h3>

          <div className="space-y-2">
            <div className="flex items-start gap-2">
              <Hash className="w-4 h-4 text-muted-foreground mt-1 shrink-0" />
              <div className="flex-1 min-w-0">
                <p className="text-xs text-muted-foreground mb-1">Signature</p>
                <p className="text-xs font-mono bg-muted px-2 py-1 rounded break-all">
                  {truncateHash(consumptionLog.signature, 32)}
                </p>
              </div>
            </div>

            <div className="flex items-start gap-2">
              <Key className="w-4 h-4 text-muted-foreground mt-1 shrink-0" />
              <div className="flex-1 min-w-0">
                <p className="text-xs text-muted-foreground mb-1">Public Key</p>
                <p className="text-xs font-mono bg-muted px-2 py-1 rounded break-all">
                  {truncateHash(consumptionLog.public_key, 32)}
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Verification Result */}
        {verificationResult && (
          <Alert className={verificationResult.valid ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200'}>
            {verificationResult.valid ? (
              <CheckCircle className="h-4 w-4 text-green-600" />
            ) : (
              <AlertCircle className="h-4 w-4 text-red-600" />
            )}
            <AlertDescription>
              <div className="space-y-2">
                <p className={`font-semibold ${verificationResult.valid ? 'text-green-800' : 'text-red-800'}`}>
                  {verificationResult.valid ? 'Signature Valid' : 'Signature Invalid'}
                </p>
                <div className="text-xs space-y-1">
                  <p className="text-muted-foreground">
                    <span className="font-medium">Algorithm:</span> {verificationResult.algorithm}
                  </p>
                  <p className="text-muted-foreground">
                    <span className="font-medium">Message Hash:</span>{' '}
                    <span className="font-mono">{truncateHash(verificationResult.message_hash, 24)}</span>
                  </p>
                </div>
              </div>
            </AlertDescription>
          </Alert>
        )}

        {/* Action Buttons */}
        <div className="flex gap-3">
          <Button
            onClick={verifySignature}
            disabled={verifying}
            variant={consumptionLog.signature_valid ? 'outline' : 'default'}
            className="flex-1"
            size="lg"
          >
            {verifying ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Verifying...
              </>
            ) : (
              <>
                <Shield className="w-4 h-4 mr-2" />
                {consumptionLog.signature_valid ? 'Re-verify' : 'Verify Signature'}
              </>
            )}
          </Button>

          <Dialog open={isDetailsOpen} onOpenChange={setIsDetailsOpen}>
            <DialogTrigger asChild>
              <Button variant="outline" size="lg">
                <Eye className="w-4 h-4 mr-2" />
                Details
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
              <DialogHeader>
                <DialogTitle>Verification Details</DialogTitle>
                <DialogDescription>
                  Complete cryptographic verification information for this consumption event
                </DialogDescription>
              </DialogHeader>

              <div className="space-y-6 mt-4">
                {/* Consumption Information */}
                <div className="space-y-3">
                  <h3 className="text-sm font-semibold text-foreground uppercase tracking-wider">
                    Consumption Information
                  </h3>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Meter ID:</span>
                      <span className="font-mono text-xs">{consumptionLog.meter_id}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Consumption:</span>
                      <span className="font-semibold">{consumptionLog.consumption_kwh.toFixed(2)} kWh</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Reading Before:</span>
                      <span>{consumptionLog.reading_before.toFixed(2)} kWh</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Reading After:</span>
                      <span>{consumptionLog.reading_after.toFixed(2)} kWh</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Timestamp:</span>
                      <span>{formatTimestamp(consumptionLog.timestamp)}</span>
                    </div>
                  </div>
                </div>

                <Separator />

                {/* Cryptographic Details */}
                <div className="space-y-3">
                  <h3 className="text-sm font-semibold text-foreground uppercase tracking-wider">
                    Cryptographic Details
                  </h3>
                  <div className="space-y-3 text-sm">
                    <div>
                      <span className="text-muted-foreground block mb-1">Signature:</span>
                      <div className="bg-muted p-3 rounded-md font-mono text-xs break-all">
                        {consumptionLog.signature}
                      </div>
                    </div>
                    <div>
                      <span className="text-muted-foreground block mb-1">Public Key:</span>
                      <div className="bg-muted p-3 rounded-md font-mono text-xs break-all">
                        {consumptionLog.public_key}
                      </div>
                    </div>
                    {verificationResult && (
                      <div>
                        <span className="text-muted-foreground block mb-1">Message Hash:</span>
                        <div className="bg-muted p-3 rounded-md font-mono text-xs break-all">
                          {verificationResult.message_hash}
                        </div>
                      </div>
                    )}
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Algorithm:</span>
                      <span className="font-semibold">
                        {verificationResult?.algorithm || 'ED25519'}
                      </span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-muted-foreground">Verification Status:</span>
                      <Badge variant={consumptionLog.signature_valid ? 'default' : 'destructive'}>
                        {consumptionLog.signature_valid ? 'VALID ✓' : 'INVALID ❌'}
                      </Badge>
                    </div>
                  </div>
                </div>

                <Separator />

                {/* Blockchain Proof */}
                {(consumptionLog.hcs_topic_id || consumptionLog.hcs_sequence_number) && (
                  <>
                    <div className="space-y-3">
                      <h3 className="text-sm font-semibold text-foreground uppercase tracking-wider">
                        Blockchain Proof
                      </h3>
                      <div className="space-y-2 text-sm">
                        {consumptionLog.hcs_topic_id && (
                          <div className="flex justify-between">
                            <span className="text-muted-foreground">HCS Topic ID:</span>
                            <span className="font-mono text-xs">{consumptionLog.hcs_topic_id}</span>
                          </div>
                        )}
                        {consumptionLog.hcs_sequence_number && (
                          <div className="flex justify-between">
                            <span className="text-muted-foreground">Sequence Number:</span>
                            <span className="font-semibold">#{consumptionLog.hcs_sequence_number}</span>
                          </div>
                        )}
                        {consumptionLog.hcs_topic_id && (
                          <div className="pt-2">
                            <a
                              href={`https://hashscan.io/testnet/topic/${consumptionLog.hcs_topic_id}`}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-primary hover:underline text-xs flex items-center gap-1"
                            >
                              View on HashScan
                              <ExternalLink className="w-3 h-3" />
                            </a>
                          </div>
                        )}
                        <p className="text-xs text-muted-foreground pt-2">
                          This consumption event has been permanently logged to the Hedera Consensus Service,
                          providing immutable proof of the meter reading and cryptographic signature.
                        </p>
                      </div>
                    </div>
                    <Separator />
                  </>
                )}

                {/* Token Information */}
                {consumptionLog.token_id && (
                  <div className="space-y-3">
                    <h3 className="text-sm font-semibold text-foreground uppercase tracking-wider">
                      Prepaid Token
                    </h3>
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Token ID:</span>
                        <span className="font-mono text-xs">{consumptionLog.token_id}</span>
                      </div>
                      {consumptionLog.units_deducted !== undefined && (
                        <div className="flex justify-between">
                          <span className="text-muted-foreground">Units Deducted:</span>
                          <span className="font-semibold">{consumptionLog.units_deducted.toFixed(2)} kWh</span>
                        </div>
                      )}
                      {consumptionLog.units_remaining !== undefined && (
                        <div className="flex justify-between">
                          <span className="text-muted-foreground">Units Remaining:</span>
                          <span className="font-semibold text-purple-600">
                            {consumptionLog.units_remaining.toFixed(2)} kWh
                          </span>
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            </DialogContent>
          </Dialog>
        </div>

        {/* Info Footer */}
        <div className="pt-2">
          <p className="text-xs text-muted-foreground text-center">
            {consumptionLog.hcs_sequence_number ? (
              <>
                Logged to Hedera HCS • Topic {consumptionLog.hcs_topic_id} • Sequence #{consumptionLog.hcs_sequence_number}
              </>
            ) : (
              'Cryptographic signature ensures data authenticity and tamper-proof verification'
            )}
          </p>
        </div>
      </CardContent>
    </Card>
  );
}
