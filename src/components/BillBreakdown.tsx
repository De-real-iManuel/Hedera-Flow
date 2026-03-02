import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Info, Zap, TrendingUp, Receipt, RefreshCw, AlertCircle, Clock, Wallet, ExternalLink } from "lucide-react";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { useEffect, useState, useCallback } from "react";
import { exchangeRateApi, paymentsApi } from "@/lib/api";
import type { ExchangeRate } from "@/types/api";
import { useHashPack, type PaymentTransaction } from "@/lib/hashpack";
import { toast } from "sonner";
import { PaymentConfirmationModal, type PaymentConfirmationData } from "./PaymentConfirmationModal";
import { TopUpModal } from "./TopUpModal";

export interface BillBreakdownData {
  // Consumption
  consumptionKwh: number;
  
  // Charges
  baseCharge: number;
  taxes: number;
  subsidies?: number;
  serviceCharge?: number;
  platformServiceCharge?: number; // 3% platform fee
  platformVat?: number; // VAT on platform fee
  totalFiat: number;
  currency: string;
  
  // Tariff details
  rateStructureType?: 'flat' | 'tiered' | 'time_of_use' | 'band_based';
  rateDetails?: {
    tiers?: Array<{
      name: string;
      kwh: number;
      rate: number;
      amount: number;
    }>;
    periods?: Array<{
      name: string;
      hours: number[];
      rate: number;
      kwh?: number;
      amount?: number;
    }>;
    band?: {
      name: string;
      rate: number;
      hoursMin: number;
    };
  };
}

interface BillBreakdownProps {
  data: BillBreakdownData;
  showHbarConversion?: boolean;
  className?: string;
  billId?: string; // Bill ID for payment
  utilityAccountId?: string; // Utility provider's Hedera account
  userAccountId?: string; // User's Hedera account
  onPaymentSuccess?: (transactionId: string) => void;
  onPaymentError?: (error: string) => void;
}

export function BillBreakdown({ 
  data, 
  showHbarConversion = false, 
  className = "",
  billId,
  utilityAccountId = "0.0.999999", // Default utility account (placeholder)
  userAccountId,
  onPaymentSuccess,
  onPaymentError,
}: BillBreakdownProps) {
  const [exchangeRate, setExchangeRate] = useState<ExchangeRate | null>(null);
  const [isLoadingRate, setIsLoadingRate] = useState(false);
  const [rateError, setRateError] = useState<string | null>(null);
  const [amountHbar, setAmountHbar] = useState<number | null>(null);
  const [rateFetchedAt, setRateFetchedAt] = useState<Date | null>(null);
  const [timeRemaining, setTimeRemaining] = useState<number>(300); // 5 minutes in seconds
  const [isExpired, setIsExpired] = useState(false);
  const [isProcessingPayment, setIsProcessingPayment] = useState(false);
  const [showConfirmationModal, setShowConfirmationModal] = useState(false);
  const [confirmationData, setConfirmationData] = useState<PaymentConfirmationData | null>(null);
  const [showTopUpModal, setShowTopUpModal] = useState(false);
  const [insufficientBalanceData, setInsufficientBalanceData] = useState<{
    currentBalance: number;
    requiredAmount: number;
    accountId: string;
  } | null>(null);
  
  const hashPack = useHashPack();

  // Fetch exchange rate when component mounts or when showHbarConversion changes
  useEffect(() => {
    if (showHbarConversion && data.currency) {
      fetchExchangeRate();
    }
  }, [showHbarConversion, data.currency]);

  // Countdown timer for rate expiry
  useEffect(() => {
    if (!rateFetchedAt || !showHbarConversion) return;

    const interval = setInterval(() => {
      const now = new Date();
      const elapsed = Math.floor((now.getTime() - rateFetchedAt.getTime()) / 1000);
      const remaining = Math.max(0, 300 - elapsed); // 5 minutes = 300 seconds
      
      setTimeRemaining(remaining);
      
      if (remaining === 0 && !isExpired) {
        setIsExpired(true);
      }
    }, 1000);

    return () => clearInterval(interval);
  }, [rateFetchedAt, showHbarConversion, isExpired]);

  const fetchExchangeRate = useCallback(async () => {
    setIsLoadingRate(true);
    setRateError(null);
    setIsExpired(false);
    
    try {
      const rate = await exchangeRateApi.get(data.currency);
      setExchangeRate(rate);
      setRateFetchedAt(new Date());
      setTimeRemaining(300); // Reset to 5 minutes
      
      // Calculate HBAR amount: fiat_amount / hbar_price
      const hbarAmount = data.totalFiat / rate.hbarPrice;
      setAmountHbar(hbarAmount);
    } catch (error: any) {
      console.error('Failed to fetch exchange rate:', error);
      setRateError(error.response?.data?.detail || 'Failed to fetch exchange rate');
    } finally {
      setIsLoadingRate(false);
    }
  }, [data.currency, data.totalFiat]);

  const formatTimeRemaining = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const getExpiryStatus = (): 'active' | 'warning' | 'expired' => {
    if (isExpired || timeRemaining === 0) return 'expired';
    if (timeRemaining < 60) return 'warning'; // Less than 1 minute
    return 'active';
  };

  /**
   * Handle payment button click
   */
  const handlePayNow = async () => {
    // Validate prerequisites
    if (!billId) {
      toast.error('Missing bill ID', {
        description: 'Cannot process payment without a bill ID.',
      });
      return;
    }

    if (!amountHbar || amountHbar <= 0) {
      toast.error('Invalid payment amount', {
        description: 'Please refresh the exchange rate and try again.',
      });
      return;
    }

    if (getExpiryStatus() === 'expired') {
      toast.error('Exchange rate expired', {
        description: 'Please refresh the rate before making a payment.',
      });
      return;
    }

    setIsProcessingPayment(true);

    try {
      // Connect to HashPack if not already connected
      let accountId = userAccountId;
      if (!accountId) {
        toast.info('Connecting to wallet...', {
          description: 'Please approve the connection in HashPack.',
        });
        
        accountId = await hashPack.connect();
        if (!accountId) {
          throw new Error('Failed to connect to wallet');
        }
      }

      // Check balance
      const balance = await hashPack.checkBalance(accountId);
      if (balance !== null && balance < amountHbar) {
        // Show Top Up modal with detailed information
        setInsufficientBalanceData({
          currentBalance: balance,
          requiredAmount: amountHbar,
          accountId: accountId,
        });
        setShowTopUpModal(true);
        setIsProcessingPayment(false);
        return;
      }

      // Prepare transaction
      const transaction: PaymentTransaction = {
        from: accountId,
        to: utilityAccountId,
        amount: amountHbar,
        memo: `Bill payment: ${billId}`,
        billId: billId,
        fiatAmount: data.totalFiat,
        currency: data.currency,
      };

      // Execute payment
      const result = await hashPack.executePayment(transaction);

      if (result.success && result.transactionId) {
        // Payment successful - fetch confirmation details from backend
        try {
          // Get payment details from backend
          const paymentDetails = await paymentsApi.get(billId);
          
          // Prepare confirmation data for modal
          const confirmData: PaymentConfirmationData = {
            transactionId: result.transactionId,
            consensusTimestamp: paymentDetails.consensus_timestamp || new Date().toISOString(),
            amountHbar: paymentDetails.amount_hbar || amountHbar,
            amountFiat: paymentDetails.amount_fiat || data.totalFiat,
            currency: paymentDetails.currency || data.currency,
            exchangeRate: paymentDetails.exchange_rate || exchangeRate?.hbarPrice || 0,
            exchangeRateSource: exchangeRate?.source || 'coingecko',
            billId: billId,
            consumptionKwh: data.consumptionKwh,
            receiptUrl: paymentDetails.receipt_url,
          };
          
          setConfirmationData(confirmData);
          setShowConfirmationModal(true);
          
          // Call success callback
          if (onPaymentSuccess) {
            onPaymentSuccess(result.transactionId);
          }
        } catch (error) {
          console.error('Failed to fetch payment details:', error);
          // Still show success but with limited data
          const confirmData: PaymentConfirmationData = {
            transactionId: result.transactionId,
            consensusTimestamp: new Date().toISOString(),
            amountHbar: amountHbar,
            amountFiat: data.totalFiat,
            currency: data.currency,
            exchangeRate: exchangeRate?.hbarPrice || 0,
            exchangeRateSource: exchangeRate?.source || 'coingecko',
            billId: billId,
            consumptionKwh: data.consumptionKwh,
          };
          
          setConfirmationData(confirmData);
          setShowConfirmationModal(true);
          
          if (onPaymentSuccess) {
            onPaymentSuccess(result.transactionId);
          }
        }
      } else {
        // Payment failed
        const errorMsg = result.error || 'Transaction failed';
        if (onPaymentError) {
          onPaymentError(errorMsg);
        }
      }
    } catch (error: any) {
      console.error('Payment error:', error);
      const errorMsg = error.message || 'An unexpected error occurred';
      
      if (onPaymentError) {
        onPaymentError(errorMsg);
      }
    } finally {
      setIsProcessingPayment(false);
    }
  };
  
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

  const getRateStructureLabel = () => {
    switch (data.rateStructureType) {
      case 'flat':
        return 'Flat Rate';
      case 'tiered':
        return 'Tiered Rate';
      case 'time_of_use':
        return 'Time-of-Use';
      case 'band_based':
        return 'Band-Based';
      default:
        return 'Standard Rate';
    }
  };

  const getRateStructureBadgeColor = () => {
    switch (data.rateStructureType) {
      case 'flat':
        return 'bg-blue-100 text-blue-800 border-blue-200';
      case 'tiered':
        return 'bg-purple-100 text-purple-800 border-purple-200';
      case 'time_of_use':
        return 'bg-orange-100 text-orange-800 border-orange-200';
      case 'band_based':
        return 'bg-green-100 text-green-800 border-green-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  return (
    <Card className={`border-2 ${className}`}>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg font-semibold flex items-center gap-2">
            <Receipt className="w-5 h-5 text-primary" />
            Bill Breakdown
          </CardTitle>
          {data.rateStructureType && (
            <Badge className={`${getRateStructureBadgeColor()} border`}>
              {getRateStructureLabel()}
            </Badge>
          )}
        </div>
      </CardHeader>
      
      <CardContent className="space-y-4">
        {/* Consumption Summary */}
        <div className="bg-gradient-to-br from-blue-50 to-blue-100 rounded-lg p-4 border border-blue-200">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Zap className="w-5 h-5 text-blue-600" />
              <span className="text-sm font-medium text-blue-900">Total Consumption</span>
            </div>
            <span className="text-2xl font-bold text-blue-900">
              {data.consumptionKwh.toLocaleString()} kWh
            </span>
          </div>
        </div>

        {/* Tariff Rate Details */}
        {data.rateDetails && (
          <>
            <Separator />
            <div className="space-y-3">
              <div className="flex items-center gap-2">
                <TrendingUp className="w-4 h-4 text-muted-foreground" />
                <h3 className="text-sm font-semibold text-foreground uppercase tracking-wider">
                  Tariff Details
                </h3>
              </div>

              {/* Tiered Rate Breakdown */}
              {data.rateDetails.tiers && data.rateDetails.tiers.length > 0 && (
                <div className="space-y-2">
                  {data.rateDetails.tiers.map((tier, index) => (
                    <div key={index} className="flex justify-between items-center text-sm bg-muted/50 p-2 rounded">
                      <div className="flex items-center gap-2">
                        <span className="text-muted-foreground">{tier.name}</span>
                        <TooltipProvider>
                          <Tooltip>
                            <TooltipTrigger>
                              <Info className="w-3 h-3 text-muted-foreground" />
                            </TooltipTrigger>
                            <TooltipContent>
                              <p>{tier.kwh} kWh × {formatCurrency(tier.rate, data.currency)}/kWh</p>
                            </TooltipContent>
                          </Tooltip>
                        </TooltipProvider>
                      </div>
                      <span className="font-medium text-foreground">
                        {formatCurrency(tier.amount, data.currency)}
                      </span>
                    </div>
                  ))}
                </div>
              )}

              {/* Time-of-Use Breakdown */}
              {data.rateDetails.periods && data.rateDetails.periods.length > 0 && (
                <div className="space-y-2">
                  {data.rateDetails.periods.map((period, index) => (
                    <div key={index} className="flex justify-between items-center text-sm bg-muted/50 p-2 rounded">
                      <div className="flex items-center gap-2">
                        <span className="text-muted-foreground capitalize">{period.name}</span>
                        <TooltipProvider>
                          <Tooltip>
                            <TooltipTrigger>
                              <Info className="w-3 h-3 text-muted-foreground" />
                            </TooltipTrigger>
                            <TooltipContent>
                              <p>Rate: {formatCurrency(period.rate, data.currency)}/kWh</p>
                              {period.kwh && <p>Usage: {period.kwh} kWh</p>}
                            </TooltipContent>
                          </Tooltip>
                        </TooltipProvider>
                      </div>
                      {period.amount && (
                        <span className="font-medium text-foreground">
                          {formatCurrency(period.amount, data.currency)}
                        </span>
                      )}
                    </div>
                  ))}
                </div>
              )}

              {/* Band-Based Rate */}
              {data.rateDetails.band && (
                <div className="bg-muted/50 p-3 rounded space-y-1">
                  <div className="flex justify-between items-center text-sm">
                    <span className="text-muted-foreground">Band Classification</span>
                    <Badge variant="outline">{data.rateDetails.band.name}</Badge>
                  </div>
                  <div className="flex justify-between items-center text-sm">
                    <span className="text-muted-foreground">Rate</span>
                    <span className="font-medium text-foreground">
                      {formatCurrency(data.rateDetails.band.rate, data.currency)}/kWh
                    </span>
                  </div>
                  <div className="flex justify-between items-center text-xs text-muted-foreground">
                    <span>Minimum Supply Hours</span>
                    <span>{data.rateDetails.band.hoursMin}h/day</span>
                  </div>
                </div>
              )}
            </div>
          </>
        )}

        <Separator />

        {/* Itemized Charges */}
        <div className="space-y-3">
          <h3 className="text-sm font-semibold text-foreground uppercase tracking-wider">
            Charges
          </h3>
          
          <div className="space-y-2">
            {/* Base Charge */}
            <div className="flex justify-between items-center text-sm">
              <span className="text-muted-foreground">Energy Charge</span>
              <span className="font-medium text-foreground">
                {formatCurrency(data.baseCharge, data.currency)}
              </span>
            </div>

            {/* Service Charge (if applicable) */}
            {data.serviceCharge && data.serviceCharge > 0 && (
              <div className="flex justify-between items-center text-sm">
                <span className="text-muted-foreground">Service Charge</span>
                <span className="font-medium text-foreground">
                  {formatCurrency(data.serviceCharge, data.currency)}
                </span>
              </div>
            )}

            {/* Taxes */}
            <div className="flex justify-between items-center text-sm">
              <div className="flex items-center gap-1">
                <span className="text-muted-foreground">Taxes & Fees</span>
                <TooltipProvider>
                  <Tooltip>
                    <TooltipTrigger>
                      <Info className="w-3 h-3 text-muted-foreground" />
                    </TooltipTrigger>
                    <TooltipContent>
                      <p>Includes VAT and distribution charges</p>
                    </TooltipContent>
                  </Tooltip>
                </TooltipProvider>
              </div>
              <span className="font-medium text-foreground">
                {formatCurrency(data.taxes, data.currency)}
              </span>
            </div>

            {/* Subsidies (if applicable) */}
            {data.subsidies && data.subsidies > 0 && (
              <div className="flex justify-between items-center text-sm">
                <span className="text-green-600">Subsidies Applied</span>
                <span className="font-medium text-green-600">
                  -{formatCurrency(data.subsidies, data.currency)}
                </span>
              </div>
            )}
          </div>
        </div>

        <Separator className="my-3" />

        {/* Platform Service Charge */}
        {(data.platformServiceCharge || data.platformVat) && (
          <>
            <div className="space-y-3">
              <div className="flex items-center gap-2">
                <h3 className="text-sm font-semibold text-foreground uppercase tracking-wider">
                  Platform Service
                </h3>
                <TooltipProvider>
                  <Tooltip>
                    <TooltipTrigger>
                      <Info className="w-3 h-3 text-muted-foreground" />
                    </TooltipTrigger>
                    <TooltipContent>
                      <p className="max-w-xs">
                        3% service fee for secure blockchain payments, fraud detection, and platform maintenance
                      </p>
                    </TooltipContent>
                  </Tooltip>
                </TooltipProvider>
              </div>

              <div className="space-y-2">
                {data.platformServiceCharge && data.platformServiceCharge > 0 && (
                  <div className="flex justify-between items-center text-sm">
                    <span className="text-muted-foreground">Service Charge (3%)</span>
                    <span className="font-medium text-foreground">
                      {formatCurrency(data.platformServiceCharge, data.currency)}
                    </span>
                  </div>
                )}

                {data.platformVat && data.platformVat > 0 && (
                  <div className="flex justify-between items-center text-sm">
                    <span className="text-muted-foreground">VAT on Service</span>
                    <span className="font-medium text-foreground">
                      {formatCurrency(data.platformVat, data.currency)}
                    </span>
                  </div>
                )}
              </div>
            </div>

            <Separator className="my-3" />
          </>
        )}

        {/* Total in Fiat */}
        <div className="bg-gradient-to-br from-primary/5 to-primary/10 rounded-lg p-3 border border-primary/20">
          <div className="flex justify-between items-center">
            <span className="text-sm font-semibold text-foreground">Total Amount Due</span>
            <span className="text-xl font-bold text-primary">
              {formatCurrency(data.totalFiat, data.currency)}
            </span>
          </div>
        </div>

        {/* HBAR Conversion (if payment data available) */}
        {showHbarConversion && (
          <>
            <Separator />
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-semibold text-foreground uppercase tracking-wider">
                  HBAR Payment
                </h3>
                {!isLoadingRate && exchangeRate && (
                  <button
                    onClick={fetchExchangeRate}
                    className="text-xs text-muted-foreground hover:text-foreground transition-colors flex items-center gap-1"
                    title="Refresh exchange rate"
                  >
                    <RefreshCw className="w-3 h-3" />
                    Refresh
                  </button>
                )}
              </div>
              
              {isLoadingRate && (
                <div className="bg-purple-50 border border-purple-200 rounded-lg p-4 flex items-center justify-center">
                  <div className="flex items-center gap-2 text-purple-700">
                    <RefreshCw className="w-4 h-4 animate-spin" />
                    <span className="text-sm">Fetching exchange rate...</span>
                  </div>
                </div>
              )}

              {rateError && (
                <Alert variant="destructive">
                  <AlertCircle className="h-4 w-4" />
                  <AlertDescription>
                    {rateError}
                  </AlertDescription>
                </Alert>
              )}

              {!isLoadingRate && !rateError && exchangeRate && amountHbar !== null && (
                <>
                  {/* Rate Expiry Warning */}
                  {getExpiryStatus() === 'expired' && (
                    <Alert variant="destructive" className="border-red-300 bg-red-50">
                      <AlertCircle className="h-4 w-4" />
                      <AlertDescription className="flex items-center justify-between">
                        <span>Exchange rate expired. Please refresh to get the current rate.</span>
                        <button
                          onClick={fetchExchangeRate}
                          className="ml-2 px-3 py-1 bg-red-600 hover:bg-red-700 text-white text-xs rounded-md flex items-center gap-1 transition-colors"
                        >
                          <RefreshCw className="w-3 h-3" />
                          Refresh Now
                        </button>
                      </AlertDescription>
                    </Alert>
                  )}

                  {getExpiryStatus() === 'warning' && (
                    <Alert className="border-yellow-300 bg-yellow-50">
                      <Clock className="h-4 w-4 text-yellow-600" />
                      <AlertDescription className="text-yellow-800">
                        Rate expires soon! Complete payment quickly or refresh for a new rate.
                      </AlertDescription>
                    </Alert>
                  )}

                  <div className={`border rounded-lg p-4 space-y-2 transition-colors ${
                    getExpiryStatus() === 'expired' 
                      ? 'bg-gray-100 border-gray-300 opacity-60' 
                      : getExpiryStatus() === 'warning'
                      ? 'bg-yellow-50 border-yellow-300'
                      : 'bg-purple-50 border-purple-200'
                  }`}>
                    <div className="flex justify-between items-center">
                      <span className={`text-sm ${
                        getExpiryStatus() === 'expired' ? 'text-gray-600' : 'text-purple-900'
                      }`}>
                        HBAR Amount
                      </span>
                      <span className={`text-2xl font-bold ${
                        getExpiryStatus() === 'expired' ? 'text-gray-700 line-through' : 'text-purple-900'
                      }`}>
                        {amountHbar.toLocaleString(undefined, { 
                          minimumFractionDigits: 2, 
                          maximumFractionDigits: 8 
                        })} ℏ
                      </span>
                    </div>
                    
                    <div className={`flex justify-between items-center text-xs ${
                      getExpiryStatus() === 'expired' ? 'text-gray-600' : 'text-purple-700'
                    }`}>
                      <span>Exchange Rate</span>
                      <span>
                        1 ℏ = {formatCurrency(exchangeRate.hbarPrice, data.currency)}
                      </span>
                    </div>
                    
                    <div className={`flex justify-between items-center text-xs ${
                      getExpiryStatus() === 'expired' ? 'text-gray-600' : 'text-purple-700'
                    }`}>
                      <span>Rate Source</span>
                      <span className="capitalize">{exchangeRate.source}</span>
                    </div>
                    
                    <div className={`flex justify-between items-center text-xs ${
                      getExpiryStatus() === 'expired' ? 'text-gray-600' : 'text-purple-700'
                    }`}>
                      <span>Rate Fetched</span>
                      <span>
                        {rateFetchedAt?.toLocaleString()}
                      </span>
                    </div>

                    <Separator className="my-2" />

                    {/* Countdown Timer */}
                    <div className={`flex items-center justify-between p-2 rounded ${
                      getExpiryStatus() === 'expired'
                        ? 'bg-gray-200'
                        : getExpiryStatus() === 'warning'
                        ? 'bg-yellow-100'
                        : 'bg-purple-100'
                    }`}>
                      <div className="flex items-center gap-2">
                        <Clock className={`w-4 h-4 ${
                          getExpiryStatus() === 'expired'
                            ? 'text-gray-600'
                            : getExpiryStatus() === 'warning'
                            ? 'text-yellow-700'
                            : 'text-purple-700'
                        }`} />
                        <span className={`text-xs font-medium ${
                          getExpiryStatus() === 'expired'
                            ? 'text-gray-700'
                            : getExpiryStatus() === 'warning'
                            ? 'text-yellow-800'
                            : 'text-purple-800'
                        }`}>
                          {getExpiryStatus() === 'expired' ? 'Rate Expired' : 'Rate Expires In'}
                        </span>
                      </div>
                      <span className={`text-lg font-bold font-mono ${
                        getExpiryStatus() === 'expired'
                          ? 'text-gray-700'
                          : getExpiryStatus() === 'warning'
                          ? 'text-yellow-800'
                          : 'text-purple-800'
                      }`}>
                        {getExpiryStatus() === 'expired' ? '0:00' : formatTimeRemaining(timeRemaining)}
                      </span>
                    </div>
                  </div>
                  
                  {getExpiryStatus() === 'active' && (
                    <p className="text-xs text-muted-foreground">
                      Exchange rate locked for 5 minutes. Pay now to secure this rate.
                    </p>
                  )}

                  {/* Pay Now Button */}
                  {billId && (
                    <>
                      <Separator className="my-3" />
                      <div className="space-y-3">
                        <Button
                          onClick={handlePayNow}
                          disabled={isProcessingPayment || getExpiryStatus() === 'expired' || !amountHbar}
                          className="w-full h-12 text-base font-semibold bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                          size="lg"
                        >
                          {isProcessingPayment ? (
                            <>
                              <RefreshCw className="w-5 h-5 mr-2 animate-spin" />
                              Processing Payment...
                            </>
                          ) : (
                            <>
                              <Wallet className="w-5 h-5 mr-2" />
                              Pay Now with HashPack
                            </>
                          )}
                        </Button>

                        {getExpiryStatus() === 'expired' && (
                          <p className="text-xs text-center text-red-600">
                            Rate expired. Please refresh before paying.
                          </p>
                        )}

                        {!hashPack.isInstalled() && (
                          <Alert className="border-blue-300 bg-blue-50">
                            <Info className="h-4 w-4 text-blue-600" />
                            <AlertDescription className="text-blue-800 text-sm">
                              <div className="flex items-center justify-between">
                                <span>HashPack wallet not detected.</span>
                                <Button
                                  variant="outline"
                                  size="sm"
                                  className="ml-2 border-blue-600 text-blue-600 hover:bg-blue-100"
                                  onClick={() => window.open('https://www.hashpack.app/', '_blank')}
                                >
                                  Install HashPack
                                  <ExternalLink className="w-3 h-3 ml-1" />
                                </Button>
                              </div>
                            </AlertDescription>
                          </Alert>
                        )}

                        <div className="text-xs text-center text-muted-foreground space-y-1">
                          <p>
                            Transaction will be submitted to Hedera Testnet
                          </p>
                          <p>
                            Consensus time: 3-5 seconds
                          </p>
                        </div>
                      </div>
                    </>
                  )}
                </>
              )}
            </div>
          </>
        )}
      </CardContent>
      
      {/* Payment Confirmation Modal */}
      {confirmationData && (
        <PaymentConfirmationModal
          isOpen={showConfirmationModal}
          onClose={() => {
            setShowConfirmationModal(false);
            setConfirmationData(null);
          }}
          data={confirmationData}
          onDownloadReceipt={confirmationData.receiptUrl ? async () => {
            try {
              // Download receipt PDF
              const response = await fetch(confirmationData.receiptUrl!);
              const blob = await response.blob();
              const url = window.URL.createObjectURL(blob);
              const a = document.createElement('a');
              a.href = url;
              a.download = `receipt-${confirmationData.billId}.pdf`;
              document.body.appendChild(a);
              a.click();
              window.URL.revokeObjectURL(url);
              document.body.removeChild(a);
              toast.success('Receipt downloaded');
            } catch (error) {
              console.error('Failed to download receipt:', error);
              toast.error('Failed to download receipt');
            }
          } : undefined}
          onViewBillDetails={() => {
            setShowConfirmationModal(false);
            // Navigate to bill details page or trigger callback
            // This can be customized based on your routing setup
            toast.info('Viewing bill details...');
          }}
        />
      )}

      {/* Top Up Modal */}
      {insufficientBalanceData && exchangeRate && (
        <TopUpModal
          isOpen={showTopUpModal}
          onClose={() => {
            setShowTopUpModal(false);
            setInsufficientBalanceData(null);
          }}
          currentBalance={insufficientBalanceData.currentBalance}
          requiredAmount={insufficientBalanceData.requiredAmount}
          fiatAmount={data.totalFiat}
          currency={data.currency}
          exchangeRate={exchangeRate.hbarPrice}
          accountId={insufficientBalanceData.accountId}
          onBalanceRefresh={async () => {
            // Refresh balance from Hedera network
            const newBalance = await hashPack.checkBalance(insufficientBalanceData.accountId);
            if (newBalance !== null) {
              // Update insufficient balance data with new balance
              setInsufficientBalanceData({
                ...insufficientBalanceData,
                currentBalance: newBalance,
              });
            }
            return newBalance;
          }}
        />
      )}
    </Card>
  );
}
