import { motion } from "framer-motion";
import { Check, Download, ExternalLink, Receipt, Calendar, Hash, Zap } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";

export interface PaymentReceiptData {
  id: string;
  billId: string;
  transactionId: string;
  amount: {
    hbar: number;
    fiat: number;
    currency: string;
  };
  exchangeRate: number;
  timestamp: string;
  consensusTimestamp?: string;
  status: 'pending' | 'confirmed' | 'failed';
  explorerUrl?: string;
  meter: {
    id: string;
    address?: string;
  };
  consumption: {
    kwh: number;
    period: string;
  };
}

interface PaymentReceiptProps {
  data: PaymentReceiptData;
  onClose?: () => void;
  onDownload?: () => void;
}

export function PaymentReceipt({ data, onClose, onDownload }: PaymentReceiptProps) {
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

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  const getStatusConfig = () => {
    switch (data.status) {
      case 'confirmed':
        return {
          color: 'text-green-600',
          bgColor: 'bg-green-50',
          borderColor: 'border-green-200',
          badge: 'CONFIRMED',
          badgeVariant: 'default' as const,
        };
      case 'pending':
        return {
          color: 'text-yellow-600',
          bgColor: 'bg-yellow-50',
          borderColor: 'border-yellow-200',
          badge: 'PENDING',
          badgeVariant: 'secondary' as const,
        };
      case 'failed':
        return {
          color: 'text-red-600',
          bgColor: 'bg-red-50',
          borderColor: 'border-red-200',
          badge: 'FAILED',
          badgeVariant: 'destructive' as const,
        };
    }
  };

  const statusConfig = getStatusConfig();

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0 }}
      className="space-y-5"
    >
      {/* Header */}
      <div className="flex flex-col items-center py-6 space-y-3">
        <div className={`w-16 h-16 rounded-full ${statusConfig.bgColor} flex items-center justify-center`}>
          <Receipt className={`w-8 h-8 ${statusConfig.color}`} />
        </div>
        <div className="text-center">
          <h2 className="text-2xl font-bold text-foreground">Payment Receipt</h2>
          <p className="text-sm text-muted-foreground mt-1">
            Transaction completed successfully
          </p>
        </div>
        <Badge variant={statusConfig.badgeVariant}>{statusConfig.badge}</Badge>
      </div>

      {/* Receipt Details */}
      <Card className="border-2">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Zap className="w-5 h-5 text-accent" />
            Payment Summary
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Amount Paid */}
          <div className="text-center py-4">
            <p className="text-sm text-muted-foreground mb-1">Amount Paid</p>
            <p className="text-3xl font-bold text-primary">
              {data.amount.hbar.toFixed(8)} HBAR
            </p>
            <p className="text-lg text-muted-foreground">
              {formatCurrency(data.amount.fiat, data.amount.currency)}
            </p>
          </div>

          <Separator />

          {/* Transaction Details */}
          <div className="space-y-3">
            <h4 className="font-semibold text-foreground">Transaction Details</h4>
            
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-muted-foreground">Transaction ID:</span>
                <div className="flex items-center gap-2">
                  <span className="font-mono text-xs">{data.transactionId}</span>
                  {data.explorerUrl && (
                    <a
                      href={data.explorerUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-primary hover:underline"
                    >
                      <ExternalLink className="w-3 h-3" />
                    </a>
                  )}
                </div>
              </div>
              
              <div className="flex justify-between">
                <span className="text-muted-foreground">Receipt ID:</span>
                <span className="font-mono text-xs">{data.id}</span>
              </div>
              
              <div className="flex justify-between">
                <span className="text-muted-foreground">Bill ID:</span>
                <span className="font-mono text-xs">{data.billId}</span>
              </div>
              
              <div className="flex justify-between">
                <span className="text-muted-foreground">Exchange Rate:</span>
                <span className="font-medium">
                  {data.exchangeRate.toFixed(6)} {data.amount.currency}/HBAR
                </span>
              </div>
            </div>
          </div>

          <Separator />

          {/* Consumption Details */}
          <div className="space-y-3">
            <h4 className="font-semibold text-foreground">Consumption Details</h4>
            
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-muted-foreground">Energy Used:</span>
                <span className="font-medium">{data.consumption.kwh.toLocaleString()} kWh</span>
              </div>
              
              <div className="flex justify-between">
                <span className="text-muted-foreground">Billing Period:</span>
                <span className="font-medium">{data.consumption.period}</span>
              </div>
              
              <div className="flex justify-between">
                <span className="text-muted-foreground">Meter ID:</span>
                <span className="font-mono text-xs">{data.meter.id}</span>
              </div>
              
              {data.meter.address && (
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Address:</span>
                  <span className="text-xs">{data.meter.address}</span>
                </div>
              )}
            </div>
          </div>

          <Separator />

          {/* Timestamps */}
          <div className="space-y-3">
            <h4 className="font-semibold text-foreground">Timestamps</h4>
            
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-muted-foreground">Payment Time:</span>
                <span className="font-medium">{formatDate(data.timestamp)}</span>
              </div>
              
              {data.consensusTimestamp && (
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Consensus Time:</span>
                  <span className="font-medium">{formatDate(data.consensusTimestamp)}</span>
                </div>
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Blockchain Verification */}
      <Card className="border-2 border-blue-200 bg-blue-50">
        <CardContent className="p-4">
          <div className="flex items-start gap-3">
            <Check className="w-5 h-5 text-blue-600 shrink-0 mt-0.5" />
            <div className="flex-1">
              <p className="text-sm font-medium text-blue-900 mb-1">
                Blockchain Verified
              </p>
              <p className="text-xs text-blue-800">
                This payment has been permanently recorded on the Hedera network and cannot be altered or disputed.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Action Buttons */}
      <div className="grid grid-cols-2 gap-3 pt-2">
        {onDownload && (
          <Button
            variant="outline"
            size="lg"
            onClick={onDownload}
            className="w-full"
          >
            <Download className="w-4 h-4 mr-2" />
            Download PDF
          </Button>
        )}
        
        {onClose && (
          <Button
            size="lg"
            onClick={onClose}
            className="w-full"
          >
            Done
          </Button>
        )}
      </div>

      {/* Footer */}
      <div className="text-center pt-4">
        <p className="text-xs text-muted-foreground">
          Powered by Hedera Flow • Decentralized Utility Payments
        </p>
      </div>
    </motion.div>
  );
}