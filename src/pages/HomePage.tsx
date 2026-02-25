import { motion } from "framer-motion";
import { ScanLine, CreditCard, Clock, Zap, TrendingUp, Calendar } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import AppHeader from "@/components/AppHeader";
import { authApi } from "@/lib/api";

const fade = (delay = 0) => ({
  initial: { opacity: 0, y: 16 },
  animate: { opacity: 1, y: 0 },
  transition: { duration: 0.4, delay, ease: "easeOut" as const },
});

const HomePage = () => {
  const navigate = useNavigate();

  // Fetch current user data
  const { data: user, isLoading: userLoading } = useQuery({
    queryKey: ['user'],
    queryFn: authApi.getCurrentUser,
    enabled: !!localStorage.getItem('auth_token'),
  });

  // TODO: Fetch bills data from API
  // const { data: bills } = useQuery({
  //   queryKey: ['bills'],
  //   queryFn: billsApi.getCurrentBill,
  // });

  // TODO: Fetch usage data from API
  // const { data: usage } = useQuery({
  //   queryKey: ['usage'],
  //   queryFn: metersApi.getUsageHistory,
  // });

  // Placeholder data until API is integrated
  const usageData = [32, 45, 38, 52, 48, 60];
  const months = ["Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  const maxUsage = Math.max(...usageData);

  // Get user's first name
  const firstName = user?.email?.split('@')[0] || 'User';

  if (userLoading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-accent border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-sm text-muted-foreground">Loading...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background pb-24">
      <AppHeader />

      <div className="px-5 space-y-5">
        {/* Greeting */}
        <motion.div {...fade(0)}>
          <h1 className="text-2xl font-bold text-foreground">
            Welcome back, <span className="text-accent">{firstName}</span>
          </h1>
          <p className="text-sm text-muted-foreground mt-0.5">Your electricity at a glance</p>
        </motion.div>

        {/* Current Bill Card - TODO: Replace with live data */}
        <motion.div {...fade(0.1)} className="glass-card-elevated p-5 relative overflow-hidden">
          <div className="absolute top-0 left-0 right-0 h-1 gradient-accent rounded-t-2xl" />
          <div className="flex items-start justify-between mb-4">
            <div>
              <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider">Current Bill</p>
              <p className="text-3xl font-bold text-foreground mt-1">₦0.00</p>
              <p className="text-xs text-muted-foreground mt-1">No bills yet</p>
            </div>
            <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-muted/50">
              <Calendar className="w-3.5 h-3.5 text-muted-foreground" />
              <span className="text-xs font-medium text-muted-foreground">--</span>
            </div>
          </div>

          {/* Mini usage chart - TODO: Replace with live data */}
          <div className="flex items-end gap-1.5 h-16 mb-3">
            {usageData.map((val, i) => (
              <div key={i} className="flex-1 flex flex-col items-center gap-1">
                <div
                  className="w-full rounded-md transition-all duration-300"
                  style={{
                    height: `${(val / maxUsage) * 100}%`,
                    background: i === usageData.length - 1
                      ? "hsl(217 100% 50%)"
                      : "hsl(217 100% 50% / 0.2)",
                  }}
                />
                <span className="text-[9px] text-muted-foreground">{months[i]}</span>
              </div>
            ))}
          </div>

          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <TrendingUp className="w-3.5 h-3.5 text-accent" />
            <span>Start scanning your meter to see usage data</span>
          </div>
        </motion.div>

        {/* Quick Actions */}
        <motion.div {...fade(0.2)} className="grid grid-cols-3 gap-3">
          {[
            { icon: ScanLine, label: "Scan Meter", path: "/scan", accent: true },
            { icon: CreditCard, label: "Pay Bill", path: "/bills", accent: false },
            { icon: Clock, label: "History", path: "/history", accent: false },
          ].map(({ icon: Icon, label, path, accent }) => (
            <button
              key={path}
              onClick={() => navigate(path)}
              className={`tap-scale glass-card p-4 flex flex-col items-center gap-2.5 ${
                accent ? "border-accent/30 bg-accent/5" : ""
              }`}
            >
              <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${
                accent ? "gradient-accent" : "bg-secondary"
              }`}>
                <Icon className={`w-5 h-5 ${accent ? "text-accent-foreground" : "text-foreground"}`} />
              </div>
              <span className="text-xs font-medium text-foreground">{label}</span>
            </button>
          ))}
        </motion.div>

        {/* Getting Started Guide */}
        <motion.div {...fade(0.3)}>
          <h2 className="text-sm font-semibold text-foreground mb-3">Getting Started</h2>
          <div className="space-y-2.5">
            <div className="glass-card p-3.5 flex items-center gap-3">
              <div className="w-9 h-9 rounded-xl flex items-center justify-center shrink-0 bg-accent/10">
                <ScanLine className="w-4 h-4 text-accent" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-foreground">Add Your Meter</p>
                <p className="text-xs text-muted-foreground">Register your electricity meter to get started</p>
              </div>
              <button
                onClick={() => navigate('/meters')}
                className="text-xs font-medium text-accent hover:underline"
              >
                Add
              </button>
            </div>
            <div className="glass-card p-3.5 flex items-center gap-3">
              <div className="w-9 h-9 rounded-xl flex items-center justify-center shrink-0 bg-accent/10">
                <Zap className="w-4 h-4 text-accent" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-foreground">Scan Your Reading</p>
                <p className="text-xs text-muted-foreground">Use AI to verify your meter reading</p>
              </div>
              <button
                onClick={() => navigate('/scan')}
                className="text-xs font-medium text-accent hover:underline"
              >
                Scan
              </button>
            </div>
          </div>
        </motion.div>
      </div>
    </div>
  );
};

export default HomePage;
