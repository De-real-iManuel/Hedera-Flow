/**
 * Payment Confirmation Modal - Example Usage
 * 
 * This file demonstrates how to use the PaymentConfirmationModal component
 * with real data from a successful HashPack payment.
 */

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { PaymentConfirmationModal, type PaymentConfirmationData } from './PaymentConfirmationModal';
import { toast } from 'sonner';

export function PaymentConfirmationModalExample() {
  const [showModal, setShowModal] = useState(false);

  // Example payment confirmation data (from backend after successful payment)
  const exampleData: PaymentConfirmationData = {
    // Transaction details from Hedera
    transactionId: '0.0.123456@1708254600.123456',
    consensusTimestamp: '2026-02-18T10:30:05.123Z',
    
    // Payment amounts
    amountHbar: 251.17647059,
    amountFiat: 85.40,
    currency: 'EUR',
    
    // Exchange rate used
    exchangeRate: 0.34,
    exchangeRateSource: 'coingecko',
    
    // Bill details
    billId: 'bill-abc123',
    consumptionKwh: 250.5,
    
    // Receipt URL
    receiptUrl: '/api/payments/bill-abc123/receipt',
  };

  const handleDownloadReceipt = async () => {
    try {
      // In real implementation, this would fetch the PDF from the backend
      toast.success('Receipt downloaded successfully');
      console.log('Downloading receipt from:', exampleData.receiptUrl);
    } catch (error) {
      toast.error('Failed to download receipt');
      console.error('Download error:', error);
    }
  };

  const handleViewBillDetails = () => {
    // In real implementation, this would navigate to the bill details page
    toast.info('Navigating to bill details...');
    console.log('Viewing bill:', exampleData.billId);
    setShowModal(false);
  };

  return (
    <div className="p-8 space-y-4">
      <h1 className="text-2xl font-bold">Payment Confirmation Modal Example</h1>
      
      <div className="space-y-2">
        <p className="text-muted-foreground">
          This example demonstrates the payment confirmation modal that appears
          after a successful HashPack transaction.
        </p>
        
        <Button onClick={() => setShowModal(true)}>
          Show Payment Confirmation
        </Button>
      </div>

      <div className="bg-muted p-4 rounded-lg space-y-2">
        <h2 className="font-semibold">Example Data:</h2>
        <pre className="text-xs overflow-auto">
          {JSON.stringify(exampleData, null, 2)}
        </pre>
      </div>

      <PaymentConfirmationModal
        isOpen={showModal}
        onClose={() => setShowModal(false)}
        data={exampleData}
        onDownloadReceipt={handleDownloadReceipt}
        onViewBillDetails={handleViewBillDetails}
      />
    </div>
  );
}

/**
 * Integration with BillBreakdown Component
 * 
 * The modal is integrated into the BillBreakdown component's payment flow:
 * 
 * 1. User clicks "Pay Now with HashPack"
 * 2. HashPack wallet opens for transaction signing
 * 3. User approves and signs the transaction
 * 4. Transaction is submitted to Hedera network
 * 5. Backend confirms payment and returns receipt data
 * 6. PaymentConfirmationModal is shown with transaction details
 * 
 * Example integration code:
 * 
 * ```typescript
 * const [showConfirmationModal, setShowConfirmationModal] = useState(false);
 * const [confirmationData, setConfirmationData] = useState<PaymentConfirmationData | null>(null);
 * 
 * const handlePaymentSuccess = async (transactionId: string) => {
 *   // Fetch payment details from backend
 *   const paymentDetails = await paymentsApi.get(billId);
 *   
 *   // Prepare confirmation data
 *   const confirmData: PaymentConfirmationData = {
 *     transactionId: transactionId,
 *     consensusTimestamp: paymentDetails.consensus_timestamp,
 *     amountHbar: paymentDetails.amount_hbar,
 *     amountFiat: paymentDetails.amount_fiat,
 *     currency: paymentDetails.currency,
 *     exchangeRate: paymentDetails.exchange_rate,
 *     exchangeRateSource: 'coingecko',
 *     billId: billId,
 *     consumptionKwh: data.consumptionKwh,
 *     receiptUrl: paymentDetails.receipt_url,
 *   };
 *   
 *   setConfirmationData(confirmData);
 *   setShowConfirmationModal(true);
 * };
 * 
 * return (
 *   <>
 *     <BillBreakdown
 *       data={billData}
 *       showHbarConversion={true}
 *       billId={billId}
 *       onPaymentSuccess={handlePaymentSuccess}
 *     />
 *     
 *     {confirmationData && (
 *       <PaymentConfirmationModal
 *         isOpen={showConfirmationModal}
 *         onClose={() => setShowConfirmationModal(false)}
 *         data={confirmationData}
 *         onDownloadReceipt={handleDownloadReceipt}
 *         onViewBillDetails={handleViewBillDetails}
 *       />
 *     )}
 *   </>
 * );
 * ```
 */

/**
 * Data Pipeline Flow
 * 
 * 1. User initiates payment in BillBreakdown component
 * 2. HashPack wallet signs and submits transaction to Hedera
 * 3. Hedera network reaches consensus (3-5 seconds)
 * 4. Backend receives transaction ID and confirms payment
 * 5. Backend updates bill status to 'paid' in database
 * 6. Backend logs payment to HCS (Hedera Consensus Service)
 * 7. Backend returns PaymentReceipt with all details
 * 8. Frontend displays PaymentConfirmationModal with:
 *    - Transaction ID (with copy button)
 *    - HBAR amount paid
 *    - Fiat equivalent
 *    - Exchange rate used
 *    - Consensus timestamp
 *    - Link to HashScan explorer
 *    - Download receipt button
 *    - View bill details button
 */

/**
 * Real Data Integration Points
 * 
 * 1. Transaction ID: From HashPack wallet after signing
 * 2. Consensus Timestamp: From Hedera network via Mirror Node
 * 3. HBAR Amount: Calculated from exchange rate at payment time
 * 4. Fiat Amount: From bill total
 * 5. Exchange Rate: From CoinGecko/CoinMarketCap API (cached in Redis)
 * 6. Receipt URL: Generated by backend for PDF download
 * 
 * All data is stored in the database and logged to HCS for immutable audit trail.
 */
