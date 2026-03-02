/**
 * Payment Confirmation Modal
 * 
 * Displays transaction confirmation details after successful HashPack payment
 * Shows transaction ID, HBAR amount, fiat equivalent, exchange rate, timestamp,
 * and link to Hedera Explorer (HashScan)
 */

import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { Badge } from "@/components/ui/badge";
import { 
  CheckCircle2, 
  ExternalLink, 
  Download, 
  Receipt, 
  Clock, 
  TrendingUp,
  FileText,
  Copy,
  Check
} from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";

export interface PaymentConfirmationData {
  // Transaction details
  transactionId: string;
  consensusTimestamp: string;
  
  // Payment amounts
  amountHbar: number;
  amountFiat: number;
  currency: string;
  
  // Exchange rate
  exchangeRate: number;
  exchangeRateSource: string;
  
  // Bill details
  billId: string;
  consumptionKwh?: number;
  
  // Receipt
  receiptUrl?: string;
}

interface PaymentConfirmationModalProps {
  isOpen: boolean;
  onClose: () => void;
  data: PaymentConfirmationData;
  onDownloadReceipt?: () => void;
  onViewBillDetails?: () => void;
}

export function PaymentConfirmationModal({
  isOpen,
  onClose,
  data,
  onDownloadReceipt,
  onViewBillDetails,
}: PaymentConfirmationModalProps) {
  const [copiedTxId, setCopiedTxId] = useState(false);

  const formatCurrency = (amount: number, currency: string) => {
    const symbols: Record<string, string> = {
      EUR: '€',
      USD: '$',
      INR: '₹',
      BRL: 'R$',
      NGN: '₦',
    };
    return `${symbols[currency] || currency}${amount.toLocaleString(undefined, { 
      minimumFractionDigits: 2, 
      maximumFractionDigits: 2 
    })}`;
  };

  const formatTimestamp = (timestamp: string) => {
    try {
      const date = new Date(timestamp);
      return date.toLocaleString(undefined, {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        timeZoneName: 'short'
      });
    } catch {
      return timestamp;
    }
  };

  const copyTransactionId = async () => {
    try {
      await navigator.clipboard.writeText(data.transactionId);
      setCopiedTxId(true);
      toast.success('Transaction ID copied to clipboard');
      setTimeout(() => setCopiedTxId(false), 2000);
    } catch (error) {
      toast.error('Failed to copy transaction ID');
    }
  };

  const openHashScan = () => {
    const url = `https://hashscan.io/testnet/transaction/${data.transactionId}`;
    window.open(url, '_blank', 'noopener,noreferrer');
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <div className="flex items-center justify-center mb-4">
            <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center">
              <CheckCircle2 className="w-10 h-10 text-green-600" />
            </div>
          </div>
          <DialogTitle className="text-2xl text-center">
            Payment Successful!
          </DialogTitle>
          <DialogDescription className="text-center text-base">
            Your bill payment has been confirmed on the Hedera network
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 mt-4">
          {/* Transaction ID Card */}
          <Card className="border-2 border-green-200 bg-green-50">
            <CardContent className="pt-6">
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-green-900">Transaction ID</span>
                  <Badge className="bg-green-600 text-white">
                    Confirmed
                  </Badge>
                </div>
                <div className="flex items-center gap-2 bg-white rounded-lg p-3 border border-green-200">
                  <code className="flex-1 text-sm font-mono text-gray-900 break-all">
                    {data.transactionId}
                  </code>
                  <button
                    onClick={copyTransactionId}
                    className="p-2 hover:bg-gray-100 rounded transition-colors"
                    title="Copy transaction ID"
                  >
                    {copiedTxId ? (
                      <Check className="w-4 h-4 text-green-600" />
                    ) : (
                      <Copy className="w-4 h-4 text-gray-600" />
                    )}
                  </button>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Payment Details */}
          <Card>
            <CardContent className="pt-6">
              <div className="space-y-4">
                <h3 className="text-sm font-semibold text-foreground uppercase tracking-wider flex items-center gap-2">
                  <Receipt className="w-4 h-4" />
                  Payment Details
                </h3>

                <Separator />

                {/* HBAR Amount */}
                <div className="flex justify-between items-center">
                  <span className="text-sm text-muted-foreground">HBAR Amount</span>
                  <span className="text-lg font-bold text-purple-900">
                    {data.amountHbar.toLocaleString(undefined, { 
                      minimumFractionDigits: 2, 
                      maximumFractionDigits: 8 
                    })} ℏ
                  </span>
                </div>

                {/* Fiat Equivalent */}
                <div className="flex justify-between items-center">
                  <span className="text-sm text-muted-foreground">Fiat Equivalent</span>
                  <span className="text-lg font-bold text-foreground">
                    {formatCurrency(data.amountFiat, data.currency)}
                  </span>
                </div>

                <Separator />

                {/* Exchange Rate */}
                <div className="bg-muted/50 rounded-lg p-3 space-y-2">
                  <div className="flex items-center gap-2 mb-2">
                    <TrendingUp className="w-4 h-4 text-muted-foreground" />
                    <span className="text-xs font-semibold text-foreground uppercase tracking-wider">
                      Exchange Rate
                    </span>
                  </div>
                  <div className="flex justify-between items-center text-sm">
                    <span className="text-muted-foreground">Rate Used</span>
                    <span className="font-medium text-foreground">
                      1 ℏ = {formatCurrency(data.exchangeRate, data.currency)}
                    </span>
                  </div>
                  <div className="flex justify-between items-center text-xs text-muted-foreground">
                    <span>Source</span>
                    <span className="capitalize">{data.exchangeRateSource}</span>
                  </div>
                </div>

                <Separator />

                {/* Timestamp */}
                <div className="flex justify-between items-center">
                  <div className="flex items-center gap-2">
                    <Clock className="w-4 h-4 text-muted-foreground" />
                    <span className="text-sm text-muted-foreground">Consensus Time</span>
                  </div>
                  <span className="text-sm font-medium text-foreground">
                    {formatTimestamp(data.consensusTimestamp)}
                  </span>
                </div>

                {/* Consumption (if available) */}
                {data.consumptionKwh && (
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-muted-foreground">Energy Consumption</span>
                    <span className="text-sm font-medium text-foreground">
                      {data.consumptionKwh.toLocaleString()} kWh
                    </span>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Action Buttons */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {/* View on HashScan */}
            <Button
              onClick={openHashScan}
              variant="outline"
              className="w-full border-2 border-purple-600 text-purple-600 hover:bg-purple-50"
            >
              <ExternalLink className="w-4 h-4 mr-2" />
              View on HashScan
            </Button>

            {/* Download Receipt */}
            {onDownloadReceipt && (
              <Button
                onClick={onDownloadReceipt}
                variant="outline"
                className="w-full border-2 border-blue-600 text-blue-600 hover:bg-blue-50"
              >
                <Download className="w-4 h-4 mr-2" />
                Download Receipt
              </Button>
            )}
          </div>

          {/* View Bill Details */}
          {onViewBillDetails && (
            <Button
              onClick={onViewBillDetails}
              variant="outline"
              className="w-full border-2 border-gray-300 hover:bg-gray-50"
            >
              <FileText className="w-4 h-4 mr-2" />
              View Bill Details
            </Button>
          )}

          {/* Close Button */}
          <Button
            onClick={onClose}
            className="w-full bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700"
            size="lg"
          >
            Done
          </Button>

          {/* Blockchain Info */}
          <div className="text-center text-xs text-muted-foreground space-y-1 pt-2">
            <p>
              This transaction is permanently recorded on the Hedera blockchain
            </p>
            <p>
              Network: Hedera Testnet
            </p>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
