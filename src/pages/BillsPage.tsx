import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Download, Check, Fingerprint, Shield } from "lucide-react";
import AppHeader from "@/components/AppHeader";

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
  const maxKwh = Math.max(...usageHistory.map((d) => d.kwh));

  const handlePay = () => {
    setPaying(true);
    setTimeout(() => {
      setPaying(false);
      setPaid(true);
    }, 2000);
  };

  return (
    <div className="min-h-screen bg-background pb-24">
      <AppHeader title="Bill Details" />

      <div className="px-5 space-y-5">
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
                <p className="text-sm text-muted-foreground mt-1">₦12,450 paid via Bank Transfer</p>
              </div>
              <div className="glass-card p-4 w-full space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">Reference</span>
                  <span className="text-foreground font-mono text-xs">HDF-2026-01-8473</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">Date</span>
                  <span className="text-foreground">Jan 15, 2026</span>
                </div>
              </div>
              <div className="flex gap-3 w-full pt-2">
                <button className="tap-scale flex-1 py-3 rounded-2xl border border-border text-foreground text-sm font-medium flex items-center justify-center gap-2">
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
                <p className="text-sm text-muted-foreground mt-1">Verify with biometrics to pay ₦12,450</p>
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

              {/* Bill Breakdown */}
              <div className="glass-card p-5 space-y-3">
                <h3 className="text-sm font-semibold text-foreground">Bill Breakdown</h3>
                {[
                  { label: "Energy (248 kWh × ₦45.50)", value: "₦11,284" },
                  { label: "Service Charge", value: "₦810" },
                  { label: "VAT (5%)", value: "₦356" },
                ].map((item, i) => (
                  <div key={i} className="flex justify-between text-sm">
                    <span className="text-muted-foreground">{item.label}</span>
                    <span className="text-foreground">{item.value}</span>
                  </div>
                ))}
                <div className="glow-line" />
                <div className="flex justify-between">
                  <span className="font-semibold text-foreground">Total</span>
                  <span className="text-xl font-bold text-accent">₦12,450</span>
                </div>
              </div>

              {/* Actions */}
              <button
                onClick={handlePay}
                className="tap-scale w-full py-4 rounded-2xl gradient-accent text-accent-foreground font-semibold text-base"
              >
                Pay Now — ₦12,450
              </button>

              <button className="tap-scale w-full py-3 rounded-2xl border border-border text-foreground font-medium text-sm flex items-center justify-center gap-2">
                <Download className="w-4 h-4" /> Download PDF
              </button>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
};

export default BillsPage;
