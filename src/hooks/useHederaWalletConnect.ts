import { useState, useCallback, useEffect } from 'react';
import { toast } from 'sonner';
import { authApi } from '@/lib/api';
import {
  DAppConnector,
  HederaJsonRpcMethod,
  HederaChainId,
} from '@hashgraph/hedera-wallet-connect';
import { LedgerId, AccountId } from '@hiero-ledger/sdk';

interface WalletState {
  isConnected: boolean;
  accountId: string | null;
}

export const useHederaWalletConnect = () => {
  const [walletState, setWalletState] = useState<WalletState>({
    isConnected: false,
    accountId: null,
  });
  const [isConnecting, setIsConnecting] = useState(false);
  const [dAppConnector, setDAppConnector] = useState<DAppConnector | null>(null);

  useEffect(() => {
    initializeDAppConnector();
  }, []);

  const initializeDAppConnector = async () => {
    try {
      console.log('Initializing Hedera DAppConnector...');
      
      const metadata = {
        name: 'Hedera Flow',
        description: 'Blockchain-powered utility verification platform',
        url: window.location.origin,
        icons: [`${window.location.origin}/hedera-flow-logo.png`],
      };

      const projectId = import.meta.env.VITE_WALLETCONNECT_PROJECT_ID || 'demo-project-id';

      const connector = new DAppConnector(
        metadata,
        LedgerId.TESTNET,
        projectId,
        Object.values(HederaJsonRpcMethod),
        [],
        [HederaChainId.Testnet],
      );

      await connector.init({ logger: 'error' });
      console.log('DAppConnector initialized successfully');

      setDAppConnector(connector);

      const signers = connector.signers;
      if (signers && signers.length > 0) {
        const accountId = signers[0].getAccountId().toString();
        console.log('Found existing session:', accountId);
        setWalletState({
          isConnected: true,
          accountId,
        });
      }

    } catch (error) {
      console.error('Failed to initialize DAppConnector:', error);
      toast.error('Initialization Failed', {
        description: 'Could not initialize wallet connection',
      });
    }
  };

  const connectWallet = useCallback(async () => {
    if (!dAppConnector) {
      toast.error('Connector not initialized', {
        description: 'Please refresh the page and try again',
      });
      return;
    }

    setIsConnecting(true);

    try {
      console.log('Opening wallet connection modal...');
      
      await dAppConnector.openModal();
      
      const signers = dAppConnector.signers;
      
      if (signers && signers.length > 0) {
        const accountId = signers[0].getAccountId().toString();
        
        console.log('Wallet connected:', accountId);
        
        setWalletState({
          isConnected: true,
          accountId,
        });

        toast.success('Wallet Connected!', {
          description: `Account: ${accountId}`,
        });

        await authenticateWithBackend(accountId);
      } else {
        setIsConnecting(false);
      }
    } catch (error: any) {
      console.error('Failed to connect wallet:', error);
      toast.error('Connection Failed', {
        description: error.message || 'Please try again',
      });
      setIsConnecting(false);
    }
  }, [dAppConnector]);

  const authenticateWithBackend = useCallback(async (accountId: string) => {
    if (!dAppConnector) {
      console.error('DAppConnector not available');
      return;
    }

    try {
      const timestamp = Date.now();
      const message = `Hedera Flow Authentication\nAccount: ${accountId}\nTimestamp: ${timestamp}`;

      toast.info('Requesting signature...', {
        description: 'Please sign the message in your wallet',
      });

      console.log('Requesting signature for:', message);

      const signer = dAppConnector.getSigner(AccountId.fromString(accountId));
      
      const signatureBytes = await signer.sign([Buffer.from(message)]);

      console.log('Signature received:', signatureBytes);

      if (!signatureBytes || signatureBytes.length === 0) {
        throw new Error('No signature received from wallet');
      }

      const signatureBase64 = Buffer.from(signatureBytes[0].signature).toString('base64');

      toast.info('Verifying signature...', {
        description: 'Authenticating with backend',
      });

      const response = await authApi.walletConnect({
        hedera_account_id: accountId,
        signature: signatureBase64,
        message,
      });

      // No need to store token - it's in httpOnly cookie

      toast.success('Successfully authenticated!', {
        description: 'Redirecting to dashboard...',
      });

      setIsConnecting(false);

      setTimeout(() => {
        window.location.href = '/home';
      }, 1000);

    } catch (error: any) {
      console.error('Backend authentication failed:', error);
      toast.error('Authentication Failed', {
        description: error.response?.data?.detail || error.message || 'Please try again',
      });
      setIsConnecting(false);
    }
  }, [dAppConnector]);

  const disconnect = useCallback(async () => {
    if (dAppConnector) {
      try {
        await dAppConnector.disconnectAll();
        setWalletState({ isConnected: false, accountId: null });
        toast.info('Wallet disconnected');
      } catch (error) {
        console.error('Failed to disconnect:', error);
      }
    }
  }, [dAppConnector]);

  return {
    walletState,
    isConnecting,
    connectWallet,
    disconnect,
    dAppConnector,
  };
};


export default useHederaWalletConnect;
