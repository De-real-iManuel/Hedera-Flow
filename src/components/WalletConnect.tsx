import { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { authApi } from '@/lib/api';

interface WalletConnectProps {
  className?: string;
}

// Inline SVG icons — no external image files needed
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

const WalletConnect = ({ className }: WalletConnectProps) => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [connecting, setConnecting] = useState<'hashpack' | 'metamask' | null>(null);

  const handleAuthSuccess = useCallback(async (accountId: string) => {
    try {
      const message = `Hedera Flow Authentication\nAccount: ${accountId}\nTimestamp: ${Date.now()}`;
      const user = await authApi.walletConnect({
        hedera_account_id: accountId,
        signature: accountId, // MVP: backend accepts account ID as signature
        message,
      });
      queryClient.setQueryData(['user'], user);
      toast.success('Wallet connected', { description: 'Redirecting to home...' });
      setTimeout(() => navigate('/home'), 800);
    } catch (err: any) {
      const detail = err?.response?.data?.detail || err?.message || 'Please try again';
      toast.error('Authentication failed', { description: detail });
    } finally {
      setConnecting(null);
    }
  }, [navigate, queryClient]);

  const connectHashPack = useCallback(async () => {
    setConnecting('hashpack');
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
  }, [handleAuthSuccess]);

  const connectMetaMask = useCallback(async () => {
    setConnecting('metamask');
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
  }, [handleAuthSuccess]);

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
          {connecting === 'hashpack' ? 'Connecting...' : 'Connect HashPack'}
        </button>

        <button
          onClick={connectMetaMask}
          disabled={isConnecting}
          className="flex items-center justify-center gap-2 w-full px-4 py-3 rounded-lg border border-orange-400 text-orange-700 hover:bg-orange-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium"
        >
          {connecting === 'metamask' ? <Spinner color="border-orange-500" /> : <MetaMaskIcon />}
          {connecting === 'metamask' ? 'Connecting...' : 'Connect MetaMask'}
        </button>
      </div>
    </div>
  );
};

export default WalletConnect;
