/**
 * BillBreakdown Component - Usage Example
 * 
 * This example demonstrates how to use the BillBreakdown component
 * with the Pay Now button for HBAR payments.
 */

import { BillBreakdown } from './BillBreakdown';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { toast } from 'sonner';

export function BillBreakdownExample() {
  const navigate = useNavigate();
  const [paymentStatus, setPaymentStatus] = useState<'idle' | 'processing' | 'success' | 'error'>('idle');

  // Example bill data
  const billData = {
    consumptionKwh: 500,
    baseCharge: 70.5,
    taxes: 14.9,
    totalFiat: 85.4,
    currency: 'EUR',
    rateStructureType: 'tiered' as const,
    rateDetails: {
      tiers: [
        { name: 'Tier 1 (0-300 kWh)', kwh: 300, rate: 0.12, amount: 36.0 },
        { name: 'Tier 2 (301-500 kWh)', kwh: 200, rate: 0.15, amount: 30.0 },
      ],
    },
  };

  const handlePaymentSuccess = (transactionId: string) => {
    setPaymentStatus('success');
    
    toast.success('Payment Successful!', {
      description: `Transaction ID: ${transactionId}`,
      action: {
        label: 'View Receipt',
        onClick: () => navigate(`/receipts/${transactionId}`),
      },
    });

    // Navigate to receipt page after 2 seconds
    setTimeout(() => {
      navigate(`/receipts/${transactionId}`);
    }, 2000);
  };

  const handlePaymentError = (error: string) => {
    setPaymentStatus('error');
    
    toast.error('Payment Failed', {
      description: error,
      action: {
        label: 'Try Again',
        onClick: () => setPaymentStatus('idle'),
      },
    });
  };

  return (
    <div className="max-w-2xl mx-auto p-6 space-y-6">
      <div className="space-y-2">
        <h1 className="text-3xl font-bold">Bill Payment</h1>
        <p className="text-muted-foreground">
          Review your bill and pay with HBAR
        </p>
      </div>

      {/* Bill Breakdown with Pay Now Button */}
      <BillBreakdown
        data={billData}
        showHbarConversion={true}
        billId="BILL-ES-2024-001"
        utilityAccountId="0.0.999999" // Utility provider's Hedera account
        userAccountId="0.0.123456" // User's Hedera account (optional)
        onPaymentSuccess={handlePaymentSuccess}
        onPaymentError={handlePaymentError}
      />

      {/* Payment Status */}
      {paymentStatus === 'success' && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-4">
          <p className="text-green-800 font-medium">
            ✓ Payment successful! Redirecting to receipt...
          </p>
        </div>
      )}

      {paymentStatus === 'error' && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800 font-medium">
            ✗ Payment failed. Please try again.
          </p>
        </div>
      )}
    </div>
  );
}

/**
 * Example: Without Payment (View Only)
 */
export function BillBreakdownViewOnly() {
  const billData = {
    consumptionKwh: 500,
    baseCharge: 70.5,
    taxes: 14.9,
    totalFiat: 85.4,
    currency: 'EUR',
    rateStructureType: 'flat' as const,
  };

  return (
    <div className="max-w-2xl mx-auto p-6">
      {/* Bill Breakdown without Pay Now button (no billId) */}
      <BillBreakdown
        data={billData}
        showHbarConversion={true}
        // No billId = no Pay Now button
      />
    </div>
  );
}

/**
 * Example: With HBAR Conversion but No Payment
 */
export function BillBreakdownWithConversion() {
  const billData = {
    consumptionKwh: 500,
    baseCharge: 70.5,
    taxes: 14.9,
    totalFiat: 85.4,
    currency: 'USD',
    rateStructureType: 'time_of_use' as const,
    rateDetails: {
      periods: [
        { name: 'peak', hours: [10, 11, 12, 13, 14, 18, 19, 20, 21], rate: 0.40, kwh: 150, amount: 60.0 },
        { name: 'off-peak', hours: [0, 1, 2, 3, 4, 5, 6, 7], rate: 0.15, kwh: 350, amount: 52.5 },
      ],
    },
  };

  return (
    <div className="max-w-2xl mx-auto p-6">
      {/* Shows HBAR conversion but no payment button */}
      <BillBreakdown
        data={billData}
        showHbarConversion={true}
      />
    </div>
  );
}

/**
 * Example: Nigeria Band-Based Tariff with Payment
 */
export function BillBreakdownNigeria() {
  const navigate = useNavigate();

  const billData = {
    consumptionKwh: 300,
    baseCharge: 12000,
    taxes: 900,
    serviceCharge: 1500,
    totalFiat: 14400,
    currency: 'NGN',
    rateStructureType: 'band_based' as const,
    rateDetails: {
      band: {
        name: 'Band A',
        rate: 225.0,
        hoursMin: 20,
      },
    },
  };

  return (
    <div className="max-w-2xl mx-auto p-6">
      <BillBreakdown
        data={billData}
        showHbarConversion={true}
        billId="BILL-NG-2024-001"
        utilityAccountId="0.0.888888"
        onPaymentSuccess={(txId) => {
          toast.success('Payment Successful!');
          navigate(`/receipts/${txId}`);
        }}
        onPaymentError={(error) => {
          toast.error('Payment Failed', { description: error });
        }}
      />
    </div>
  );
}
