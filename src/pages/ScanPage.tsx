import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Zap, Shield, Camera as CameraIcon } from "lucide-react";
import AppHeader from "@/components/AppHeader";
import { Camera } from "@/components/Camera";
import { VerificationResult, VerificationResultData } from "@/components/VerificationResult";
import { verificationApi } from "@/lib/api";
import { useToast } from "@/hooks/use-toast";

const ScanPage = () => {
  const [phase, setPhase] = useState<"ready" | "scanning" | "result">("ready");
  const [capturedImage, setCapturedImage] = useState<File | null>(null);
  const [verificationResult, setVerificationResult] = useState<VerificationResultData | null>(null);
  const { toast } = useToast();

  const handleCapture = async (file: File) => {
    setCapturedImage(file);
    setPhase("scanning");
    
    try {
      // Call the verification API
      const result = await verificationApi.scanMeter(file);
      
      // Transform API response to VerificationResultData format
      const verificationData: VerificationResultData = {
        reading: result.reading,
        previousReading: result.previousReading,
        consumption: result.consumption,
        confidence: result.confidence,
        status: result.status || 'VERIFIED',
        fraudScore: result.fraudScore || 0,
        fraudFlags: result.fraudFlags,
        bill: result.bill ? {
          baseCharge: result.bill.baseCharge,
          taxes: result.bill.taxes,
          serviceCharge: result.bill.serviceCharge,
          total: result.bill.total,
          currency: result.bill.currency,
          breakdown: result.bill.breakdown
        } : undefined,
        hcsSequenceNumber: result.hcsSequenceNumber,
        hcsTopicId: result.hcsTopicId,
        utilityReading: result.utilityReading
      };
      
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
    setPhase("ready");
  };

  return (
    <div className="min-h-screen bg-background pb-24">
      <AppHeader title="Verify Meter Reading" />

      <div className="px-5 py-6">
        <AnimatePresence mode="wait">
          {/* Ready State - Camera Capture */}
          {phase === "ready" && (
            <motion.div
              key="ready"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="space-y-6"
            >
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
                onPay={() => {
                  // TODO: Implement payment flow
                  toast({
                    title: "Payment Flow",
                    description: "Payment functionality will be implemented in Week 4",
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
