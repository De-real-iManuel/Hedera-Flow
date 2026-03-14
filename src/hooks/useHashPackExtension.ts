import { useState, useCallback, useEffect } from 'react';
import { toast } from 'sonner';

interface HashpackData {
  topic: string;
  pairingString: string;
  accountIds: string[];
  network: string;
}

export const useHashPackExtension = () => {
  const [walletState, setWalletState] = useState({
    isConnected: false,
    accountId: null as string | null,
  });
  const [isConnecting, setIsConnecting] = useState(false);
  const [isHashPackInstalled, setIsHashPackInstalled] = useState(false);

  useEffect(() => {
    checkHashPackInstalled();
  }, []);

  const checkHashPackInstalled = () => {
    const installed = !!(window as any).hashpack;
    setIsHashPackInstalled(installed);
    return installed;
  };

  const connectHashPack = useCallback(async () => {
    const hashpack = (window as any).hashpack;
    
    if (!hashpack) {
      toast.error('HashPack Not Found', {
        description: 'Please install HashPack browser extension',
      });
      return;
    }

    setIsConnecting(true);

    try {
      const appMetadata = {
        name: 'Hedera Flow',
        description: 'Blockchain-powered utility verification',
        icon: `${window.location.origin}/hedera-flow-logo.png`,
      };

      const result: HashpackData = await hashpack.connectToLocalWallet(appMetadata);
      
      if (result.accountIds && result.accountIds.length > 0) {
        const accountId = result.accountIds[0];
        setWalletState({
          isConnected: true,
          accountId,
        });

        toast.success('Connected!', {
          description: `Account: ${accountId}`,
        });
      }
    } catch (error: any) {
      console.error('Connection failed:', error);
      toast.error('Connection Failed', {
        description: error.message || 'Please try again',
      });
    } finally {
      setIsConnecting(false);
    }
  }, []);

  const disconnect = useCallback(async () => {
    setWalletState({ isConnected: false, accountId: null });
    toast.info('Disconnected');
  }, []);

  return {
    walletState,
    isConnecting,
    isHashPackInstalled,
    connectHashPack,
    disconnect,
    recheckHashPack: checkHashPackInstalled,
  };
};
