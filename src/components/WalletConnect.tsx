import { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { authApi } from '@/lib/api';

interface WalletConnectProps {
  className?: string;
}

const WalletConnect = ({ className }: WalletConnectProps) => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [isConnecting, setIsConnecting] = useState(false);

  const handleAuthSuccess = useCallback(async (accountId: string) => {
    try {
      const message = `Hedera Flow Authentication\nAccount: ${accountId}\nTimestamp: ${Date.now()}`;
      const signature = accountId; // MVP: backend accepts account ID as signature for wallet-only auth

      const user = await authApi.walletConnect({
        hedera_account_id: accountId,
        signature,
        message,
      });

      queryClient.setQueryData(['user'], user);
      toast.success('Wallet connected', { description: 'Redirecting...' });
      setTimeout(() => navigate('/home'), 800);
    } catch (err: any) {
      const detail = err?.response?.data?.detail || err?.message || 'Please try again';
      toast.error('Authentication failed', { description: detail });
    } finally {
      setIsConnecting(false);
    }
  }, [navigate, queryClient]);


  const connectHashPack = useCallback(async () => {
    setIsConnecting(true);
    const hp = (window as any).hashpack;
    if (!hp) {
      toast.error('HashPack not found', {
        description: 'Install the HashPack extension',
        action: { label: 'Install', onClick: () => window.open('https://www.hashpack.app/', '_blank') },
      });
      setIsConnecting(false);
      return;
    }
    try {
      const result = await hp.connect();
      const accountId: string = result?.accountIds?.[0] ?? result?.accountId;
      if (!accountId) throw new Error('No account ID returned from HashPack');
      await handleAuthSuccess(accountId);
    } catch (err: any) {
      toast.error('HashPack connection failed', { description: err?.message });
      setIsConnecting(false);
    }
  }, [handleAuthSuccess]);

  const connectMetaMask = useCallback(async () => {
    setIsConnecting(true);
    const eth = (window as any).ethereum;
    if (!eth) {
      toast.error('MetaMask not found', {
        description: 'Install the MetaMask extension',
        action: { label: 'Install', onClick: () => window.open('https://metamask.io/', '_blank') },
      });
      setIsConnecting(false);
      return;
    }
    try {
      const accounts: string[] = await eth.request({ method: 'eth_requestAccounts' });
      const address = accounts[0];
      if (!address) throw new Error('No account returned from MetaMask');
      await handleAuthSuccess(address);
    } catch (err: any) {
      toast.error('MetaMask connection failed', { description: err?.message });
      setIsConnecting(false);
    }
  }, [handleAuthSuccess]);

  return (
    <div className={className}>
      <div className="flex flex-col gap-3">
        <button
          onClick={connectHashPack}
          disabled={isConnecting}
          className="flex items-center justify-center gap-2 w-full px-4 py-3 rounded-lg border border-purple-500 text-purple-600 hover:bg-purple-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium"
        >
          {isConnecting ? (
            <span className="animate-spin rounded-full h-4 w-4 border-b-2 border-purple-600" />
          ) : (
            <img src="/hashpack-logo.png" alt="" className="h-5 w-5" onError={(e) => { (e.target as HTMLImageElement).style.display = 'none'; }} />
          )}
          Connect HashPack
        </button>

        <button
          onClick={connectMetaMask}
          disabled={isConnecting}
          className="flex items-center justify-center gap-2 w-full px-4 py-3 rounded-lg border border-orange-400 text-orange-600 hover:bg-orange-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium"
        >
          {isConnecting ? (
            <span className="animate-spin rounded-full h-4 w-4 border-b-2 border-orange-500" />
          ) : (
            <img src="/metamask-logo.png" alt="" className="h-5 w-5" onError={(e) => { (e.target as HTMLImageElement).style.display = 'none'; }} />
          )}
          Connect MetaMask
        </button>
      </div>
    </div>
  );
};

export default WalletConnect;
