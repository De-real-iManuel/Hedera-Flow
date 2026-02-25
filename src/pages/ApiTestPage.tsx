import { useState } from "react";
import { healthApi } from "@/lib/api";
import AppHeader from "@/components/AppHeader";

const ApiTestPage = () => {
  const [status, setStatus] = useState<string>("Not tested");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const testConnection = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await healthApi.check();
      setStatus(`✅ Connected! Status: ${response.status}`);
    } catch (err: any) {
      setError(err.message || "Connection failed");
      setStatus("❌ Connection failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-background pb-24">
      <AppHeader title="API Test" />

      <div className="px-5 space-y-5">
        <div className="glass-card p-5 space-y-4">
          <h2 className="text-lg font-bold text-foreground">Backend Connection Test</h2>
          
          <div className="space-y-2">
            <p className="text-sm text-muted-foreground">
              Backend URL: {import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'}
            </p>
            <p className="text-sm text-muted-foreground">
              Status: <span className="font-medium text-foreground">{status}</span>
            </p>
            {error && (
              <p className="text-sm text-destructive">
                Error: {error}
              </p>
            )}
          </div>

          <button
            onClick={testConnection}
            disabled={loading}
            className="w-full py-3 rounded-2xl gradient-accent text-accent-foreground font-semibold text-sm disabled:opacity-50"
          >
            {loading ? "Testing..." : "Test Connection"}
          </button>
        </div>

        <div className="glass-card p-5 space-y-3">
          <h3 className="text-sm font-semibold text-foreground">Troubleshooting</h3>
          <ul className="text-xs text-muted-foreground space-y-2">
            <li>✓ Make sure backend is running on port 8000</li>
            <li>✓ Check CORS settings in backend/.env</li>
            <li>✓ Verify VITE_API_BASE_URL in .env</li>
            <li>✓ Check browser console for errors</li>
          </ul>
        </div>

        <div className="glass-card p-5 space-y-3">
          <h3 className="text-sm font-semibold text-foreground">Environment</h3>
          <div className="text-xs text-muted-foreground space-y-1">
            <p>API Base URL: {import.meta.env.VITE_API_BASE_URL}</p>
            <p>API Timeout: {import.meta.env.VITE_API_TIMEOUT}ms</p>
            <p>Hedera Network: {import.meta.env.VITE_HEDERA_NETWORK}</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ApiTestPage;
