import { motion } from "framer-motion";
import { Check, Lock, ChevronDown, Zap, Image } from "lucide-react";
import { useState } from "react";
import AppHeader from "@/components/AppHeader";

const bills = [
  { id: 1, month: "December 2025", kwh: 248, amount: "₦12,450", status: "paid", date: "Jan 15, 2026", ref: "HDF-2026-01-8473" },
  { id: 2, month: "November 2025", kwh: 228, amount: "₦9,800", status: "paid", date: "Dec 12, 2025", ref: "HDF-2025-12-7391" },
  { id: 3, month: "October 2025", kwh: 245, amount: "₦11,100", status: "paid", date: "Nov 10, 2025", ref: "HDF-2025-11-6204" },
  { id: 4, month: "September 2025", kwh: 210, amount: "₦8,950", status: "paid", date: "Oct 8, 2025", ref: "HDF-2025-10-5127" },
  { id: 5, month: "August 2025", kwh: 232, amount: "₦10,200", status: "paid", date: "Sep 5, 2025", ref: "HDF-2025-09-4088" },
];

const HistoryPage = () => {
  const [expanded, setExpanded] = useState<number | null>(null);

  return (
    <div className="min-h-screen bg-background pb-24">
      <AppHeader title="Bill History" />

      <div className="px-5 space-y-3">
        <div className="flex items-center gap-2 mb-2">
          <Lock className="w-3.5 h-3.5 text-success" />
          <span className="text-xs text-muted-foreground">All records are immutable & audit-proof</span>
        </div>

        {bills.map((bill, i) => (
          <motion.div
            key={bill.id}
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.06 }}
          >
            <button
              onClick={() => setExpanded(expanded === bill.id ? null : bill.id)}
              className="w-full glass-card p-4 text-left tap-scale"
            >
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 rounded-xl bg-success/10 flex items-center justify-center shrink-0">
                  <Check className="w-4 h-4 text-success" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-foreground">{bill.month}</p>
                  <p className="text-xs text-muted-foreground">{bill.kwh} kWh · Paid {bill.date}</p>
                </div>
                <span className="text-sm font-semibold text-foreground">{bill.amount}</span>
                <ChevronDown
                  className={`w-4 h-4 text-muted-foreground transition-transform duration-200 ${
                    expanded === bill.id ? "rotate-180" : ""
                  }`}
                />
              </div>

              {expanded === bill.id && (
                <motion.div
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: "auto", opacity: 1 }}
                  className="mt-3 pt-3 border-t border-border/50 space-y-2"
                >
                  <div className="flex justify-between text-xs">
                    <span className="text-muted-foreground">Reference</span>
                    <span className="text-foreground font-mono">{bill.ref}</span>
                  </div>
                  <div className="flex justify-between text-xs">
                    <span className="text-muted-foreground">Verified Reading</span>
                    <span className="text-foreground">{bill.kwh} kWh</span>
                  </div>
                  <div className="flex items-center gap-2 text-xs text-muted-foreground">
                    <Image className="w-3.5 h-3.5" />
                    <span>Meter photo on file</span>
                    <Lock className="w-3 h-3 text-success ml-auto" />
                    <span className="text-success">Verified</span>
                  </div>
                </motion.div>
              )}
            </button>
          </motion.div>
        ))}

        <div className="pt-4 flex items-center justify-center gap-2 text-xs text-muted-foreground">
          <Zap className="w-3.5 h-3.5 text-accent" />
          <span>5 verified bills · Total ₦52,500 paid</span>
        </div>
      </div>
    </div>
  );
};

export default HistoryPage;
