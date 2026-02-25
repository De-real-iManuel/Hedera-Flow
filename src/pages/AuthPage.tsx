import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Mail, Lock, MapPin, ArrowRight, Eye, EyeOff } from "lucide-react";
import { useAuth } from "@/hooks/useAuth";
import { toast } from "sonner";
import logo from "@/assets/hedera-flow-logo.png";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

const countries = [
  { code: "ES", name: "Spain", flag: "🇪🇸" },
  { code: "US", name: "United States", flag: "🇺🇸" },
  { code: "IN", name: "India", flag: "🇮🇳" },
  { code: "BR", name: "Brazil", flag: "🇧🇷" },
  { code: "NG", name: "Nigeria", flag: "🇳🇬" },
];

const AuthPage = () => {
  const [mode, setMode] = useState<"login" | "signup">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [countryCode, setCountryCode] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const { login, register, isLoginLoading, isRegisterLoading } = useAuth();

  const loading = isLoginLoading || isRegisterLoading;

  const handleAuth = (e: React.FormEvent) => {
    e.preventDefault();

    if (!email || !password) {
      toast.error("Please fill in all fields");
      return;
    }

    if (mode === "signup") {
      if (!countryCode) {
        toast.error("Please select your country");
        return;
      }

      register(
        {
          email,
          password,
          country_code: countryCode,
        },
        {
          onSuccess: () => {
            toast.success("Registration successful! Redirecting...");
          },
          onError: (error: any) => {
            toast.error(error?.response?.data?.detail || "Registration failed");
          },
        }
      );
    } else {
      login(
        { email, password },
        {
          onSuccess: () => {
            toast.success("Login successful! Redirecting...");
          },
          onError: (error: any) => {
            toast.error(error?.response?.data?.detail || "Login failed");
          },
        }
      );
    }
  };

  return (
    <div className="min-h-screen bg-background flex flex-col relative overflow-hidden">
      {/* Background accents */}
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute top-1/4 left-0 right-0 h-px energy-wave animate-wave-flow" />
        <div
          className="absolute top-1/4 translate-y-3 left-0 right-0 h-px energy-wave animate-wave-flow"
          style={{ animationDelay: "0.5s" }}
        />
      </div>

      {/* Header */}
      <div className="flex flex-col items-center pt-16 pb-8 px-8">
        <motion.img
          src={logo}
          alt="Hedera Flow"
          className="w-20 h-20 rounded-2xl mb-4"
          initial={{ scale: 0.8, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ duration: 0.5 }}
        />
        <motion.h1
          className="text-2xl font-bold text-foreground"
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.15 }}
        >
          {mode === "login" ? "Welcome Back" : "Create Account"}
        </motion.h1>
        <motion.p
          className="text-sm text-muted-foreground mt-1"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.25 }}
        >
          {mode === "login" ? "Sign in to manage your bills" : "Get started with Hedera Flow"}
        </motion.p>
      </div>

      {/* Form */}
      <motion.div
        className="flex-1 px-6 pb-8"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
      >
        <form onSubmit={handleAuth} className="space-y-4">
          <AnimatePresence mode="wait">
            {mode === "signup" && (
              <motion.div
                key="country"
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: "auto" }}
                exit={{ opacity: 0, height: 0 }}
                transition={{ duration: 0.2 }}
              >
                <div className="glass-card px-4 py-3">
                  <Select value={countryCode} onValueChange={setCountryCode} required={mode === "signup"}>
                    <SelectTrigger className="border-0 bg-transparent p-0 h-auto focus:ring-0">
                      <div className="flex items-center gap-3">
                        <MapPin className="w-5 h-5 text-muted-foreground shrink-0" />
                        <SelectValue placeholder="Select Country" />
                      </div>
                    </SelectTrigger>
                    <SelectContent>
                      {countries.map((country) => (
                        <SelectItem key={country.code} value={country.code}>
                          <span className="flex items-center gap-2">
                            <span className="text-lg">{country.flag}</span>
                            <span>{country.name}</span>
                          </span>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          <div className="glass-card flex items-center gap-3 px-4 py-3">
            <Mail className="w-5 h-5 text-muted-foreground shrink-0" />
            <input
              type="email"
              placeholder="Email address"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="flex-1 bg-transparent text-foreground placeholder:text-muted-foreground outline-none text-base"
              required
            />
          </div>

          <div className="glass-card flex items-center gap-3 px-4 py-3">
            <Lock className="w-5 h-5 text-muted-foreground shrink-0" />
            <input
              type={showPassword ? "text" : "password"}
              placeholder="Password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="flex-1 bg-transparent text-foreground placeholder:text-muted-foreground outline-none text-base"
              required
              minLength={8}
            />
            <button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              className="text-muted-foreground"
            >
              {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
            </button>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="tap-scale w-full py-4 rounded-2xl gradient-accent text-accent-foreground font-semibold text-base flex items-center justify-center gap-2 disabled:opacity-50"
          >
            {loading ? (
              <div className="w-5 h-5 border-2 border-accent-foreground/30 border-t-accent-foreground rounded-full animate-spin" />
            ) : (
              <>
                {mode === "login" ? "Sign In" : "Sign Up"}
                <ArrowRight className="w-5 h-5" />
              </>
            )}
          </button>
        </form>

        {/* Toggle mode */}
        <p className="text-center text-sm text-muted-foreground mt-8">
          {mode === "login" ? "Don't have an account?" : "Already have an account?"}{" "}
          <button
            onClick={() => setMode(mode === "login" ? "signup" : "login")}
            className="text-accent font-semibold"
          >
            {mode === "login" ? "Sign Up" : "Sign In"}
          </button>
        </p>
      </motion.div>
    </div>
  );
};

export default AuthPage;
