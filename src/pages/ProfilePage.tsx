import { motion } from "framer-motion";
import { User, Bell, Moon, HelpCircle, Shield, ChevronRight, LogOut, Wallet, Zap } from "lucide-react";
import { useNavigate } from "react-router-dom";
import AppHeader from "@/components/AppHeader";

const ProfilePage = () => {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-background pb-24">
      <AppHeader title="Profile" />

      <div className="px-5 space-y-5">
        {/* User Info */}
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          className="glass-card-elevated p-5 flex items-center gap-4"
        >
          <div className="w-14 h-14 rounded-full gradient-navy flex items-center justify-center">
            <span className="text-xl font-bold text-primary-foreground">EA</span>
          </div>
          <div className="flex-1">
            <h2 className="text-lg font-bold text-foreground">Emmanuel Nwajari</h2>
            <p className="text-sm text-muted-foreground">emmanuel@email.com</p>
            <p className="text-xs text-accent mt-0.5">Meter ID: MTR-LG-0847291</p>
          </div>
        </motion.div>

        {/* Wallet */}
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.05 }}
        >
          <button className="tap-scale w-full glass-card p-4 flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-accent/10 flex items-center justify-center">
              <Wallet className="w-5 h-5 text-accent" />
            </div>
            <div className="flex-1 text-left">
              <p className="text-sm font-medium text-foreground">Connect Secure Wallet</p>
              <p className="text-xs text-muted-foreground">Link payment method for quick pay</p>
            </div>
            <ChevronRight className="w-4 h-4 text-muted-foreground" />
          </button>
        </motion.div>

        {/* My Meters */}
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.08 }}
        >
          <button 
            onClick={() => navigate('/meters')}
            className="tap-scale w-full glass-card p-4 flex items-center gap-3"
          >
            <div className="w-10 h-10 rounded-xl bg-blue-500/10 flex items-center justify-center">
              <Zap className="w-5 h-5 text-blue-500" />
            </div>
            <div className="flex-1 text-left">
              <p className="text-sm font-medium text-foreground">My Meters</p>
              <p className="text-xs text-muted-foreground">View and manage registered meters</p>
            </div>
            <ChevronRight className="w-4 h-4 text-muted-foreground" />
          </button>
        </motion.div>

        {/* Settings */}
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="glass-card overflow-hidden"
        >
          {[
            { icon: Bell, label: "Notifications", desc: "Bill reminders & alerts" },
            { icon: Moon, label: "Dark Mode", desc: "Switch appearance", toggle: true },
            { icon: Shield, label: "Security", desc: "Biometric & PIN settings" },
            { icon: HelpCircle, label: "Help & FAQ", desc: "Support center" },
          ].map((item, i) => (
            <button
              key={i}
              className="tap-scale w-full p-4 flex items-center gap-3 border-b border-border/30 last:border-0"
            >
              <div className="w-9 h-9 rounded-xl bg-secondary flex items-center justify-center shrink-0">
                <item.icon className="w-4 h-4 text-foreground" />
              </div>
              <div className="flex-1 text-left">
                <p className="text-sm font-medium text-foreground">{item.label}</p>
                <p className="text-xs text-muted-foreground">{item.desc}</p>
              </div>
              {item.toggle ? (
                <div className="w-10 h-6 rounded-full bg-border relative">
                  <div className="absolute top-1 left-1 w-4 h-4 rounded-full bg-card shadow-sm" />
                </div>
              ) : (
                <ChevronRight className="w-4 h-4 text-muted-foreground" />
              )}
            </button>
          ))}
        </motion.div>

        {/* Logout */}
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.15 }}
        >
          <button className="tap-scale w-full p-4 rounded-2xl border border-destructive/20 text-destructive flex items-center justify-center gap-2 text-sm font-medium">
            <LogOut className="w-4 h-4" />
            Sign Out
          </button>
        </motion.div>
      </div>
    </div>
  );
};

export default ProfilePage;
