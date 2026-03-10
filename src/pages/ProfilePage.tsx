import { motion } from "framer-motion";
import { Bell, Moon, HelpCircle, Shield, ChevronRight, LogOut, Wallet, Zap } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { useState, useEffect } from "react";
import { toast } from "sonner";
import AppHeader from "@/components/AppHeader";
import { useAuth } from "@/hooks/useAuth";
import { useMeters } from "@/hooks/useMeters";
import { userApi, UserPreferences } from "@/lib/api";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog";
import WalletConnect from "@/components/WalletConnect";

const ProfilePage = () => {
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const { meters } = useMeters();
  const [preferences, setPreferences] = useState<UserPreferences | null>(null);
  const [isDarkMode, setIsDarkMode] = useState(false);
  const [showWalletDialog, setShowWalletDialog] = useState(false);
  
  // Get user initials
  const getInitials = () => {
    if (user?.first_name && user?.last_name) {
      return `${user.first_name[0]}${user.last_name[0]}`.toUpperCase();
    }
    if (user?.email) {
      return user.email.substring(0, 2).toUpperCase();
    }
    return "U";
  };
  
  // Get full name
  const getFullName = () => {
    if (user?.first_name && user?.last_name) {
      return `${user.first_name} ${user.last_name}`;
    }
    return user?.email || "User";
  };
  
  // Get primary meter or first meter
  const primaryMeter = meters?.find(m => m.is_primary) || meters?.[0];

  // Load user preferences
  useEffect(() => {
    const loadPreferences = async () => {
      try {
        const prefs = await userApi.getPreferences();
        setPreferences(prefs);
        setIsDarkMode(prefs.theme === 'dark');
      } catch (error) {
        console.error('Failed to load preferences:', error);
      }
    };
    loadPreferences();
  }, []);

  // Toggle dark mode
  const handleDarkModeToggle = async () => {
    if (!preferences) return;
    
    const newTheme = isDarkMode ? 'light' : 'dark';
    setIsDarkMode(!isDarkMode);
    
    try {
      await userApi.updatePreferences({
        ...preferences,
        theme: newTheme,
      });
      toast.success(`${newTheme === 'dark' ? 'Dark' : 'Light'} mode enabled`);
    } catch (error) {
      console.error('Failed to update theme:', error);
      setIsDarkMode(isDarkMode); // Revert on error
      toast.error('Failed to update theme');
    }
  };

  // Open wallet connect dialog
  const handleWalletConnect = () => {
    setShowWalletDialog(true);
  };

  // Navigate to notifications settings
  const handleNotifications = () => {
    navigate('/settings/notifications');
  };

  // Navigate to security settings
  const handleSecurity = () => {
    navigate('/settings/security');
  };

  // Navigate to help
  const handleHelp = () => {
    navigate('/help');
  };

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
            <span className="text-xl font-bold text-primary-foreground">{getInitials()}</span>
          </div>
          <div className="flex-1">
            <h2 className="text-lg font-bold text-foreground">{getFullName()}</h2>
            <p className="text-sm text-muted-foreground">{user?.email}</p>
            {primaryMeter && (
              <p className="text-xs text-accent mt-0.5">Meter ID: {primaryMeter.meter_id}</p>
            )}
          </div>
        </motion.div>

        {/* Wallet */}
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.05 }}
        >
          <button 
            onClick={handleWalletConnect}
            className="tap-scale w-full glass-card p-4 flex items-center gap-3"
          >
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
          <button
            onClick={handleNotifications}
            className="tap-scale w-full p-4 flex items-center gap-3 border-b border-border/30"
          >
            <div className="w-9 h-9 rounded-xl bg-secondary flex items-center justify-center shrink-0">
              <Bell className="w-4 h-4 text-foreground" />
            </div>
            <div className="flex-1 text-left">
              <p className="text-sm font-medium text-foreground">Notifications</p>
              <p className="text-xs text-muted-foreground">Bill reminders & alerts</p>
            </div>
            <ChevronRight className="w-4 h-4 text-muted-foreground" />
          </button>

          <button
            onClick={handleDarkModeToggle}
            className="tap-scale w-full p-4 flex items-center gap-3 border-b border-border/30"
          >
            <div className="w-9 h-9 rounded-xl bg-secondary flex items-center justify-center shrink-0">
              <Moon className="w-4 h-4 text-foreground" />
            </div>
            <div className="flex-1 text-left">
              <p className="text-sm font-medium text-foreground">Dark Mode</p>
              <p className="text-xs text-muted-foreground">Switch appearance</p>
            </div>
            <div className={`w-10 h-6 rounded-full relative transition-colors ${isDarkMode ? 'bg-accent' : 'bg-border'}`}>
              <div className={`absolute top-1 w-4 h-4 rounded-full bg-card shadow-sm transition-transform ${isDarkMode ? 'left-5' : 'left-1'}`} />
            </div>
          </button>

          <button
            onClick={handleSecurity}
            className="tap-scale w-full p-4 flex items-center gap-3 border-b border-border/30"
          >
            <div className="w-9 h-9 rounded-xl bg-secondary flex items-center justify-center shrink-0">
              <Shield className="w-4 h-4 text-foreground" />
            </div>
            <div className="flex-1 text-left">
              <p className="text-sm font-medium text-foreground">Security</p>
              <p className="text-xs text-muted-foreground">Biometric & PIN settings</p>
            </div>
            <ChevronRight className="w-4 h-4 text-muted-foreground" />
          </button>

          <button
            onClick={handleHelp}
            className="tap-scale w-full p-4 flex items-center gap-3"
          >
            <div className="w-9 h-9 rounded-xl bg-secondary flex items-center justify-center shrink-0">
              <HelpCircle className="w-4 h-4 text-foreground" />
            </div>
            <div className="flex-1 text-left">
              <p className="text-sm font-medium text-foreground">Help & FAQ</p>
              <p className="text-xs text-muted-foreground">Support center</p>
            </div>
            <ChevronRight className="w-4 h-4 text-muted-foreground" />
          </button>
        </motion.div>

        {/* Logout */}
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.15 }}
        >
          <button 
            onClick={logout}
            className="tap-scale w-full p-4 rounded-2xl border border-destructive/20 text-destructive flex items-center justify-center gap-2 text-sm font-medium"
          >
            <LogOut className="w-4 h-4" />
            Sign Out
          </button>
        </motion.div>
      </div>

      {/* Wallet Connect Dialog */}
      <Dialog open={showWalletDialog} onOpenChange={setShowWalletDialog}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Connect Wallet</DialogTitle>
            <DialogDescription>
              Connect your MetaMask wallet to enable HBAR payments for prepaid tokens
            </DialogDescription>
          </DialogHeader>
          <div className="py-4">
            <WalletConnect />
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default ProfilePage;
