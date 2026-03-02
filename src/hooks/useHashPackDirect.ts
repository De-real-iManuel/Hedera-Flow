import { useState, useCallback, useEffect } from 'react';
import { toast } from 'sonner';
import { authApi } from '@/lib/api';

// Improved HashPack detection - checks multiple indicators
const checkHashPackInstalled = (): boolean => {
  if (typeof window === 'undefined') return false;
  
  // Check all possible HashPack injection points
  const win = window as any;
  const hasHashPack = typeof win.hashpack !== 'undefined';
  const hasHashConnect = typeof win.hashconnect !== 'undefined';
  const hasMeta = document.querySelector('meta[name="hashpack-extension"]') !== null;
  const hasLocalStorage = localStorage.getItem('hashconnectData') !== null;
  
  // Check if HashPack extension ID is in the page
  const hasExtensionScript = Array.from(document.querySelectorAll('script')).some(
    script => script.src.includes('chrome-extension://') && script.src.includes('gjagmgiddbbciopjhllkdnddhcglnemk')
  );
  
  console.log('HashPack detection:', { 
    hasHashPack, 
    hasHashConnect, 
    hasMeta, 
    hasLocalStorage,
    hasExtensionScript,
    windowKeys: Object.keys(win).filter(k => k.toLowerCase().includes('hash'))
  });
  
  return hasHashPack || hasHashConnect || hasMeta || hasLocalStorage || hasExtensionScript;
};

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
  const [hashPackFound, setHashPackFound] = useState(false);

  // Check for HashPack on mount and periodically
  useEffect(() => {
    let checkCount = 0;
    const maxChecks = 20; // Increased from 10
    
    const checkHashPack = () => {
      const found = checkHashPackInstalled();
      setHashPackFound(found);
      checkCount++;
      
      console.log(`HashPack check ${checkCount}/${maxChecks}: ${found ? 'Found' : 'Not found'}`);
      
      // Stop checking once found or max checks reached
      if (found || checkCount >= maxChecks) {
        if (intervalId) clearInterval(intervalId);
      }
      
      return found;
    };

    // Check immediately
    checkHashPack();

    // Check periodically with longer interval (HashPack extension loads asynchronously)
    const intervalId = setInterval(checkHashPack, 1000); // Increased from 500ms to 1000ms

    return () => {
      if (intervalId) clearInterval(intervalId);
    };
  }, []);

  // Connect using HashConnect library
  const connectHashPack = useCallback(async () => {
    setIsConnecting(true);
    
    try {
      // Final check before attempting connection
      const isInstalled = checkHashPackInstalled();
      console.log('Final HashPack check before connect:', isInstalled);
      
      if (!isInstalled) {
        toast.error('HashPack Not Found', {
          description: 'Please install HashPack extension and refresh the page.',
          duration: 5000,
          action: {
            label: 'Get HashPack',
            onClick: () => window.open('https://www.hashpack.app/download', '_blank'),
          },
        });
        setIsConnecting(false);
        return;
      }

      // Dynamic import of HashConnect
      const { HashConnect } = await import('hashconnect');
      
      const hashconnect = new HashConnect();
      
      // App metadata
      const appMetadata = {
        name: 'Hedera Flow',
        description: 'Blockchain-powered utility verification platform',
        icons: [window.location.origin + '/hedera-flow-logo.png'],
      };

      toast.info('Initializing connection...', {
        description: 'Setting up HashConnect',
      });

      // Initialize HashConnect
      let initData;
      try {
        initData = await hashconnect.init(appMetadata, 'testnet', false);
        console.log('HashConnect initialized:', initData);
      } catch (error) {
        console.error('HashConnect init failed:', error);
        throw new Error('Failed to initialize HashConnect. Please try again.');
      }

      // Set up pairing event listener
      hashconnect.pairingEvent.on((pairingData) => {
        console.log('Pairing event received:', pairingData);
        
        if (pairingData.accountIds && pairingData.accountIds.length > 0) {
          const accountId = pairingData.accountIds[0];
          
          setWalletState({
            isConnected: true,
            accountId,
          });

          toast.success('Wallet Connected!', {
            description: `Account: ${accountId}`,
          });

          // Authenticate with backend
          authenticateWithBackend(accountId, hashconnect);
        }
      });

      toast.info('Opening HashPack...', {
        description: 'Please approve the connection in your wallet',
        duration: 10000,
      });

      // Connect to local wallet (opens HashPack)
      await hashconnect.connectToLocalWallet();

    } catch (error: any) {
      console.error('Failed to connect to HashPack:', error);
      
      let errorMessage = 'Please try again';
      let errorTitle = 'Connection Failed';
      
      if (error.message?.includes('initialize')) {
        errorMessage = 'Failed to initialize HashConnect. Please refresh the page and try again.';
      } else if (error.message) {
        errorMessage = error.message;
      }
      
      toast.error(errorTitle, {
        description: errorMessage,
        duration: 5000,
      });
      setIsConnecting(false);
    }
  }, [hashPackFound]);

  // Authenticate with backend
  const authenticateWithBackend = useCallback(async (accountId: string, hashconnect: any) => {
    try {
      // Create a message to sign
      const timestamp = Date.now();
      const message = `Hedera Flow Authentication\nAccount: ${accountId}\nTimestamp: ${timestamp}`;
      
      toast.info('Requesting signature...', {
        description: 'Please sign the message in HashPack',
      });

      // Sign message
      const signResult = await hashconnect.signMessage(message);
      console.log('Sign result:', signResult);

      if (!signResult || !signResult.signature) {
        throw new Error('No signature received from wallet');
      }

      const signature = signResult.signature;

      toast.info('Verifying signature...', {
        description: 'Authenticating with backend',
      });

      // Send to backend for verification
      const response = await authApi.walletConnect({
        hedera_account_id: accountId,
        signature,
        message,
      });

      // Store token
      localStorage.setItem('auth_token', response.token);
      localStorage.setItem('user', JSON.stringify(response.user));

      toast.success('Successfully authenticated!', {
        description: 'Redirecting to dashboard...',
      });
      
      setIsConnecting(false);
      
      // Redirect to home
      setTimeout(() => {
        window.location.href = '/';
      }, 1000);

    } catch (error: any) {
      console.error('Backend authentication failed:', error);
      toast.error('Authentication Failed', {
        description: error.response?.data?.detail || error.message || 'Please try again',
        duration: 5000,
      });
      setIsConnecting(false);
    }
  }, []);

  return {
    walletState,
    isConnecting,
    isHashPackInstalled: hashPackFound,
    connectHashPack,
    disconnect: () => {
      setWalletState({ isConnected: false, accountId: null });
    },
  };
};
