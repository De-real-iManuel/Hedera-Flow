import { useState, useEffect } from "react";
import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route, useLocation, useNavigate } from "react-router-dom";
import HomePage from "./pages/HomePage";
import ScanPage from "./pages/ScanPage";
import BillsPage from "./pages/BillsPage";
import HistoryPage from "./pages/HistoryPage";
import ProfilePage from "./pages/ProfilePage";
import NotFound from "./pages/NotFound";
import ApiTestPage from "./pages/ApiTestPage";
import AuthPage from "./pages/AuthPage";
import VerifyEmailPage from "./pages/VerifyEmailPage";
import RegisterMeterPage from "./pages/RegisterMeterPage";
import MetersPage from "./pages/MetersPage";
import VerificationTestPage from "./pages/VerificationTestPage";
import PrepaidPage from "./pages/PrepaidPage";
import PrepaidSmartMeterPage from "./pages/PrepaidSmartMeterPage";
import PrepaidMeterPage from "./pages/PrepaidMeterPage";
import SmartMeterPage from "./pages/SmartMeterPage";
import MeterHubPage from "./pages/MeterHubPage";
import BottomNav from "./components/BottomNav";
import SplashScreen from "./components/SplashScreen";
import LandingPage from "./pages/LandingPage";
import AuthGuard from "./components/AuthGuard";
import MeterDetailPage from "./pages/MeterDetailPage";

const queryClient = new QueryClient();

const AppContent = () => {
  const [showSplash, setShowSplash] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();

  // Show splash screen only after successful authentication
  useEffect(() => {
    const hasSeenSplash = sessionStorage.getItem('hasSeenSplash');
    
    // Show splash if user navigates to home and hasn't seen it this session
    if (!hasSeenSplash && location.pathname === '/home') {
      setShowSplash(true);
    }
  }, [location.pathname]);

  const handleSplashComplete = () => {
    setShowSplash(false);
    sessionStorage.setItem('hasSeenSplash', 'true');
  };

  // Pages where BottomNav should NOT be shown
  const hideNavPaths = ['/', '/auth', '/verify-email', '/login', '/register'];
  const shouldShowNav = !hideNavPaths.includes(location.pathname);

  return (
    <>
      {showSplash && <SplashScreen onComplete={handleSplashComplete} />}
      <div className="max-w-lg mx-auto relative min-h-screen">
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/auth" element={<AuthPage />} />
          <Route path="/verify-email" element={<VerifyEmailPage />} />
          
          {/* Protected Routes */}
          <Route path="/home" element={<AuthGuard><HomePage /></AuthGuard>} />
          <Route path="/register-meter" element={<AuthGuard><RegisterMeterPage /></AuthGuard>} />
          <Route path="/meters" element={<AuthGuard><MetersPage /></AuthGuard>} />
          <Route path="/meters/:id" element={<AuthGuard><MeterDetailPage /></AuthGuard>} />
          <Route path="/meter-hub" element={<AuthGuard><MeterHubPage /></AuthGuard>} />
          <Route path="/prepaid" element={<AuthGuard><PrepaidPage /></AuthGuard>} />
          <Route path="/prepaid-meter" element={<AuthGuard><PrepaidMeterPage /></AuthGuard>} />
          <Route path="/smart-meter" element={<AuthGuard><SmartMeterPage /></AuthGuard>} />
          <Route path="/prepaid-smart-meter" element={<AuthGuard><PrepaidSmartMeterPage /></AuthGuard>} />
          <Route path="/scan" element={<AuthGuard><ScanPage /></AuthGuard>} />
          <Route path="/bills" element={<AuthGuard><BillsPage /></AuthGuard>} />
          <Route path="/history" element={<AuthGuard><HistoryPage /></AuthGuard>} />
          <Route path="/profile" element={<AuthGuard><ProfilePage /></AuthGuard>} />
          <Route path="/api-test" element={<AuthGuard><ApiTestPage /></AuthGuard>} />
          <Route path="/verification-test" element={<AuthGuard><VerificationTestPage /></AuthGuard>} />
          
          <Route path="*" element={<NotFound />} />
        </Routes>
        {shouldShowNav && <BottomNav />}
      </div>
    </>
  );
};

const App = () => (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <Toaster />
      <Sonner />
      <BrowserRouter>
        <AppContent />
      </BrowserRouter>
    </TooltipProvider>
  </QueryClientProvider>
);

export default App;
