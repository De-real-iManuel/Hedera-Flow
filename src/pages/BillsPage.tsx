import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Download, Check, Fingerprint, Shield, Loader2, AlertCircle } from "lucide-react";
import AppHeader from "@/components/AppHeader";
import { BillBreakdown } from "@/components/BillBreakdown";
import { toast } from "sonner";
import { billsApi } from "@/lib/api";
import type { Bill } from "@/types/api";
import type { BillBreakdownData } from "@/components/BillBreakdown";

const usageHistory = [
  { month: "Jul", kwh: 198 },
  { month: "Aug", kwh: 232 },
  { month: "Sep", kwh: 210 },
  { month: "Oct", kwh: 245 },
  { month: "Nov", kwh: 228 },
  { month: "Dec", kwh: 248 },
];

const BillsPage = () => {
  const [paying, setPaying] = useState(false);
  const [paid, setPaid] = useState(false);
  const [transactionId, setTransactionId] = useState<string>("");
  const [bills, setBills] = useState<Bill[]>([]);
  const [selectedBill, setSelectedBill] = useState<Bill | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const maxKwh = Math.max(...usageHistory.map((d) => d.kwh));

  // Fetch bills on component mount
  useEffect(() => {
    fetchBills();
  }, []);

  const fetchBills = async () => {
    try {
      setIsLoading(true);
      setError(null);
      const fetchedBills = await billsApi.list();
      setBills(fetchedBills);
      
      // Select the first unpaid bill by default
      const unpaidBill = fetchedBills.find(b => b.status === 'pending' || b.status === 'overdue');
      if (unpaidBill) {
        setSelectedBill(unpaidBill);
      } else if (fetchedBills.length > 0) {
        setSelectedBill(fetchedBills[0]);
      }
    } catch (err: any) {
      console.error('Failed to fetch bills:', err);
      setError(err.response?.data?.detail || 'Failed to load bills');
      toast.error('Failed to load bills', {
        description: 'Please try again later',
      });
    } finally {
      setIsLoading(false);
    }
  };

  // Convert API Bill to BillBreakdownData format
  const getBillBreakdownData = (bill: Bill): BillBreakdownData | null => {
    if (!bill) return null;

    // Calculate charges from bill data
    const totalAmount = bill.amount_due;
    const vatRate = 0.075; // 7.5% VAT for Nigeria
    const serviceChargeRate = 0.065; // ~6.5% service charge
    const platformFeeRate = 0.03; // 3% platform service charge
    
    // Reverse calculate from total
    // Total = base + utility_taxes + service + platform_fee + platform_vat
    // Total = base * (1 + vat + service) * (1 + platform_fee * (1 + vat))
    
    // Simplified calculation for display
    const subtotal = totalAmount / (1 + platformFeeRate * (1 + vatRate));
    const baseCharge = subtotal / (1 + vatRate + serviceChargeRate);
    const taxes = baseCharge * vatRate;
    const serviceCharge = baseCharge * serviceChargeRate;
    const platformServiceCharge = subtotal * platformFeeRate;
    const platformVat = platformServiceCharge * vatRate;

    return {
      consumptionKwh: bill.consumption_kwh,
      baseCharge: Math.round(baseCharge),
      taxes: Math.round(taxes),
      serviceCharge: Math.round(serviceCharge),
      platformServiceCharge: Math.round(platformServiceCharge),
      platformVat: Math.round(platformVat),
      totalFiat: totalAmount,
      currency: bill.currency,
      rateStructureType: 'flat', // Default to flat, can be enhanced later
    };
  };

  const billData = selectedBill ? getBillBreakdownData(selectedBill) : null;

  const handlePaymentSuccess = (txId: string) => {
    setTransactionId(txId);
    setPaid(true);
    toast.success('Payment Successful!', {
      description: `Transaction ID: ${txId}`,
    });
    
    // Refresh bills to update status
    setTimeout(() => {
      fetchBills();
    }, 2000);
  };

  const handlePaymentError = (error: string) => {
    toast.error('Payment Failed', {
      description: error,
    });
  };

  return (
    <div className="min-h-screen bg-background pb-24">
      <AppHeader title="Bill Details" />

      <div className="px-5 space-y-5">
        {/* Loading State */}
        {isLoading && (
          <div className="flex flex-col items-center justify-center py-16 space-y-4">
            <Loader2 className="w-12 h-12 text-accent animate-spin" />
            <p className="text-sm text-muted-foreground">Loading bills...</p>
          </div>
        )}

        {/* Error State */}
        {error && !isLoading && (
          <div className="flex flex-col items-center justify-center py-16 space-y-4">
            <div className="w-16 h-16 rounded-full bg-destructive/10 flex items-center justify-center">
              <AlertCircle className="w-8 h-8 text-destructive" />
            </div>
            <div className="text-center space-y-2">
              <p className="text-lg font-semibold text-foreground">Failed to Load Bills</p>
              <p className="text-sm text-muted-foreground">{error}</p>
            </div>
            <button
              onClick={fetchBills}
              className="tap-scale px-6 py-3 rounded-2xl gradient-accent text-accent-foreground font-semibold text-sm"
            >
              Try Again
            </button>
          </div>
        )}

        {/* No Bills State */}
        {!isLoading && !error && bills.length === 0 && (
          <div className="flex flex-col items-center justify-center py-16 space-y-4">
            <div className="w-16 h-16 rounded-full bg-muted flex items-center justify-center">
              <Check className="w-8 h-8 text-muted-foreground" />
            </div>
            <div className="text-center space-y-2">
              <p className="text-lg font-semibold text-foreground">No Bills Found</p>
              <p className="text-sm text-muted-foreground">You don't have any bills yet</p>
            </div>
          </div>
        )}

        {/* Bills Content */}
        {!isLoading && !error && selectedBill && billData && (
          <AnimatePresence mode="wait">
          {paid ? (
            <motion.div
              key="success"
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              className="flex flex-col items-center py-12 space-y-5"
            >
              <div className="w-20 h-20 rounded-full bg-success/10 flex items-center justify-center">
                <Check className="w-10 h-10 text-success" />
              </div>
              <div className="text-center">
                <h2 className="text-2xl font-bold text-foreground">Payment Successful!</h2>
                <p className="text-sm text-muted-foreground mt-1">
                  {selectedBill.currency === 'NGN' ? '₦' : selectedBill.currency}
                  {selectedBill.amount_due.toLocaleString()} paid via HBAR
                </p>
              </div>
              <div className="glass-card p-4 w-full space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">Reference</span>
                  <span className="text-foreground font-mono text-xs">
                    {transactionId || "HDF-2026-01-8473"}
                  </span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">Date</span>
                  <span className="text-foreground">
                    {new Date().toLocaleDateString('en-US', { 
                      month: 'short', 
                      day: 'numeric', 
                      year: 'numeric' 
                    })}
                  </span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">Amount</span>
                  <span className="text-foreground font-semibold">
                    {selectedBill.currency === 'NGN' ? '₦' : selectedBill.currency}
                    {selectedBill.amount_due.toLocaleString()}
                  </span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">Bill Period</span>
                  <span className="text-foreground">
                    {new Date(selectedBill.billing_period_start).toLocaleDateString('en-US', { 
                      month: 'short', 
                      day: 'numeric' 
                    })} - {new Date(selectedBill.billing_period_end).toLocaleDateString('en-US', { 
                      month: 'short', 
                      day: 'numeric',
                      year: 'numeric'
                    })}
                  </span>
                </div>
              </div>
              <div className="flex gap-3 w-full pt-2">
                <button 
                  onClick={async () => {
                    if (!selectedBill) return;
                    try {
                      // Download receipt PDF
                      const response = await fetch(`/api/payments/${selectedBill.id}/receipt`, {
                        headers: {
                          'Authorization': `Bearer ${localStorage.getItem('token')}`,
                        },
                      });
                      
                      if (!response.ok) {
                        throw new Error('Failed to download receipt');
                      }
                      
                      const blob = await response.blob();
                      const url = window.URL.createObjectURL(blob);
                      const a = document.createElement('a');
                      a.href = url;
                      a.download = `hedera-flow-receipt-${selectedBill.id.substring(0, 8)}.pdf`;
                      document.body.appendChild(a);
                      a.click();
                      window.URL.revokeObjectURL(url);
                      document.body.removeChild(a);
                      toast.success('Receipt downloaded');
                    } catch (error) {
                      console.error('Failed to download receipt:', error);
                      toast.error('Failed to download receipt');
                    }
                  }}
                  className="tap-scale flex-1 py-3 rounded-2xl border border-border text-foreground text-sm font-medium flex items-center justify-center gap-2"
                >
                  <Download className="w-4 h-4" /> Receipt
                </button>
                <button
                  onClick={() => setPaid(false)}
                  className="tap-scale flex-1 py-3 rounded-2xl gradient-accent text-accent-foreground text-sm font-semibold"
                >
                  Done
                </button>
              </div>
            </motion.div>
          ) : paying ? (
            <motion.div
              key="paying"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="flex flex-col items-center py-16 space-y-6"
            >
              <div className="w-20 h-20 rounded-full bg-accent/10 flex items-center justify-center">
                <Fingerprint className="w-10 h-10 text-accent animate-pulse" />
              </div>
              <div className="text-center">
                <p className="text-lg font-semibold text-foreground">Confirm Payment</p>
                <p className="text-sm text-muted-foreground mt-1">
                  Verify with biometrics to pay {selectedBill.currency === 'NGN' ? '₦' : selectedBill.currency}
                  {selectedBill.amount_due.toLocaleString()}
                </p>
              </div>
              <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
                <Shield className="w-3.5 h-3.5" />
                <span>Secured with end-to-end encryption</span>
              </div>
            </motion.div>
          ) : (
            <motion.div
              key="details"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="space-y-5"
            >
              {/* Usage Graph */}
              <div className="glass-card-elevated p-5">
                <h3 className="text-sm font-semibold text-foreground mb-4">Usage History (kWh)</h3>
                <div className="flex items-end gap-2 h-28">
                  {usageHistory.map((d, i) => (
                    <div key={i} className="flex-1 flex flex-col items-center gap-1.5">
                      <span className="text-[10px] font-medium text-accent">{d.kwh}</span>
                      <div
                        className="w-full rounded-lg transition-all"
                        style={{
                          height: `${(d.kwh / maxKwh) * 100}%`,
                          background:
                            i === usageHistory.length - 1
                              ? "linear-gradient(180deg, hsl(217 100% 50%), hsl(200 100% 50%))"
                              : "hsl(217 100% 50% / 0.15)",
                        }}
                      />
                      <span className="text-[10px] text-muted-foreground">{d.month}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Bill Breakdown with Pay Now Button */}
              <BillBreakdown
                data={billData}
                showHbarConversion={true}
                billId={selectedBill.id}
                utilityAccountId="0.0.999999"
                onPaymentSuccess={handlePaymentSuccess}
                onPaymentError={handlePaymentError}
              />

              {/* Download PDF Button */}
              <button className="tap-scale w-full py-3 rounded-2xl border border-border text-foreground font-medium text-sm flex items-center justify-center gap-2">
                <Download className="w-4 h-4" /> Download PDF
              </button>
            </motion.div>
          )}
        </AnimatePresence>
        )}
      </div>
    </div>
  );
};

export default BillsPage;
