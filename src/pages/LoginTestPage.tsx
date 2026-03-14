import { useState } from 'react';
import { authApi, billsApi } from '@/lib/api';
import { toast } from 'sonner';

const LoginTestPage = () => {
  const [isLoading, setIsLoading] = useState(false);
  const [isLoggedIn, setIsLoggedIn] = useState(!!localStorage.getItem('auth_token'));
  const [testResults, setTestResults] = useState<string[]>([]);

  const addResult = (message: string) => {
    setTestResults(prev => [...prev, message]);
  };

  const testLogin = async () => {
    setIsLoading(true);
    setTestResults([]);
    
    try {
      addResult('🔄 Testing login...');
      
      const result = await authApi.login({
        email: 'test@hederaflow.com',
        password: 'testpass123'
      });
      
      addResult(`✅ Login successful: ${result.user.email}`);
      setIsLoggedIn(true);
      toast.success('Login successful!');
      
      // Test bills API
      addResult('🔄 Testing bills API...');
      const bills = await billsApi.list();
      addResult(`✅ Bills API successful: Found ${bills.length} bills`);
      
    } catch (error: any) {
      addResult(`❌ Error: ${error.message}`);
      toast.error('Test failed');
    } finally {
      setIsLoading(false);
    }
  };

  const testLogout = () => {
    authApi.logout();
    setIsLoggedIn(false);
    setTestResults([]);
    toast.success('Logged out');
  };

  return (
    <div className="min-h-screen bg-background p-5">
      <div className="max-w-md mx-auto space-y-6">
        <h1 className="text-2xl font-bold text-center">Login & CORS Test</h1>
        
        <div className="glass-card p-6 space-y-4">
          <div className="flex items-center justify-between">
            <span>Status:</span>
            <span className={`font-semibold ${isLoggedIn ? 'text-green-600' : 'text-red-600'}`}>
              {isLoggedIn ? 'Logged In' : 'Not Logged In'}
            </span>
          </div>
          
          <div className="space-y-2">
            {!isLoggedIn ? (
              <button
                onClick={testLogin}
                disabled={isLoading}
                className="w-full py-3 rounded-2xl gradient-accent text-accent-foreground font-semibold disabled:opacity-50"
              >
                {isLoading ? 'Testing...' : 'Test Login & API'}
              </button>
            ) : (
              <button
                onClick={testLogout}
                className="w-full py-3 rounded-2xl border border-border text-foreground font-semibold"
              >
                Logout
              </button>
            )}
          </div>
        </div>

        {testResults.length > 0 && (
          <div className="glass-card p-6">
            <h3 className="font-semibold mb-3">Test Results:</h3>
            <div className="space-y-2">
              {testResults.map((result, index) => (
                <div key={index} className="text-sm font-mono">
                  {result}
                </div>
              ))}
            </div>
          </div>
        )}

        <div className="glass-card p-6">
          <h3 className="font-semibold mb-3">Instructions:</h3>
          <div className="text-sm text-muted-foreground space-y-2">
            <p>1. Click "Test Login & API" to authenticate and test the bills endpoint</p>
            <p>2. If successful, you should see login confirmation and bills count</p>
            <p>3. This verifies that CORS is working correctly</p>
            <p>4. You can then navigate to other pages safely</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LoginTestPage;