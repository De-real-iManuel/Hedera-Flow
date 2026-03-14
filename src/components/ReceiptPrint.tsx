/**
 * Receipt Print Component
 * 
 * Handles receipt printing functionality for prepaid token purchases
 * Features:
 * - Print receipt in browser
 * - Download as PDF
 * - Email receipt
 * - QR code for blockchain verification
 */

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Separator } from '@/components/ui/separator';
import {
  Printer,
  Download,
  Mail,
  QrCode,
  ExternalLink,
  Loader2,
  Check,
  AlertCircle,
} from 'lucide-react';
import { toast } from 'sonner';
import { prepaidApi } from '@/lib/api/prepaid';
import type { PrepaidToken } from '@/lib/api/prepaid';
import { format } from 'date-fns';

export interface ReceiptPrintProps {
  transaction: PrepaidToken;
  trigger?: React.ReactNode;
}

export function ReceiptPrint({ transaction, trigger }: ReceiptPrintProps) {
  const [receiptContent, setReceiptContent] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const [emailAddress, setEmailAddress] = useState('');
  const [emailLoading, setEmailLoading] = useState(false);
  const [emailSent, setEmailSent] = useState(false);

  // Load receipt content
  const loadReceipt = async () => {
    try {
      setLoading(true);
      const receipt = await prepaidApi.getReceipt(transaction.token_id, 'html');
      setReceiptContent(receipt as string);
    } catch (err) {
      console.error('Failed to load receipt:', err);
      toast.error('Failed to load receipt', {
        description: err instanceof Error ? err.message : 'Unknown error',
      });
    } finally {
      setLoading(false);
    }
  };

  // Print receipt
  const printReceipt = () => {
    if (!receiptContent) {
      toast.error('Receipt not loaded');
      return;
    }

    const printWindow = window.open('', '_blank');
    if (!printWindow) {
      toast.error('Failed to open print window');
      return;
    }

    printWindow.document.write(`
      <!DOCTYPE html>
      <html>
        <head>
          <title>Receipt - ${transaction.token_id}</title>
          <style>
            body {
              font-family: 'Courier New', monospace;
              margin: 20px;
              line-height: 1.4;
            }
            .receipt {
              max-width: 400px;
              margin: 0 auto;
            }
            .header {
              text-align: center;
              border-bottom: 2px solid #000;
              padding-bottom: 10px;
              margin-bottom: 15px;
            }
            .row {
              display: flex;
              justify-content: space-between;
              margin: 5px 0;
            }
            .separator {
              border-top: 1px dashed #000;
              margin: 10px 0;
            }
            .qr-code {
              text-align: center;
              margin: 15px 0;
            }
            @media print {
              body { margin: 0; }
              .no-print { display: none; }
            }
          </style>
        </head>
        <body>
          ${receiptContent}
          <div class="no-print" style="text-align: center; margin-top: 20px;">
            <button onclick="window.print()">Print</button>
            <button onclick="window.close()" style="margin-left: 10px;">Close</button>
          </div>
        </body>
      </html>
    `);

    printWindow.document.close();
    printWindow.focus();
    
    // Auto-print after a short delay
    setTimeout(() => {
      printWindow.print();
    }, 500);
  };

  // Download receipt as HTML
  const downloadReceipt = async (format: 'html' | 'text' = 'html') => {
    try {
      const receipt = await prepaidApi.getReceipt(transaction.token_id, format);
      
      const blob = new Blob([receipt as string], {
        type: format === 'html' ? 'text/html' : 'text/plain',
      });
      
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `receipt-${transaction.token_id}.${format}`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      
      toast.success(`Receipt downloaded as ${format.toUpperCase()}`);
      
    } catch (err) {
      console.error('Failed to download receipt:', err);
      toast.error('Failed to download receipt', {
        description: err instanceof Error ? err.message : 'Unknown error',
      });
    }
  };

  // Email receipt
  const emailReceipt = async () => {
    if (!emailAddress) {
      toast.error('Please enter an email address');
      return;
    }

    try {
      setEmailLoading(true);
      await prepaidApi.emailReceipt(transaction.token_id, emailAddress);
      setEmailSent(true);
      toast.success('Receipt emailed successfully', {
        description: `Receipt sent to ${emailAddress}`,
      });
    } catch (err) {
      console.error('Failed to email receipt:', err);
      toast.error('Failed to email receipt', {
        description: err instanceof Error ? err.message : 'Unknown error',
      });
    } finally {
      setEmailLoading(false);
    }
  };

  // Format currency
  const formatCurrency = (amount: number, currency: string) => {
    const symbols: Record<string, string> = {
      EUR: '€',
      USD: '$',
      INR: '₹',
      BRL: 'R$',
      NGN: '₦',
    };
    const symbol = symbols[currency] || currency;
    return `${symbol}${amount.toLocaleString(undefined, {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    })}`;
  };

  return (
    <Dialog>
      <DialogTrigger asChild>
        {trigger || (
          <Button variant="outline" size="sm" onClick={loadReceipt}>
            <Printer className="w-4 h-4 mr-1" />
            Receipt
          </Button>
        )}
      </DialogTrigger>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Printer className="w-5 h-5" />
            Receipt - {transaction.token_id}
          </DialogTitle>
          <DialogDescription>
            Print, download, or email your transaction receipt
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6">
          {/* Transaction Summary */}
          <div className="bg-gray-50 rounded-lg p-4 space-y-2">
            <div className="flex justify-between items-center">
              <span className="font-semibold">Token ID:</span>
              <span className="font-mono">{transaction.token_id}</span>
            </div>
            {transaction.sts_token && (
              <div className="flex justify-between items-center">
                <span className="font-semibold">STS Token:</span>
                <span className="font-mono text-blue-600 bg-blue-50 px-2 py-1 rounded">{transaction.sts_token}</span>
              </div>
            )}
            <div className="flex justify-between items-center">
              <span className="font-semibold">Amount Paid:</span>
              <span>{formatCurrency(transaction.amount_paid_fiat, transaction.currency)}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="font-semibold">Units:</span>
              <span>{transaction.units_purchased.toFixed(2)} kWh</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="font-semibold">Date:</span>
              <span>{transaction.issued_at ? (() => {
                try {
                  const date = new Date(transaction.issued_at);
                  return isNaN(date.getTime()) ? 'Date unavailable' : format(date, 'PPP p');
                } catch {
                  return 'Date unavailable';
                }
              })() : 'Date unavailable'}</span>
            </div>
            {transaction.hedera_tx_id && (
              <div className="flex justify-between items-center">
                <span className="font-semibold">Blockchain:</span>
                <Button
                  variant="link"
                  size="sm"
                  className="p-0 h-auto"
                  onClick={() => window.open(
                    `https://hashscan.io/testnet/transaction/${transaction.hedera_tx_id}`,
                    '_blank'
                  )}
                >
                  <ExternalLink className="w-3 h-3 mr-1" />
                  View on HashScan
                </Button>
              </div>
            )}
          </div>

          {/* Receipt Preview */}
          {loading ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="w-6 h-6 animate-spin" />
              <span className="ml-2">Loading receipt...</span>
            </div>
          ) : receiptContent ? (
            <div className="border rounded-lg p-4 bg-white max-h-96 overflow-y-auto">
              <div dangerouslySetInnerHTML={{ __html: receiptContent }} />
            </div>
          ) : (
            <div className="text-center py-8">
              <Button onClick={loadReceipt} variant="outline">
                Load Receipt Preview
              </Button>
            </div>
          )}

          <Separator />

          {/* Actions */}
          <div className="space-y-4">
            <h3 className="font-semibold">Receipt Actions</h3>
            
            {/* Print & Download */}
            <div className="flex gap-2 flex-wrap">
              <Button
                onClick={printReceipt}
                disabled={!receiptContent}
                className="flex-1"
              >
                <Printer className="w-4 h-4 mr-2" />
                Print Receipt
              </Button>
              <Button
                onClick={() => downloadReceipt('html')}
                variant="outline"
                disabled={!receiptContent}
              >
                <Download className="w-4 h-4 mr-2" />
                Download HTML
              </Button>
              <Button
                onClick={() => downloadReceipt('text')}
                variant="outline"
                disabled={!receiptContent}
              >
                <Download className="w-4 h-4 mr-2" />
                Download Text
              </Button>
            </div>

            {/* Email Receipt */}
            <div className="space-y-3">
              <Label htmlFor="email">Email Receipt</Label>
              <div className="flex gap-2">
                <Input
                  id="email"
                  type="email"
                  placeholder="Enter email address"
                  value={emailAddress}
                  onChange={(e) => setEmailAddress(e.target.value)}
                  disabled={emailLoading || emailSent}
                />
                <Button
                  onClick={emailReceipt}
                  disabled={!emailAddress || emailLoading || emailSent}
                  variant="outline"
                >
                  {emailLoading ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : emailSent ? (
                    <Check className="w-4 h-4" />
                  ) : (
                    <Mail className="w-4 h-4" />
                  )}
                </Button>
              </div>
              {emailSent && (
                <Alert className="bg-green-50 border-green-200">
                  <Check className="h-4 w-4 text-green-600" />
                  <AlertDescription className="text-green-800">
                    Receipt sent successfully to {emailAddress}
                  </AlertDescription>
                </Alert>
              )}
            </div>
          </div>

          {/* Blockchain Verification Info */}
          <Alert className="bg-blue-50 border-blue-200">
            <QrCode className="h-4 w-4 text-blue-600" />
            <AlertDescription className="text-blue-800">
              <p className="font-semibold mb-1">Blockchain Verified</p>
              <p className="text-sm">
                This receipt is cryptographically verified on the Hedera network. 
                The QR code in the receipt links to the immutable transaction record.
              </p>
            </AlertDescription>
          </Alert>
        </div>
      </DialogContent>
    </Dialog>
  );
}