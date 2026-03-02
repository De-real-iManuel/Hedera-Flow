/**
 * Top Up Modal Component
 * 
 * Displays when user has insufficient HBAR balance to complete payment.
 * Shows:
 * - Current balance vs required amount
 * - Shortfall in HBAR and fiat
 * - Links to exchanges (Binance, Coinbase)
 * - QR code for receiving HBAR
 * - Copy-to-clipboard for account ID
 * - Minimum amount needed
 * 
 * Requirements: FR-6.3, US-7
 */

import { useState, useEffect } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Separator } from '@/components/ui/separator';
import { Badge } from '@/components/ui/badge';
import {
  Wallet,
  AlertCircle,
  ExternalLink,
  Copy,
  Check,
  RefreshCw,
  TrendingUp,
  ArrowRight,
  Info,
} from 'lucide-react';
import { toast } from 'sonner';
import QRCode from 'qrcode';

export interface TopUpModalProps {
  isOpen: boolean;
  onClose: () => void;
  currentBalance: number; // HBAR
  requiredAmount: number; // HBAR
  fiatAmount: number;
  currency: string;
  exchangeRate: number; // HBAR price in fiat
  accountId: string;
  onBalanceRefresh?: () => Promise<number | null>; // Callback to refresh balance
}

export function TopUpModal({
  isOpen,
  onClose,
  currentBalance,
  requiredAmount,
  fiatAmount,
  currency,
  exchangeRate,
  accountId,
  onBalanceRefresh,
}: TopUpModalProps) {
  const [qrCodeUrl, setQrCodeUrl] = useState<string>('');
  const [isCopied, setIsCopied] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [updatedBalance, setUpdatedBalance] = useState<number | null>(null);

  // Calculate shortfall
  const shortfall = Math.max(0, requiredAmount - currentBalance);
  const shortfallFiat = shortfall * exchangeRate;

  // Minimum amount needed (shortfall + small buffer for fees)
  const minimumNeeded = Math.ceil(shortfall + 5); // Add 5 HBAR buffer for fees
  const minimumNeededFiat = minimumNeeded * exchangeRate;

  // Generate QR code for account ID
  useEffect(() => {
    if (isOpen && accountId) {
      generateQRCode();
    }
  }, [isOpen, accountId]);

  const generateQRCode = async () => {
    try {
      // Generate QR code with account ID
      const url = await QRCode.toDataURL(accountId, {
        width: 256,
        margin: 2,
        color: {
          dark: '#000000',
          light: '#FFFFFF',
        },
      });
      setQrCodeUrl(url);
    } catch (error) {
      console.error('Failed to generate QR code:', error);
      toast.error('Failed to generate QR code');
    }
  };

  const handleCopyAccountId = async () => {
    try {
      await navigator.clipboard.writeText(accountId);
      setIsCopied(true);
      toast.success('Account ID copied to clipboard');
      
      // Reset copied state after 2 seconds
      setTimeout(() => setIsCopied(false), 2000);
    } catch (error) {
      console.error('Failed to copy:', error);
      toast.error('Failed to copy account ID');
    }
  };

  const handleRefreshBalance = async () => {
    if (!onBalanceRefresh) return;

    setIsRefreshing(true);
    try {
      const newBalance = await onBalanceRefresh();
      if (newBalance !== null) {
        setUpdatedBalance(newBalance);
        
        // Check if balance is now sufficient
        if (newBalance >= requiredAmount) {
          toast.success('Balance Updated!', {
            description: `You now have ${newBalance.toFixed(2)} HBAR. You can proceed with payment.`,
          });
          
          // Close modal after 2 seconds
          setTimeout(() => {
            onClose();
          }, 2000);
        } else {
          toast.info('Balance Updated', {
            description: `Current balance: ${newBalance.toFixed(2)} HBAR. Still need ${(requiredAmount - newBalance).toFixed(2)} HBAR more.`,
          });
        }
      }
    } catch (error) {
      console.error('Failed to refresh balance:', error);
      toast.error('Failed to refresh balance');
    } finally {
      setIsRefreshing(false);
    }
  };

  const formatCurrency = (amount: number, curr: string) => {
    const symbols: Record<string, string> = {
      EUR: '€',
      USD: '$',
      INR: '₹',
      BRL: 'R$',
      NGN: '₦',
    };
    return `${symbols[curr] || curr}${amount.toLocaleString(undefined, {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    })}`;
  };

  const displayBalance = updatedBalance !== null ? updatedBalance : currentBalance;

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <div className="flex items-center gap-3">
            <div className="p-2 bg-red-100 rounded-lg">
              <Wallet className="w-6 h-6 text-red-600" />
            </div>
            <div>
              <DialogTitle className="text-xl">Insufficient HBAR Balance</DialogTitle>
              <DialogDescription>
                You need more HBAR to complete this payment
              </DialogDescription>
            </div>
          </div>
        </DialogHeader>

        <div className="space-y-6 mt-4">
          {/* Balance Summary */}
          <Alert variant="destructive" className="border-red-300 bg-red-50">
            <AlertCircle className="h-5 w-5" />
            <AlertDescription className="text-red-800">
              <div className="space-y-2">
                <p className="font-semibold">
                  Your current balance is insufficient for this transaction.
                </p>
                <div className="grid grid-cols-2 gap-4 mt-3 text-sm">
                  <div>
                    <p className="text-red-600 mb-1">Current Balance</p>
                    <p className="text-lg font-bold text-red-900">
                      {displayBalance.toFixed(2)} ℏ
                    </p>
                    <p className="text-xs text-red-700">
                      ≈ {formatCurrency(displayBalance * exchangeRate, currency)}
                    </p>
                  </div>
                  <div>
                    <p className="text-red-600 mb-1">Required Amount</p>
                    <p className="text-lg font-bold text-red-900">
                      {requiredAmount.toFixed(2)} ℏ
                    </p>
                    <p className="text-xs text-red-700">
                      ≈ {formatCurrency(fiatAmount, currency)}
                    </p>
                  </div>
                </div>
              </div>
            </AlertDescription>
          </Alert>

          {/* Shortfall Details */}
          <div className="bg-orange-50 border-2 border-orange-200 rounded-lg p-4">
            <div className="flex items-center justify-between mb-3">
              <h3 className="font-semibold text-orange-900 flex items-center gap-2">
                <TrendingUp className="w-5 h-5" />
                Amount Needed
              </h3>
              <Badge className="bg-orange-600 text-white">
                Shortfall
              </Badge>
            </div>
            
            <div className="space-y-2">
              <div className="flex justify-between items-center">
                <span className="text-sm text-orange-700">Shortfall</span>
                <span className="text-xl font-bold text-orange-900">
                  {shortfall.toFixed(2)} ℏ
                </span>
              </div>
              <div className="flex justify-between items-center text-sm">
                <span className="text-orange-700">In {currency}</span>
                <span className="font-semibold text-orange-800">
                  {formatCurrency(shortfallFiat, currency)}
                </span>
              </div>
              
              <Separator className="my-2 bg-orange-200" />
              
              <div className="flex justify-between items-center">
                <span className="text-sm text-orange-700">Minimum to Add</span>
                <span className="text-lg font-bold text-orange-900">
                  {minimumNeeded.toFixed(2)} ℏ
                </span>
              </div>
              <div className="flex justify-between items-center text-xs">
                <span className="text-orange-600">
                  (includes 5 HBAR buffer for fees)
                </span>
                <span className="font-medium text-orange-700">
                  ≈ {formatCurrency(minimumNeededFiat, currency)}
                </span>
              </div>
            </div>
          </div>

          <Separator />

          {/* Top Up Options */}
          <div className="space-y-4">
            <h3 className="font-semibold text-lg flex items-center gap-2">
              <ArrowRight className="w-5 h-5 text-primary" />
              How to Top Up Your HBAR Balance
            </h3>

            {/* Option 1: Buy from Exchanges */}
            <div className="border-2 border-gray-200 rounded-lg p-4 space-y-3">
              <div className="flex items-center justify-between">
                <h4 className="font-semibold text-base">Option 1: Buy HBAR from Exchanges</h4>
                <Badge variant="outline" className="bg-green-50 text-green-700 border-green-300">
                  Recommended
                </Badge>
              </div>
              
              <p className="text-sm text-muted-foreground">
                Purchase HBAR from cryptocurrency exchanges and send to your account
              </p>

              <div className="grid grid-cols-2 gap-3">
                <Button
                  variant="outline"
                  className="w-full justify-between hover:bg-blue-50 hover:border-blue-300"
                  onClick={() => window.open('https://www.binance.com/en/trade/HBAR_USDT', '_blank')}
                >
                  <span className="flex items-center gap-2">
                    <img 
                      src="https://cryptologos.cc/logos/binance-coin-bnb-logo.png" 
                      alt="Binance" 
                      className="w-5 h-5"
                    />
                    Binance
                  </span>
                  <ExternalLink className="w-4 h-4" />
                </Button>

                <Button
                  variant="outline"
                  className="w-full justify-between hover:bg-blue-50 hover:border-blue-300"
                  onClick={() => window.open('https://www.coinbase.com/price/hedera', '_blank')}
                >
                  <span className="flex items-center gap-2">
                    <img 
                      src="https://cryptologos.cc/logos/coinbase-coin-logo.png" 
                      alt="Coinbase" 
                      className="w-5 h-5"
                    />
                    Coinbase
                  </span>
                  <ExternalLink className="w-4 h-4" />
                </Button>
              </div>

              <Alert className="bg-blue-50 border-blue-200">
                <Info className="h-4 w-4 text-blue-600" />
                <AlertDescription className="text-sm text-blue-800">
                  After purchasing, withdraw HBAR to your account ID below
                </AlertDescription>
              </Alert>
            </div>

            {/* Option 2: Receive from Another Wallet */}
            <div className="border-2 border-gray-200 rounded-lg p-4 space-y-3">
              <h4 className="font-semibold text-base">Option 2: Receive HBAR from Another Wallet</h4>
              
              <p className="text-sm text-muted-foreground">
                Send HBAR from another wallet or exchange to your account
              </p>

              {/* Account ID */}
              <div className="space-y-2">
                <label className="text-sm font-medium text-foreground">
                  Your Hedera Account ID
                </label>
                <div className="flex gap-2">
                  <div className="flex-1 bg-gray-100 border border-gray-300 rounded-lg px-4 py-3 font-mono text-sm">
                    {accountId}
                  </div>
                  <Button
                    variant="outline"
                    size="icon"
                    onClick={handleCopyAccountId}
                    className="shrink-0"
                  >
                    {isCopied ? (
                      <Check className="w-4 h-4 text-green-600" />
                    ) : (
                      <Copy className="w-4 h-4" />
                    )}
                  </Button>
                </div>
              </div>

              {/* QR Code */}
              {qrCodeUrl && (
                <div className="flex flex-col items-center gap-2 p-4 bg-white border-2 border-gray-200 rounded-lg">
                  <p className="text-sm font-medium text-muted-foreground">
                    Scan QR Code to Send HBAR
                  </p>
                  <img 
                    src={qrCodeUrl} 
                    alt="Account QR Code" 
                    className="w-48 h-48 border-4 border-gray-300 rounded-lg"
                  />
                  <p className="text-xs text-muted-foreground text-center max-w-xs">
                    Scan this QR code with a Hedera wallet to send HBAR to your account
                  </p>
                </div>
              )}
            </div>
          </div>

          <Separator />

          {/* Refresh Balance */}
          <div className="bg-purple-50 border-2 border-purple-200 rounded-lg p-4">
            <div className="flex items-center justify-between mb-3">
              <div>
                <h4 className="font-semibold text-purple-900">
                  Added HBAR to Your Account?
                </h4>
                <p className="text-sm text-purple-700 mt-1">
                  Click refresh to check your updated balance
                </p>
              </div>
            </div>
            
            <Button
              onClick={handleRefreshBalance}
              disabled={isRefreshing}
              className="w-full bg-purple-600 hover:bg-purple-700 text-white"
              size="lg"
            >
              {isRefreshing ? (
                <>
                  <RefreshCw className="w-5 h-5 mr-2 animate-spin" />
                  Checking Balance...
                </>
              ) : (
                <>
                  <RefreshCw className="w-5 h-5 mr-2" />
                  Refresh Balance
                </>
              )}
            </Button>
          </div>

          {/* Important Notes */}
          <Alert className="bg-gray-50 border-gray-200">
            <Info className="h-4 w-4 text-gray-600" />
            <AlertDescription className="text-sm text-gray-700">
              <p className="font-semibold mb-2">Important Notes:</p>
              <ul className="list-disc list-inside space-y-1 text-xs">
                <li>Minimum recommended top-up: {minimumNeeded.toFixed(2)} HBAR</li>
                <li>Exchange transfers may take 5-15 minutes to confirm</li>
                <li>Always verify the account ID before sending HBAR</li>
                <li>Network fees are typically 0.0001 HBAR per transaction</li>
                <li>This is Hedera Testnet - use testnet HBAR only</li>
              </ul>
            </AlertDescription>
          </Alert>

          {/* Action Buttons */}
          <div className="flex gap-3">
            <Button
              variant="outline"
              onClick={onClose}
              className="flex-1"
            >
              Cancel Payment
            </Button>
            <Button
              onClick={handleRefreshBalance}
              disabled={isRefreshing}
              className="flex-1 bg-primary hover:bg-primary/90"
            >
              {isRefreshing ? (
                <>
                  <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                  Checking...
                </>
              ) : (
                <>
                  <RefreshCw className="w-4 h-4 mr-2" />
                  Check Balance & Retry
                </>
              )}
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
