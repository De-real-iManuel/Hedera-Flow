import { useState, useEffect, useCallback } from 'react';
import { HashConnect, HashConnectTypes, MessageTypes } from 'hashconnect';
import { toast } from 'sonner';
import { authApi } from '@/lib/api';

const APP_METADATA: HashConnectTypes.AppMetadata = {
  name: 'Hedera Flow',
  description: 'Blockchain-powered utility verification platform',
  icons: [window.location.origin + '/hedera-flow-logo.png'],
  url: window.location.origin,
};

const WALLET_CONFIG = {
  projectId: 'd4b1f89c512ed68b69f5a9485287936a',
  metadata: APP_METADATA,
};

interface WalletState {
  isConnected: boolean;
  accountId: string | null;
  topic: string | null;
  pairingString: string | null;
  walletType: 'hashpack' | 'blade' | null;
}

export const useWalletConnect = () => {
  const [hashConnect] = useState(() => new HashConnect());
  const [walletState, setWalletState] = useState<WalletState>({
    isConnected: false,
    accountId: null,
    topic: null,
    pairingString: null,
    walletType: null,
  });
  const [isInitializing, setIsInitializing] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);

  // Initialize HashConnect
  const initHashConnect = useCallback(async () => {
    if (isInitializing) return;
    
    setIsInitializing(true);
    try {
      console.log('Initializing HashConnect with metadata:', APP_METADATA);
      
      // Initialize HashConnect - try different parameter combinations
      let initData;
      try {
        // Try v3 initialization first
        initData = await hashConnect.init(
          APP_METADATA,
          WALLET_CONFIG.projectId,
          true
        );
      } catch (v3Error) {
        console.warn('HashConnect v3 init failed, trying v2:', v3Error);
        // Fallback to v2 initialization
        initData = await hashConnect.init(APP_METADATA);
      }
      
      setWalletState(prev => ({
        ...prev,
        topic: initData.topic,
        pairingString: initData.pairingString,
      }));

      console.log('HashConnect initialized successfully:', initData);
      return initData;
    } catch (error: any) {
      console.error('Failed to initialize HashConnect:', error);
      toast.error('Failed to initialize wallet connection', {
        description: error.message || 'Please check console for details'
      });
      throw error;
    } finally {
      setIsInitializing(false);
    }
  }, [hashConnect, isInitializing]);

  // Connect to HashPack wallet
  const connectHashPack = useCallback(async () => {
    setIsConnecting(true);
    try {
      console.log('Connecting to HashPack...');
      
      // Initialize if not already done
      if (!walletState.topic) {
        console.log('Initializing HashConnect first...');
        await initHashConnect();
      }

      // Check if HashPack is installed
      if (!(window as any).hashpack) {
        toast.error('HashPack wallet not found', {
          description: 'Please install the HashPack browser extension',
          action: {
            label: 'Install',
            onClick: () => window.open('https://www.hashpack.app/', '_blank'),
          },
        });
        setIsConnecting(false);
        return;
      }

      // Open HashPack extension
      console.log('Opening HashPack wallet...');
      hashConnect.connectToLocalWallet();
      
      toast.info('Opening HashPack wallet...', {
        description: 'Please approve the connection in your wallet',
      });
    } catch (error: any) {
      console.error('Failed to connect to HashPack:', error);
      toast.error('Failed to connect to HashPack wallet', {
        description: error.message || 'Please try again'
      });
      setIsConnecting(false);
    }
  }, [hashConnect, walletState.topic, initHashConnect]);

  // Connect to Blade wallet
  const connectBlade = useCallback(async () => {
    setIsConnecting(true);
    try {
      // Check if Blade wallet is installed
      if (!(window as any).bladeConnect) {
        toast.error('Blade wallet not found', {
          description: 'Please install the Blade wallet extension',
        });
        setIsConnecting(false);
        return;
      }

      // Initialize if not already done
      if (!walletState.topic) {
        await initHashConnect();
      }

      // Connect to Blade
      const bladeConnect = (window as any).bladeConnect;
      const result = await bladeConnect.createSession(APP_METADATA);
      
      if (result.success) {
        setWalletState(prev => ({
          ...prev,
          isConnected: true,
          accountId: result.accountId,
          walletType: 'blade',
        }));
        
        toast.success('Connected to Blade wallet');
      } else {
        throw new Error(result.error || 'Failed to connect');
      }
    } catch (error) {
      console.error('Failed to connect to Blade:', error);
      toast.error('Failed to connect to Blade wallet');
    } finally {
      setIsConnecting(false);
    }
  }, [walletState.topic, initHashConnect]);

  // Authenticate with backend
  const authenticateWithBackend = useCallback(async (accountId: string, walletType: 'hashpack' | 'blade') => {
    try {
      console.log(`Starting authentication for ${walletType} wallet:`, accountId);
      
      // Create a message to sign
      const message = `Hedera Flow Authentication\nAccount: ${accountId}\nTimestamp: ${Date.now()}`;
      console.log('Message to sign:', message);
      
      // Request signature from wallet
      let signature: string;
      
      if (walletType === 'hashpack') {
        console.log('Requesting signature from HashPack...');
        try {
          const signResult = await hashConnect.signMessage(message);
          console.log('HashPack sign result:', signResult);
          signature = signResult.signature;
          
          if (!signature) {
            throw new Error('No signature received from HashPack');
          }
        } catch (signError) {
          console.error('HashPack signing failed:', signError);
          toast.error('Failed to sign message with HashPack', {
            description: 'Please try connecting again'
          });
          throw signError;
        }
      } else {
        // Blade wallet signature
        console.log('Requesting signature from Blade...');
        try {
          const bladeConnect = (window as any).bladeConnect;
          const signResult = await bladeConnect.signMessage(message);
          console.log('Blade sign result:', signResult);
          signature = signResult.signature;
          
          if (!signature) {
            throw new Error('No signature received from Blade');
          }
        } catch (signError) {
          console.error('Blade signing failed:', signError);
          toast.error('Failed to sign message with Blade', {
            description: 'Please try connecting again'
          });
          throw signError;
        }
      }

      console.log('Signature obtained, sending to backend...');

      // Send to backend for verification
      const response = await authApi.walletConnect({
        hedera_account_id: accountId,
        signature,
        message,
      });

      console.log('Backend authentication successful:', response);

      // No need to store token - it's in httpOnly cookie
      toast.success('Successfully authenticated!', {
        description: 'Redirecting to home page...'
      });
      
      // Redirect to home page
      setTimeout(() => {
        window.location.href = '/home';
      }, 1000);
      
      return response;
    } catch (error: any) {
      console.error('Backend authentication failed:', error);
      
      // More specific error messages
      if (error.response?.status === 401) {
        toast.error('Authentication failed', {
          description: 'Invalid signature or account not found'
        });
      } else if (error.response?.status === 400) {
        toast.error('Invalid request', {
          description: error.response?.data?.detail || 'Please check your wallet connection'
        });
      } else {
        toast.error('Authentication failed', {
          description: error.response?.data?.detail || error.message || 'Please try again'
        });
      }
      
      // Reset connection state on failure
      setWalletState(prev => ({
        ...prev,
        isConnected: false,
        accountId: null,
        walletType: null,
      }));
      
      throw error;
    }
  }, [hashConnect]);

  // Disconnect wallet
  const disconnect = useCallback(() => {
    hashConnect.disconnect();
    setWalletState({
      isConnected: false,
      accountId: null,
      topic: null,
      pairingString: null,
      walletType: null,
    });
    toast.info('Wallet disconnected');
  }, [hashConnect]);

  // Set up event listeners
  useEffect(() => {
    // Pairing event (wallet connected)
    hashConnect.pairingEvent.on((pairingData) => {
      console.log('Pairing event:', pairingData);
      
      const accountId = pairingData.accountIds[0];
      
      setWalletState(prev => ({
        ...prev,
        isConnected: true,
        accountId,
        walletType: 'hashpack',
      }));
      
      setIsConnecting(false);
      
      // Authenticate with backend
      authenticateWithBackend(accountId, 'hashpack');
    });

    // Connection status change
    hashConnect.connectionStatusChangeEvent.on((state) => {
      console.log('Connection status changed:', state);
    });

    // Cleanup
    return () => {
      hashConnect.pairingEvent.off(() => {});
      hashConnect.connectionStatusChangeEvent.off(() => {});
    };
  }, [hashConnect, authenticateWithBackend]);

  return {
    walletState,
    isInitializing,
    isConnecting,
    connectHashPack,
    connectBlade,
    disconnect,
    initHashConnect,
  };
};
