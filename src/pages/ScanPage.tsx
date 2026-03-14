import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Zap, Shield, Camera as CameraIcon, AlertCircle, Wallet } from "lucide-react";
import AppHeader from "@/components/AppHeader";
import { Camera } from "@/components/Camera";
import { VerificationResult, VerificationResultData } from "@/components/VerificationResult";
import WalletConnect from "@/components/WalletConnect";
import { PaymentReceipt, PaymentReceiptData } from "@/components/PaymentReceipt";
import { verificationApi, paymentsApi } from "@/lib/api";
import { useToast } from "@/hooks/use-toast";
import { useMeters } from "@/hooks/useMeters";
import { useAuth } from "@/hooks/useAuth";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { walletService, WalletConnection } from "@/services/wallet-integration.service";
import { transactionVerificationService } from "@/services/transaction-verification.service";

const ScanPage = () => {
  const [phase, setPhase] = useState<"ready" | "scanning" | "result" | "receipt">("ready");
  const [capturedImage, setCapturedImage] = useState<File | null>(null);
  const [verificationResult, setVerificationResult] = useState<VerificationResultData | null>(null);
  const [paymentReceipt, setPaymentReceipt] = useState<PaymentReceiptData | null>(null);
  const [selectedMeterId, setSelectedMeterId] = useState<string>("");
  const [billId, setBillId] = useState<string | null>(null);
  const [isProcessingPayment, setIsProcessingPayment] = useState(false);
  const [walletConnection, setWalletConnection] = useState<WalletConnection | null>(null);
  const [showWalletConnect, setShowWalletConnect] = useState(false);
  const { toast } = useToast();
  const { user } = useAuth();
  const { meters, isLoading: metersLoading } = useMeters();

  // Auto-select meter if only one available
  useEffect(() => {
    if (meters && meters.length === 1 && !selectedMeterId) {
      setSelectedMeterId(meters[0].id);
    }
  }, [meters, selectedMeterId]);

  // Check for existing wallet connection
  useEffect(() => {
    const connection = walletService.getCurrentConnection();
    if (connection) {
      setWalletConnection(connection);
    }
  }, []);

  const handleCapture = async (file: File) => {
    if (!selectedMeterId) {
      toast({
        title: "No Meter Selected",
        description: "Please select a meter before scanning.",
        variant: "destructive",
      });
      return;
    }

    setCapturedImage(file);
    setPhase("scanning");
    
    try {
      // Call the verification API with meter ID
      const result = await verificationApi.scanMeter(selectedMeterId, file);
      
      // Helper function to safely convert to number
      const toNumber = (value: any): number => {
        if (typeof value === 'number') return value;
        if (typeof value === 'string') return parseFloat(value);
        return 0;
      };
      
      // Transform API response to VerificationResultData format
      const verificationData: VerificationResultData = {
        reading: toNumber(result.reading_value),
        previousReading: result.previous_reading ? toNumber(result.previous_reading) : undefined,
        consumption: result.consumption_kwh ? toNumber(result.consumption_kwh) : undefined,
        confidence: toNumber(result.confidence),
        status: result.status,
        fraudScore: toNumber(result.fraud_score),
        fraudFlags: result.fraud_flags ? Object.keys(result.fraud_flags) : undefined,
        bill: result.bill ? {
          baseCharge: 0, // Not available in BillSummary
          taxes: 0, // Not available in BillSummary
          serviceCharge: 0, // Not available in BillSummary
          total: toNumber(result.bill.total_fiat),
          currency: result.bill.currency,
          breakdown: [] // Not available in BillSummary
        } : undefined,
        hcsSequenceNumber: result.hcs_sequence_number,
        hcsTopicId: result.hcs_topic_id,
        utilityReading: result.utility_reading ? toNumber(result.utility_reading) : undefined
      };
      
      // Store bill ID for payment processing
      if (result.bill) {
        setBillId(result.bill.id);
      }
      
      setVerificationResult(verificationData);
      setPhase("result");
    } catch (error) {
      console.error("Verification failed:", error);
      toast({
        title: "Verification Failed",
        description: "Unable to process the meter image. Please try again.",
        variant: "destructive",
      });
      setPhase("ready");
    }
  };

  const handleRetry = () => {
    setCapturedImage(null);
    setVerificationResult(null);
    setPaymentReceipt(null);
    setBillId(null);
    setPhase("ready");
  };

  const handlePayment = async () => {
    if (!billId) {
      toast({
        title: "No Bill Available",
        description: "No bill was generated for this verification.",
        variant: "destructive",
      });
      return;
    }

    if (!walletConnection) {
      setShowWalletConnect(true);
      toast({
        title: "Wallet Required",
        description: "Please connect your Hedera wallet to make payments.",
        variant: "destructive",
      });
      return;
    }

    setIsProcessingPayment(true);

    try {
      // Step 1: Prepare payment
      const paymentPrep = await paymentsApi.prepare(billId);
      
      toast({
        title: "Payment Prepared",
        description: `Amount: ${paymentPrep.transaction.amount_hbar} HBAR (${paymentPrep.bill.total_fiat} ${paymentPrep.bill.currency})`,
      });

      // Step 2: Send transaction through wallet
      const transactionResult = await walletService.sendTransaction({
        to: paymentPrep.transaction.to,
        amount: paymentPrep.transaction.amount_hbar,
        memo: paymentPrep.transaction.memo,
      });
      
      toast({
        title: "Transaction Sent",
        description: `Transaction ID: ${transactionResult.transactionId}. Waiting for confirmation...`,
      });

      // Step 2.5: Verify transaction on Hedera network
      const verificationResult = await transactionVerificationService.pollTransactionStatus(
        transactionResult.transactionId,
        30, // 30 attempts
        3000 // 3 second intervals
      );

      if (verificationResult.status !== 'success') {
        throw new Error(`Transaction verification failed: ${verificationResult.result || 'Transaction not confirmed'}`);
      }

      // Verify payment details match
      const paymentVerification = await transactionVerificationService.verifyPaymentTransaction(
        transactionResult.transactionId,
        paymentPrep.transaction.amount_hbar,
        paymentPrep.transaction.to,
        walletConnection.accountId
      );

      if (!paymentVerification.isValid) {
        throw new Error(`Payment verification failed: ${paymentVerification.errors.join(', ')}`);
      }

      // Step 3: Confirm payment with backend
      const confirmation = await paymentsApi.confirm(billId, transactionResult.transactionId);
      
      // Create receipt data
      const receiptData: PaymentReceiptData = {
        id: confirmation.payment.id,
        billId: billId,
        transactionId: transactionResult.transactionId,
        amount: {
          hbar: paymentPrep.transaction.amount_hbar,
          fiat: paymentPrep.bill.total_fiat,
          currency: paymentPrep.bill.currency,
        },
        exchangeRate: paymentPrep.exchange_rate.hbar_price,
        timestamp: new Date().toISOString(),
        consensusTimestamp: verificationResult.consensusTimestamp,
        status: 'confirmed',
        explorerUrl: transactionResult.explorerUrl,
        meter: {
          id: meters?.find(m => m.id === selectedMeterId)?.meter_id || selectedMeterId,
          address: meters?.find(m => m.id === selectedMeterId)?.address,
        },
        consumption: {
          kwh: paymentPrep.bill.consumption_kwh,
          period: 'Current billing period',
        },
      };

      setPaymentReceipt(receiptData);
      setPhase("receipt");
      
      toast({
        title: "Payment Successful",
        description: `Payment confirmed! View receipt for details.`,
      });

    } catch (error) {
      console.error("Payment failed:", error);
      toast({
        title: "Payment Failed",
        description: error instanceof Error ? error.message : "Unable to process payment. Please try again.",
        variant: "destructive",
      });
    } finally {
      setIsProcessingPayment(false);
    }
  };

  const handleWalletConnect = (connection: WalletConnection) => {
    setWalletConnection(connection);
    setShowWalletConnect(false);
  };

  const handleWalletDisconnect = () => {
    setWalletConnection(null);
  };

  // Show loading state while fetching meters
  if (metersLoading) {
    return (
      <div className="min-h-screen bg-background pb-24">
        <AppHeader title="Verify Meter Reading" />
        <div className="px-5 py-6 flex items-center justify-center">
          <div className="text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-accent mx-auto mb-4"></div>
            <p className="text-muted-foreground">Loading your meters...</p>
          </div>
        </div>
      </div>
    );
  }

  // Show error if no meters available
  if (!meters || meters.length === 0) {
    return (
      <div className="min-h-screen bg-background pb-24">
        <AppHeader title="Verify Meter Reading" />
        <div className="px-5 py-6">
          <Card>
            <CardContent className="p-6 text-center">
              <AlertCircle className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
              <h3 className="text-lg font-semibold mb-2">No Meters Found</h3>
              <p className="text-muted-foreground mb-4">
                You need to register a meter before you can verify readings.
              </p>
              <Button onClick={() => window.history.back()}>
                Go Back
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background pb-24">
      <AppHeader title="Verify Meter Reading" />

      <div className="px-5 py-6">
        <AnimatePresence mode="wait">
          {/* Wallet Connection Modal */}
          {showWalletConnect && (
            <motion.div
              key="wallet-connect"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="space-y-4"
            >
              <WalletConnect
                onConnect={handleWalletConnect}
                onDisconnect={handleWalletDisconnect}
              />
              <Button
                variant="outline"
                onClick={() => setShowWalletConnect(false)}
                className="w-full"
              >
                Cancel
              </Button>
            </motion.div>
          )}

          {/* Meter Selection (if multiple meters) */}
          {!selectedMeterId && meters.length > 1 && !showWalletConnect && (
            <motion.div
              key="meter-selection"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="space-y-4"
            >
              <Card>
                <CardHeader>
                  <CardTitle>Select Meter to Verify</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  {meters.map((meter) => (
                    <Card
                      key={meter.id}
                      className="cursor-pointer hover:shadow-lg hover:border-accent transition-all"
                      onClick={() => setSelectedMeterId(meter.id)}
                    >
                      <CardContent className="p-4">
                        <div className="flex items-center justify-between">
                          <div>
                            <div className="flex items-center gap-2 mb-1">
                              <h3 className="font-semibold text-lg">{meter.meter_id}</h3>
                              {meter.is_primary && (
                                <Badge className="bg-accent text-white">Primary</Badge>
                              )}
                            </div>
                            <p className="text-sm text-muted-foreground">
                              {meter.utility_provider} • {meter.state_province}
                            </p>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </CardContent>
              </Card>
            </motion.div>
          )}

          {/* Ready State - Camera Capture */}
          {phase === "ready" && selectedMeterId && !showWalletConnect && (
            <motion.div
              key="ready"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="space-y-6"
            >
              {/* Wallet Status */}
              {walletConnection && (
                <Card className="border-green-200 bg-green-50">
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Wallet className="w-4 h-4 text-green-600" />
                        <span className="text-sm font-medium text-green-900">
                          Wallet Connected
                        </span>
                      </div>
                      <Badge variant="default" className="bg-green-600">
                        {walletConnection.provider}
                      </Badge>
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Selected Meter Info */}
              {meters.length > 1 && (
                <Card>
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm text-muted-foreground">Selected Meter</p>
                        <p className="font-semibold">
                          {meters.find(m => m.id === selectedMeterId)?.meter_id}
                        </p>
                      </div>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => setSelectedMeterId('')}
                        className="text-accent hover:text-accent/80"
                      >
                        Change
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Instructions Card */}
              <div className="glass-card p-4 space-y-3">
                <div className="flex items-center gap-2">
                  <CameraIcon className="w-5 h-5 text-accent" />
                  <h3 className="font-semibold text-foreground">Capture Your Meter</h3>
                </div>
                <ul className="space-y-2 text-sm text-muted-foreground">
                  <li className="flex items-start gap-2">
                    <span className="text-accent mt-0.5">•</span>
                    <span>Ensure good lighting and clear visibility of the meter display</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-accent mt-0.5">•</span>
                    <span>Align the meter within the guide frame</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-accent mt-0.5">•</span>
                    <span>Hold steady and capture when ready</span>
                  </li>
                </ul>
              </div>

              {/* Camera Component */}
              <Camera onCapture={handleCapture} />
            </motion.div>
          )}

          {/* Processing State */}
          {phase === "scanning" && (
            <motion.div
              key="scanning"
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0 }}
              className="flex flex-col items-center justify-center py-20 space-y-6"
            >
              {/* Animated Spinner */}
              <div className="relative w-24 h-24">
                <div className="absolute inset-0 rounded-full border-4 border-accent/20" />
                <div className="absolute inset-0 rounded-full border-4 border-transparent border-t-accent animate-spin" />
                <Zap className="absolute inset-0 m-auto w-10 h-10 text-accent animate-pulse" />
              </div>

              {/* Processing Steps */}
              <div className="text-center space-y-4">
                <p className="text-xl font-semibold text-foreground">AI Verification in Progress</p>
                <div className="space-y-2 text-sm text-muted-foreground">
                  <p className="flex items-center justify-center gap-2">
                    <span className="w-1.5 h-1.5 rounded-full bg-accent animate-pulse" />
                    Extracting meter reading...
                  </p>
                  <p className="flex items-center justify-center gap-2">
                    <span className="w-1.5 h-1.5 rounded-full bg-accent/60" />
                    Running fraud detection...
                  </p>
                  <p className="flex items-center justify-center gap-2">
                    <span className="w-1.5 h-1.5 rounded-full bg-accent/40" />
                    Calculating bill amount...
                  </p>
                </div>
              </div>

              {/* Security Badge */}
              <div className="flex items-center gap-2 px-4 py-2 rounded-full bg-accent/10 border border-accent/20">
                <Shield className="w-4 h-4 text-accent" />
                <span className="text-xs font-medium text-accent">Blockchain Verified</span>
              </div>
            </motion.div>
          )}

          {/* Verification Result */}
          {phase === "result" && verificationResult && (
            <motion.div
              key="result"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
            >
              <VerificationResult 
                data={verificationResult}
                onRetry={handleRetry}
                onPay={isProcessingPayment ? undefined : handlePayment}
              />
            </motion.div>
          )}
          {/* Payment Receipt */}
          {phase === "receipt" && paymentReceipt && (
            <motion.div
              key="receipt"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
            >
              <PaymentReceipt 
                data={paymentReceipt}
                onClose={handleRetry}
                onDownload={() => {
                  toast({
                    title: "Download Receipt",
                    description: "PDF download functionality will be implemented soon.",
                  });
                }}
              />
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
};

export default ScanPage;
