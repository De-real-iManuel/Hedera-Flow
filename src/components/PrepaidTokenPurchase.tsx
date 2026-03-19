/**
 * Prepaid Token Purchase Component
 * 
 * Allows users to purchase prepaid electricity tokens with HBAR.
 * Features:
 * - Amount input with currency display
 * - Real-time HBAR equivalent calculation
 * - kWh units preview based on tariff
 * - HashPack wallet integration for payment
 * - Loading states and error handling
 * - Success/error notifications
 * 
 * Requirements: US-13, FR-8.1, FR-8.3, FR-8.4
 */

import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Separator } from '@/components/ui/separator';
import { Badge } from '@/components/ui/badge';
import {
  Wallet,
  Zap,
  ArrowRight,
  AlertCircle,
  Loader2,
  Info,
} from 'lucide-react';
import { toast } from 'sonner';
import { useAuth } from '@/hooks/useAuth';
import { prepaidApi } from '@/lib/api/prepaid';
import type { PrepaidTokenPreview } from '@/lib/api/prepaid';
import { useMetaMaskHedera } from '@/hooks/useMetaMaskHedera';

export interface PrepaidTokenPurchaseProps {
  meterId: string;
  onSuccess?: (tokenId: string) => void;
  onCancel?: () => void;
}

export function PrepaidTokenPurchase({
  meterId,
  onSuccess,
  onCancel,
}: PrepaidTokenPurchaseProps) {
  const { user } = useAuth();
  const { walletState, sendHbarPayment, getBalance } = useMetaMaskHedera();
  
  const [amount, setAmount] = useState<number>(50);
  const [loading, setLoading] = useState(false);
  const [loadingStage, setLoadingStage] = useState<string>('');
  const [calculating, setCalculating] = useState(false);
  const [preview, setPreview] = useState<PrepaidTokenPreview | null>(null);
  const [error, setError] = useState<string | null>(null);

  const currency = user?.country_code === 'US' ? 'USD' : 
                   user?.country_code === 'IN' ? 'INR' :
                   user?.country_code === 'BR' ? 'BRL' :
                   user?.country_code === 'NG' ? 'NGN' : 'EUR';

  // Calculate preview when amount changes (with debouncing)
  useEffect(() => {
    if (amount > 0) {
      // Debounce the API call to avoid excessive requests
      const timeoutId = setTimeout(() => {
        calculatePreview();
      }, 500); // Wait 500ms after user stops typing
      
      return () => clearTimeout(timeoutId);
    } else {
      setPreview(null);
    }
  }, [amount, meterId]);

  const calculatePreview = async () => {
    setCalculating(true);
    setError(null);
    
    try {
      const data = await prepaidApi.preview(meterId, amount, currency);
      setPreview(data);
    } catch (err) {
      console.error('Preview calculation failed:', err);
      setError(err instanceof Error ? err.message : 'Failed to calculate preview');
    } finally {
      setCalculating(false);
    }
  };

  const handlePurchase = async () => {
    console.log('Purchase started - User:', user?.email, 'Meter ID:', meterId);
    console.log('Preview data:', preview);
    
    // Validate meter ID format
    const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
    if (!uuidRegex.test(meterId)) {
      toast.error('❌ Invalid Meter ID', {
        description: `Meter ID format is invalid: ${meterId}`,
        duration: 4000,
        className: 'bg-red-50 border-red-500',
      });
      return;
    }
    
    if (!user) {
      toast.error('🔐 Authentication Required', {
        description: 'Please log in to purchase tokens.',
        duration: 4000,
        className: 'bg-red-50 border-red-500',
      });
      return;
    }
    
    if (!preview) {
      toast.error('⚠️ Preview Required', {
        description: 'Please wait for preview calculation to complete.',
        duration: 3000,
        className: 'bg-yellow-50 border-yellow-500',
      });
      return;
    }

    if (!walletState.evmAddress) {
      toast.error('🔌 Wallet Not Connected', {
        description: 'Please connect your MetaMask wallet before purchasing tokens.',
        duration: 4000,
        className: 'bg-yellow-50 border-yellow-500',
      });
      return;
    }

    if (amount <= 0) {
      toast.error('⚠️ Invalid Amount', {
        description: 'Please enter a valid amount greater than 0.',
        duration: 3000,
        className: 'bg-yellow-50 border-yellow-500',
      });
      return;
    }

    setLoading(true);
    setError(null);

    try {
      // Step 1: Check HBAR balance
      setLoadingStage('Checking balance...');
      toast.info('💰 Checking balance...', {
        description: 'Verifying you have sufficient HBAR...',
        duration: 3000,
        className: 'bg-blue-50 border-blue-500',
      });

      const balance = await getBalance();
      if (balance !== null && balance < preview.amount_hbar) {
        throw new Error(
          `Insufficient HBAR balance. Required: ${preview.amount_hbar.toFixed(2)} ℏ, Available: ${balance.toFixed(2)} ℏ`
        );
      }

      // Step 2: Create prepaid token purchase on backend
      setLoadingStage('Preparing transaction...');
      toast.info('📝 Preparing transaction...', {
        description: 'Creating prepaid token purchase...',
        duration: 3000,
        className: 'bg-blue-50 border-blue-500',
      });

      console.log('Making buy API call...');
      
      let buyResponse;
      try {
        buyResponse = await prepaidApi.buy({
          meter_id: meterId,
          amount_fiat: amount,
          currency: currency,
          payment_method: 'HBAR',
        });
        console.log('Buy response received:', buyResponse);
      } catch (apiError) {
        console.error('Buy API call failed:', apiError);
        throw new Error(`Buy API call failed: ${apiError instanceof Error ? apiError.message : 'Unknown error'}`);
      }

      if (!buyResponse || !buyResponse.token) {
        console.error('Invalid buy response:', buyResponse);
        throw new Error('Invalid response from buy endpoint: ' + JSON.stringify(buyResponse));
      }

      const tokenId = buyResponse.token.token_id;
      const transactionDetails = buyResponse.token;

      // Step 3: Request payment signature from MetaMask
      setLoadingStage('Awaiting signature...');
      toast.info('✍️ Awaiting signature...', {
        description: 'Please sign the transaction in MetaMask wallet.',
        duration: 10000,
        className: 'bg-blue-50 border-blue-500',
      });

      // Use treasury account from buy response, fallback to env var
      const treasuryAccount = buyResponse.transaction?.to
        || import.meta.env.VITE_HEDERA_TREASURY_ACCOUNT
        || '0.0.7942971';

      const paymentResult = await sendHbarPayment({
        to: treasuryAccount,
        amount: preview.amount_hbar,
        memo: `Prepaid token: ${tokenId}`,
      });

      if (paymentResult.status !== 'success') {
        throw new Error('Transaction failed on Hedera network');
      }

      // Step 4: Confirm with backend
      setLoadingStage('Confirming payment...');
      toast.info('⏳ Confirming payment...', {
        description: 'Verifying transaction on Hedera...',
        duration: 5000,
        className: 'bg-blue-50 border-blue-500',
      });

      // For MetaMask, we use the transaction hash as the Hedera TX ID
      console.log('Making confirm API call with:', { tokenId, transactionHash: paymentResult.transactionHash });
      
      let confirmResponse;
      try {
        confirmResponse = await prepaidApi.confirm(tokenId, paymentResult.transactionHash);
        console.log('Confirm response received:', confirmResponse);
      } catch (confirmError) {
        console.error('Confirm API call failed:', confirmError);
        throw new Error(`Confirm API call failed: ${confirmError instanceof Error ? confirmError.message : 'Unknown error'}`);
      }

      if (!confirmResponse || !confirmResponse.token) {
        console.error('Invalid confirm response:', confirmResponse);
        throw new Error('Invalid response from confirm endpoint: ' + JSON.stringify(confirmResponse));
      }
      
      setLoadingStage('');
      
      // Success notification with token details
      toast.success('🎉 Token Purchased Successfully!', {
        description: (
          <div className="space-y-2 mt-2">
            <div className="flex items-center justify-between">
              <span className="text-sm font-semibold">Token ID:</span>
              <span className="text-sm font-mono bg-green-100 px-2 py-1 rounded">
                {confirmResponse.token.token_id}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm font-semibold">Units:</span>
              <span className="text-sm">{confirmResponse.token.units_purchased.toFixed(2)} kWh</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm font-semibold">Paid:</span>
              <span className="text-sm">{preview.amount_hbar.toFixed(2)} ℏ</span>
            </div>
            <div className="pt-2 border-t border-green-200">
              <p className="text-xs text-green-700">
                ✓ Receipt confirmed and logged to Hedera HCS
              </p>
              <p className="text-xs text-green-600 mt-1">
                📄 View receipt in Transaction History
              </p>
            </div>
          </div>
        ),
        duration: 8000,
        className: 'bg-green-50 border-green-500',
        action: {
          label: 'View Receipt',
          onClick: () => {
            // Navigate to history or open receipt modal
            window.location.href = '/history';
          },
        },
      });

      if (onSuccess) {
        onSuccess(confirmResponse.token.token_id);
      }
    } catch (err) {
      console.error('Purchase failed:', err);
      const errorMessage = err instanceof Error ? err.message : 'Purchase failed';
      setError(errorMessage);
      
      // Error notification with clear error message
      toast.error('❌ Purchase Failed', {
        description: (
          <div className="space-y-2 mt-2">
            <p className="text-sm font-semibold text-red-800">
              {errorMessage}
            </p>
            <div className="pt-2 border-t border-red-200">
              <p className="text-xs text-red-700">
                Please try again or contact support if the issue persists.
              </p>
            </div>
          </div>
        ),
        duration: 6000,
        className: 'bg-red-50 border-red-500',
        action: {
          label: 'Dismiss',
          onClick: () => {
            // Toast will auto-dismiss
          },
        },
      });
    } finally {
      setLoading(false);
      setLoadingStage('');
    }
  };

  const getCurrencySymbol = (curr: string): string => {
    const symbols: Record<string, string> = {
      EUR: '€',
      USD: '$',
      INR: '₹',
      BRL: 'R$',
      NGN: '₦',
    };
    return symbols[curr] || curr;
  };

  const formatCurrency = (value: number, curr: string) => {
    const symbol = getCurrencySymbol(curr);
    return `${symbol}${value.toLocaleString(undefined, {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    })}`;
  };

  // Show authentication required message if user is not logged in
  if (!user) {
    return (
      <Card className="w-full max-w-2xl">
        <CardHeader>
          <div className="flex items-center gap-3">
            <div className="p-2 bg-red-100 rounded-lg">
              <AlertCircle className="w-6 h-6 text-red-600" />
            </div>
            <div>
              <CardTitle className="text-2xl">Authentication Required</CardTitle>
              <CardDescription>
                Please log in to purchase prepaid electricity tokens
              </CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <Alert className="bg-red-50 border-red-200">
            <AlertCircle className="h-4 w-4 text-red-600" />
            <AlertDescription className="text-red-800">
              You must be logged in to purchase tokens. Please log in and try again.
            </AlertDescription>
          </Alert>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="w-full max-w-2xl">
      <CardHeader>
        <div className="flex items-center gap-3">
          <div className="p-2 bg-purple-100 rounded-lg">
            <Zap className="w-6 h-6 text-purple-600" />
          </div>
          <div>
            <CardTitle className="text-2xl">Buy Prepaid Tokens</CardTitle>
            <CardDescription>
              Pay upfront with HBAR and receive electricity tokens
            </CardDescription>
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-6">
        {/* Amount Input */}
        <div className="space-y-2">
          <Label htmlFor="amount" className="text-base font-semibold">
            Amount
          </Label>
          <div className="relative">
            <div className="absolute left-3 top-1/2 -translate-y-1/2 text-2xl font-bold text-purple-600 pointer-events-none">
              {getCurrencySymbol(currency)}
            </div>
            <Input
              id="amount"
              type="number"
              min="1"
              step="1"
              value={amount}
              onChange={(e) => setAmount(Number(e.target.value))}
              placeholder="Enter amount"
              className="text-lg h-12 pl-12 pr-20"
              disabled={loading}
            />
            <div className="absolute right-3 top-1/2 -translate-y-1/2 text-sm font-semibold text-muted-foreground pointer-events-none">
              {currency}
            </div>
          </div>
          <p className="text-sm text-muted-foreground">
            Minimum: {formatCurrency(10, currency)} • Recommended: {formatCurrency(50, currency)}
          </p>
        </div>

        {/* Preview Calculation */}
        {calculating && (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="w-8 h-8 animate-spin text-purple-600" />
            <span className="ml-3 text-muted-foreground">Calculating...</span>
          </div>
        )}

        {preview && !calculating && (
          <>
            <Separator />

            {/* Preview Details */}
            <div className="bg-gradient-to-br from-purple-50 to-blue-50 border-2 border-purple-200 rounded-lg p-6 space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="font-semibold text-lg text-purple-900">
                  Purchase Preview
                </h3>
                <Badge className="bg-purple-600 text-white">
                  Live Rate
                </Badge>
              </div>

              {/* HBAR Amount */}
              <div className="flex justify-between items-center">
                <span className="text-sm text-purple-700">HBAR Amount</span>
                <div className="text-right">
                  <p className="text-2xl font-bold text-purple-900">
                    {preview.amount_hbar.toFixed(2)} ℏ
                  </p>
                  <p className="text-xs text-purple-600">
                    @ {formatCurrency(preview.exchange_rate, currency)}/HBAR
                  </p>
                </div>
              </div>

              <Separator className="bg-purple-200" />

              {/* kWh Units */}
              <div className="flex justify-between items-center">
                <span className="text-sm text-purple-700">Electricity Units</span>
                <div className="text-right">
                  <p className="text-2xl font-bold text-purple-900">
                    {preview.units_kwh.toFixed(2)} kWh
                  </p>
                  <p className="text-xs text-purple-600">
                    @ {formatCurrency(preview.tariff_rate, currency)}/kWh
                  </p>
                </div>
              </div>

              <Separator className="bg-purple-200" />

              {/* Total Cost */}
              <div className="flex justify-between items-center pt-2">
                <span className="font-semibold text-purple-900">Total Cost</span>
                <p className="text-2xl font-bold text-purple-900">
                  {formatCurrency(preview.amount_fiat, currency)}
                </p>
              </div>
            </div>

            {/* Info Alert */}
            <Alert className="bg-blue-50 border-blue-200">
              <Info className="h-4 w-4 text-blue-600" />
              <AlertDescription className="text-sm text-blue-800">
                <p className="font-semibold mb-1">Token Details:</p>
                <ul className="list-disc list-inside space-y-1 text-xs">
                  <li>Token valid for 1 year from purchase</li>
                  <li>Units deducted automatically as you consume</li>
                  <li>Low balance alert at 10 kWh remaining</li>
                  <li>Transaction logged to Hedera HCS for audit</li>
                </ul>
              </AlertDescription>
            </Alert>
          </>
        )}

        {/* Error Display */}
        {error && (
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        {/* Loading Stage Display */}
        {loading && loadingStage && (
          <Alert className="bg-purple-50 border-purple-200">
            <Loader2 className="h-4 w-4 text-purple-600 animate-spin" />
            <AlertDescription className="text-purple-800 font-medium">
              {loadingStage}
            </AlertDescription>
          </Alert>
        )}

        {/* Action Buttons */}
        <div className="flex gap-3 pt-4">
          {onCancel && (
            <Button
              variant="outline"
              onClick={onCancel}
              disabled={loading}
              className="flex-1"
            >
              Cancel
            </Button>
          )}
          <Button
            onClick={handlePurchase}
            disabled={loading || calculating || !preview || amount <= 0}
            className="flex-1 bg-purple-600 hover:bg-purple-700 text-white"
            size="lg"
          >
            {loading ? (
              <>
                <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                {loadingStage || 'Processing...'}
              </>
            ) : (
              <>
                <Wallet className="w-5 h-5 mr-2" />
                Buy with MetaMask
                <ArrowRight className="w-5 h-5 ml-2" />
              </>
            )}
          </Button>
        </div>

        {/* Wallet Connection Notice */}
        {!walletState.evmAddress && (
          <Alert className="bg-yellow-50 border-yellow-200">
            <AlertCircle className="h-4 w-4 text-yellow-600" />
            <AlertDescription className="text-sm text-yellow-800">
              Please connect your MetaMask wallet before purchasing tokens
            </AlertDescription>
          </Alert>
        )}
      </CardContent>
    </Card>
  );
}
