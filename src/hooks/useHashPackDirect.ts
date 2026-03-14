import { useState, useCallback, useEffect } from 'react';
import { toast } from 'sonner';
import { authApi } from '@/lib/api';
import { HashConnect, DappMetadata, SessionData, HashConnectConnectionState } from 'hashconnect';
import { LedgerId } from '@hashgraph/sdk';

interface WalletState {
  isConnected: boolean;
  accountId: string | null;
}

export const useHashPackDirect = () => {
  const [walletState, setWalletState] = useState<WalletState>({
    isConnected: false,
    accountId: null,
  });
  const [isConnecting, setIsConnecting] = useState(false);
  const [hashConnect, setHashConnect] = useState<HashConnect | null>(null);
  const [pairingString, setPairingString] = useState<string>('');

  // Initialize HashConnect on mount
  useEffect(() => {
    initializeHashConnect();
  }, []);

  const initializeHashConnect = async () => {
    try {
      console.log('Initializing HashConnect...');
      
      // App metadata
      const appMetadata: DappMetadata = {
        name: 'Hedera Flow',
        description: 'Blockchain-powered utility verification platform',
        icons: [`${window.location.origin}/hedera-flow-logo.png`],
        url: window.location.origin,
      };

      // Create HashConnect instance with correct v3 API
      const hashconnect = new HashConnect(
        LedgerId.TESTNET,
        import.meta.env.VITE_WALLETCONNECT_PROJECT_ID || 'demo-project-id',
        appMetadata,
        true // debug mode
      );

      // Set up event listeners BEFORE init
      hashconnect.pairingEvent.on((data: SessionData) => {
        console.log('Pairing event:', data);
        handlePairingEvent(data);
      });

      hashconnect.disconnectionEvent.on(() => {
        console.log('Disconnection event');
        setWalletState({ isConnected: false, accountId: null });
      });

      hashconnect.connectionStatusChangeEvent.on((state: HashConnectConnectionState) => {
        console.log('Connection status changed:', state);
      });

      // Initialize - this will automatically detect and pair with extension if installed
      const initData = await hashconnect.init();
      console.log('HashConnect initialized:', initData);

      setHashConnect(hashconnect);
      
      // Get pairing string for QR code
      const pairingStr = hashconnect.pairingString;
      if (pairingStr) {
        setPairingString(pairingStr);
        console.log('Pairing string:', pairingStr);
      }

      // Check for existing connection
      const connectedAccounts = hashconnect.connectedAccountIds;
      if (connectedAccounts && connectedAccounts.length > 0) {
        const accountId = connectedAccounts[0].toString();
        console.log('Found existing connection:', accountId);
        setWalletState({
          isConnected: true,
          accountId,
        });
      }

    } catch (error) {
      console.error('Failed to initialize HashConnect:', error);
      toast.error('Initialization Failed', {
        description: 'Could not initialize WalletConnect',
      });
    }
  };

  const handlePairingEvent = (data: SessionData) => {
    console.log('Pairing approved:', data);
    
    // Stop connecting state
    setIsConnecting(false);
    
    if (data.accountIds && data.accountIds.length > 0) {
      const accountId = data.accountIds[0];
      setWalletState({
        isConnected: true,
        accountId,
      });

      toast.success('Wallet Connected!', {
        description: `Account: ${accountId}`,
      });

      // Authenticate with backend
      authenticateWithBackend(accountId);
    }
  };

  const connectHashPack = useCallback(async () => {
    if (!hashConnect) {
      toast.error('HashConnect not initialized', {
        description: 'Please refresh the page and try again',
      });
      return;
    }

    setIsConnecting(true);

    try {
      console.log('Opening pairing modal...');
      console.log('HashConnect state:', {
        connectedAccountIds: hashConnect.connectedAccountIds,
        pairingString: hashConnect.pairingString,
      });
      
      // According to HashConnect docs:
      // "If the HashPack extension is found during init, it will automatically pop it up and request pairing."
      // openPairingModal() will show QR code for mobile OR trigger extension popup
      await hashConnect.openPairingModal();

      toast.info('Waiting for connection...', {
        description: 'Approve in HashPack extension or scan QR code with mobile app',
        duration: 20000,
      });

    } catch (error: any) {
      console.error('Failed to open pairing modal:', error);
      toast.error('Connection Failed', {
        description: error.message || 'Please try again',
      });
      setIsConnecting(false);
    }
  }, [hashConnect]);

  const authenticateWithBackend = useCallback(async (accountId: string) => {
    if (!hashConnect) {
      console.error('HashConnect not available');
      return;
    }

    try {
      const timestamp = Date.now();
      const message = `Hedera Flow Authentication\nAccount: ${accountId}\nTimestamp: ${timestamp}`;

      toast.info('Requesting signature...', {
        description: 'Please sign the message in HashPack',
      });

      console.log('Requesting signature for:', message);

      // Get the signer for this account
      const signer = hashConnect.getSigner(hashConnect.connectedAccountIds[0]);
      
      // Sign the message
      const signerSignatures = await signer.sign([Buffer.from(message)]);

      console.log('Sign result:', signerSignatures);

      if (!signerSignatures || signerSignatures.length === 0) {
        throw new Error('No signature received from wallet');
      }

      // Get the first signature
      const signerSignature = signerSignatures[0];
      
      // Convert signature to base64 for backend
      const signatureBytes = signerSignature.signature;
      const signatureBase64 = Buffer.from(signatureBytes).toString('base64');

      toast.info('Verifying signature...', {
        description: 'Authenticating with backend',
      });

      const response = await authApi.walletConnect({
        hedera_account_id: accountId,
        signature: signatureBase64,
        message,
      });

      localStorage.setItem('auth_token', response.token);
      localStorage.setItem('user', JSON.stringify(response.user));

      toast.success('Successfully authenticated!', {
        description: 'Redirecting to dashboard...',
      });

      setIsConnecting(false);

      setTimeout(() => {
        window.location.href = '/';
      }, 1000);

    } catch (error: any) {
      console.error('Backend authentication failed:', error);
      toast.error('Authentication Failed', {
        description: error.response?.data?.detail || error.message || 'Please try again',
      });
      setIsConnecting(false);
    }
  }, [hashConnect]);

  const disconnect = useCallback(async () => {
    if (hashConnect) {
      await hashConnect.disconnect();
    }
    setWalletState({ isConnected: false, accountId: null });
  }, [hashConnect]);

  return {
    walletState,
    isConnecting,
    isHashPackInstalled: true, // Always true since it's WalletConnect-based
    connectHashPack,
    disconnect,
    pairingString,
    recheckHashPack: () => {
      toast.info('HashPack uses WalletConnect', {
        description: 'Click Connect to scan QR code or copy pairing string',
      });
      return true;
    },
  };
};
