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
import BottomNav from "./components/BottomNav";
import SplashScreen from "./components/SplashScreen";
import LandingPage from "./pages/LandingPage";

const queryClient = new QueryClient();

const AppContent = () => {
  const [showSplash, setShowSplash] = useState(false);
  const [isAuthenticated, setIsAuthenticated] = useState(!!localStorage.getItem('auth_token'));
  const location = useLocation();
  const navigate = useNavigate();

  // Update auth state when location changes (after login/register)
  useEffect(() => {
    setIsAuthenticated(!!localStorage.getItem('auth_token'));
  }, [location.pathname]);

  // Show splash screen only after successful authentication
  useEffect(() => {
    const hasSeenSplash = sessionStorage.getItem('hasSeenSplash');
    
    // Show splash if user just authenticated and hasn't seen it this session
    if (isAuthenticated && !hasSeenSplash && location.pathname === '/home') {
      setShowSplash(true);
    }
  }, [isAuthenticated, location.pathname]);

  const handleSplashComplete = () => {
    setShowSplash(false);
    sessionStorage.setItem('hasSeenSplash', 'true');
  };

  // Pages where BottomNav should NOT be shown
  const hideNavPaths = ['/', '/auth', '/verify-email', '/login', '/register'];
  const shouldShowNav = !hideNavPaths.includes(location.pathname) && isAuthenticated;

  return (
    <>
      {showSplash && <SplashScreen onComplete={handleSplashComplete} />}
      <div className="max-w-lg mx-auto relative min-h-screen">
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/home" element={<HomePage />} />
          <Route path="/auth" element={<AuthPage />} />
          <Route path="/verify-email" element={<VerifyEmailPage />} />
          <Route path="/register-meter" element={<RegisterMeterPage />} />
          <Route path="/meters" element={<MetersPage />} />
          <Route path="/scan" element={<ScanPage />} />
          <Route path="/bills" element={<BillsPage />} />
          <Route path="/history" element={<HistoryPage />} />
          <Route path="/profile" element={<ProfilePage />} />
          <Route path="/api-test" element={<ApiTestPage />} />
          <Route path="/verification-test" element={<VerificationTestPage />} />
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
