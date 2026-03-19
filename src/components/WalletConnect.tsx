import { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { authApi } from '@/lib/api';
import { setMemoryToken } from '@/lib/api-client';

interface WalletConnectProps {
  className?: string;
  /** 'auth' = login/register flow (default). 'link' = bind wallet to existing account. */
  mode?: 'auth' | 'link';
  onLinked?: () => void;
}

const isMobile = () => /Android|iPhone|iPad|iPod/i.test(navigator.userAgent);

const HashPackIcon = () => (
  <svg width="20" height="20" viewBox="0 0 32 32" fill="none" aria-hidden="true">
    <rect width="32" height="32" rx="8" fill="#8259EF"/>
    <path d="M8 24V8h4v6h8V8h4v16h-4v-6H12v6H8z" fill="white"/>
  </svg>
);

const MetaMaskIcon = () => (
  <svg width="20" height="20" viewBox="0 0 32 32" fill="none" aria-hidden="true">
    <rect width="32" height="32" rx="8" fill="#F6851B"/>
    <path d="M26 6L18 12l1.5-4.5L26 6z" fill="#E2761B"/>
    <path d="M6 6l7.9 6.1L12.5 7.5 6 6z" fill="#E4761B"/>
    <path d="M23.2 21l-2.1 3.2 4.5 1.2 1.3-4.3-3.7-.1z" fill="#E4761B"/>
    <path d="M5.1 21.1l1.3 4.3 4.5-1.2L8.8 21l-3.7.1z" fill="#E4761B"/>
    <path d="M10.6 14.5l-1.3 2 4.6.2-.2-5-3.1 2.8z" fill="#E4761B"/>
    <path d="M21.4 14.5l-3.2-2.9-.1 5 4.6-.2-1.3-1.9z" fill="#E4761B"/>
    <path d="M10.9 24.2l2.7-1.3-2.4-1.8-.3 3.1z" fill="#E4761B"/>
    <path d="M18.4 22.9l2.7 1.3-.3-3.1-2.4 1.8z" fill="#E4761B"/>
  </svg>
);

const Spinner = ({ color }: { color: string }) => (
  <span className={`animate-spin rounded-full h-4 w-4 border-b-2 ${color}`} />
);

const WalletConnect = ({ className, mode = 'auth', onLinked }: WalletConnectProps) => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [connecting, setConnecting] = useState<'hashpack' | 'metamask' | null>(null);
  const mobile = isMobile();

  const handleAuthSuccess = useCallback(async (accountId: string) => {
    try {
      const message = `Hedera Flow Authentication\nAccount: ${accountId}\nTimestamp: ${Date.now()}`;
      const payload = { hedera_account_id: accountId, signature: accountId, message };

      let user;
      if (mode === 'link') {
        user = await authApi.linkWallet(payload);
        if (user.access_token) setMemoryToken(user.access_token);
        queryClient.setQueryData(['user'], user);
        toast.success('Wallet linked to your account');
        onLinked?.();
      } else {
        user = await authApi.walletConnect(payload);
        if (user.access_token) setMemoryToken(user.access_token);
        queryClient.setQueryData(['user'], user);
        toast.success('Wallet connected', { description: 'Redirecting to home...' });
        setTimeout(() => navigate('/home'), 800);
      }
    } catch (err: any) {
      const detail = err?.response?.data?.detail || err?.message || 'Please try again';
      toast.error(mode === 'link' ? 'Failed to link wallet' : 'Authentication failed', { description: detail });
    } finally {
      setConnecting(null);
    }
  }, [navigate, queryClient, mode, onLinked]);

  // ── HashPack ──────────────────────────────────────────────────────────────
  const connectHashPack = useCallback(async () => {
    setConnecting('hashpack');

    if (mobile) {
      // HashPack mobile deep link — opens the HashPack app
      const returnUrl = encodeURIComponent(window.location.href);
      window.location.href = `https://www.hashpack.app/download`;
      toast.info('Open HashPack app', {
        description: 'After connecting in HashPack, return here and enter your account ID below.',
      });
      setConnecting(null);
      return;
    }

    const hp = (window as any).hashpack;
    if (!hp) {
      toast.error('HashPack not found', {
        description: 'Install the HashPack browser extension',
        action: { label: 'Install', onClick: () => window.open('https://www.hashpack.app/', '_blank') },
      });
      setConnecting(null);
      return;
    }
    try {
      const result = await hp.connect();
      const accountId: string = result?.accountIds?.[0] ?? result?.accountId;
      if (!accountId) throw new Error('No account ID returned from HashPack');
      await handleAuthSuccess(accountId);
    } catch (err: any) {
      toast.error('HashPack connection failed', { description: err?.message });
      setConnecting(null);
    }
  }, [handleAuthSuccess, mobile]);

  // ── MetaMask ──────────────────────────────────────────────────────────────
  const connectMetaMask = useCallback(async () => {
    setConnecting('metamask');

    if (mobile) {
      // MetaMask mobile deep link
      const dappUrl = encodeURIComponent(window.location.href);
      window.location.href = `https://metamask.app.link/dapp/${window.location.host}${window.location.pathname}`;
      setConnecting(null);
      return;
    }

    const eth = (window as any).ethereum;
    if (!eth) {
      toast.error('MetaMask not found', {
        description: 'Install the MetaMask browser extension',
        action: { label: 'Install', onClick: () => window.open('https://metamask.io/', '_blank') },
      });
      setConnecting(null);
      return;
    }
    try {
      const accounts: string[] = await eth.request({ method: 'eth_requestAccounts' });
      const address = accounts[0];
      if (!address) throw new Error('No account returned from MetaMask');
      await handleAuthSuccess(address);
    } catch (err: any) {
      toast.error('MetaMask connection failed', { description: err?.message });
      setConnecting(null);
    }
  }, [handleAuthSuccess, mobile]);

  // ── Manual account ID entry (mobile fallback) ─────────────────────────────
  const [manualId, setManualId] = useState('');
  const [showManual, setShowManual] = useState(false);

  const handleManualSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const id = manualId.trim();
    if (!id) return;
    setConnecting('hashpack');
    await handleAuthSuccess(id);
    setManualId('');
    setShowManual(false);
  };

  const isConnecting = connecting !== null;

  return (
    <div className={className}>
      <div className="flex flex-col gap-3">
        <button
          onClick={connectHashPack}
          disabled={isConnecting}
          className="flex items-center justify-center gap-2 w-full px-4 py-3 rounded-lg border border-purple-500 text-purple-700 hover:bg-purple-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium"
        >
          {connecting === 'hashpack' ? <Spinner color="border-purple-600" /> : <HashPackIcon />}
          {mobile
            ? 'Open HashPack App'
            : connecting === 'hashpack' ? 'Connecting...' : 'Connect HashPack'}
        </button>

        <button
          onClick={connectMetaMask}
          disabled={isConnecting}
          className="flex items-center justify-center gap-2 w-full px-4 py-3 rounded-lg border border-orange-400 text-orange-700 hover:bg-orange-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium"
        >
          {connecting === 'metamask' ? <Spinner color="border-orange-500" /> : <MetaMaskIcon />}
          {mobile
            ? 'Open MetaMask App'
            : connecting === 'metamask' ? 'Connecting...' : 'Connect MetaMask'}
        </button>

        {/* Mobile manual entry fallback */}
        {mobile && (
          <div className="mt-1">
            <button
              type="button"
              onClick={() => setShowManual(v => !v)}
              className="w-full text-xs text-muted-foreground underline text-center"
            >
              {showManual ? 'Hide' : 'Enter Hedera account ID manually'}
            </button>
            {showManual && (
              <form onSubmit={handleManualSubmit} className="mt-2 flex gap-2">
                <input
                  type="text"
                  value={manualId}
                  onChange={e => setManualId(e.target.value)}
                  placeholder="0.0.xxxxxx"
                  className="flex-1 border rounded-lg px-3 py-2 text-sm bg-background text-foreground"
                />
                <button
                  type="submit"
                  disabled={isConnecting || !manualId.trim()}
                  className="px-4 py-2 rounded-lg bg-accent text-accent-foreground text-sm font-medium disabled:opacity-50"
                >
                  {isConnecting ? '...' : 'Link'}
                </button>
              </form>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default WalletConnect;
