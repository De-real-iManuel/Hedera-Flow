import { useState, useCallback, useEffect } from 'react';
import { toast } from 'sonner';
import { authApi } from '@/lib/api';

interface WalletState {
  isConnected: boolean;
  accountId: string | null;
  evmAddress: string | null;
}

interface EthereumProvider {
  request: (args: { method: string; params?: any[] }) => Promise<any>;
  on?: (event: string, handler: (...args: any[]) => void) => void;
  removeListener?: (event: string, handler: (...args: any[]) => void) => void;
  isMetaMask?: boolean;
}

declare global {
  interface Window {
    ethereum?: EthereumProvider;
  }
}

export const useMetaMaskHedera = () => {
  const [walletState, setWalletState] = useState<WalletState>({
    isConnected: false,
    accountId: null,
    evmAddress: null,
  });
  const [isConnecting, setIsConnecting] = useState(false);
  const [isMetaMaskInstalled, setIsMetaMaskInstalled] = useState(false);

  useEffect(() => {
    checkMetaMaskInstalled();
    checkExistingConnection();
  }, []);

  const checkMetaMaskInstalled = () => {
    const installed = typeof window.ethereum !== 'undefined';
    setIsMetaMaskInstalled(installed);
    return installed;
  };

  const checkExistingConnection = async () => {
    if (typeof window.ethereum === 'undefined') return;

    try {
      const accounts = await window.ethereum.request({ 
        method: 'eth_accounts' 
      });
      
      if (accounts && accounts.length > 0) {
        const evmAddress = accounts[0];
        console.log('Found existing MetaMask connection:', evmAddress);
        
        // Convert EVM address to Hedera account ID format
        // For now, we'll use the EVM address as identifier
        setWalletState({
          isConnected: true,
          accountId: null, // Will be set after authentication
          evmAddress,
        });
      }
    } catch (error) {
      console.error('Error checking existing connection:', error);
    }
  };

  const connectMetaMask = useCallback(async () => {
    if (typeof window.ethereum === 'undefined') {
      toast.error('MetaMask Not Found', {
        description: 'Please install MetaMask browser extension',
      });
      window.open('https://metamask.io/download/', '_blank');
      return;
    }

    setIsConnecting(true);

    try {
      console.log('Requesting MetaMask connection...');

      // Request account access
      const accounts = await window.ethereum.request({
        method: 'eth_requestAccounts',
      });

      if (!accounts || accounts.length === 0) {
        throw new Error('No accounts returned from MetaMask');
      }

      const evmAddress = accounts[0];
      console.log('MetaMask connected:', evmAddress);

      // Check if connected to Hedera network
      const chainId = await window.ethereum.request({ method: 'eth_chainId' });
      console.log('Current chain ID:', chainId);

      // Hedera Testnet chain ID: 0x128 (296 in decimal)
      const hederaTestnetChainId = '0x128';
      
      if (chainId !== hederaTestnetChainId) {
        toast.info('Switching to Hedera Testnet...', {
          description: 'Please approve the network switch in MetaMask',
        });

        try {
          // Try to switch to Hedera Testnet
          await window.ethereum.request({
            method: 'wallet_switchEthereumChain',
            params: [{ chainId: hederaTestnetChainId }],
          });
        } catch (switchError: any) {
          // If network doesn't exist, add it
          if (switchError.code === 4902) {
            await window.ethereum.request({
              method: 'wallet_addEthereumChain',
              params: [{
                chainId: hederaTestnetChainId,
                chainName: 'Hedera Testnet',
                nativeCurrency: {
                  name: 'HBAR',
                  symbol: 'HBAR',
                  decimals: 18,
                },
                rpcUrls: ['https://testnet.hashio.io/api'],
                blockExplorerUrls: ['https://hashscan.io/testnet'],
              }],
            });
          } else {
            throw switchError;
          }
        }
      }

      setWalletState({
        isConnected: true,
        accountId: null,
        evmAddress,
      });

      toast.success('MetaMask Connected!', {
        description: `Address: ${evmAddress.slice(0, 6)}...${evmAddress.slice(-4)}`,
      });

      // Authenticate with backend
      await authenticateWithBackend(evmAddress);

    } catch (error: any) {
      console.error('MetaMask connection failed:', error);
      
      if (error.code === 4001) {
        toast.error('Connection Rejected', {
          description: 'You rejected the connection request',
        });
      } else {
        toast.error('Connection Failed', {
          description: error.message || 'Please try again',
        });
      }
      setIsConnecting(false);
    }
  }, []);

  const authenticateWithBackend = useCallback(async (evmAddress: string) => {
    try {
      const timestamp = Date.now();
      const message = `Hedera Flow Authentication\nAddress: ${evmAddress}\nTimestamp: ${timestamp}`;

      toast.info('Requesting signature...', {
        description: 'Please sign the message in MetaMask',
      });

      console.log('Requesting signature for:', message);

      // Request signature from MetaMask
      const signature = await window.ethereum.request({
        method: 'personal_sign',
        params: [message, evmAddress],
      });

      console.log('Signature received');

      toast.info('Verifying signature...', {
        description: 'Authenticating with backend',
      });

      // For now, we'll use the EVM address as the account identifier
      // The backend will need to handle EVM address authentication
      const response = await authApi.walletConnect({
        hedera_account_id: evmAddress, // Using EVM address
        signature: signature,
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
      
      if (error.code === 4001) {
        toast.error('Signature Rejected', {
          description: 'You rejected the signature request',
        });
      } else {
        toast.error('Authentication Failed', {
          description: error.response?.data?.detail || error.message || 'Please try again',
        });
      }
      setIsConnecting(false);
    }
  }, []);

  const disconnect = useCallback(async () => {
    setWalletState({ 
      isConnected: false, 
      accountId: null,
      evmAddress: null,
    });
    toast.info('Wallet disconnected');
  }, []);

  const sendHbarPayment = useCallback(async (params: {
    to: string;
    amount: number;
    memo: string;
  }) => {
    if (!walletState.evmAddress) {
      throw new Error('Wallet not connected');
    }

    if (typeof window.ethereum === 'undefined') {
      throw new Error('MetaMask not found');
    }

    try {
      console.log('Preparing HBAR payment:', params);

      // Convert HBAR amount to tinybar (1 HBAR = 100,000,000 tinybar)
      const tinybarAmount = Math.floor(params.amount * 100_000_000);
      
      // Convert to hex (wei equivalent for Hedera)
      const amountHex = '0x' + tinybarAmount.toString(16);

      console.log(`Sending ${params.amount} HBAR (${tinybarAmount} tinybar) = ${amountHex}`);

      // Request transaction from MetaMask
      const txHash = await window.ethereum.request({
        method: 'eth_sendTransaction',
        params: [{
          from: walletState.evmAddress,
          to: params.to,
          value: amountHex,
          data: '0x' + Buffer.from(params.memo, 'utf8').toString('hex'), // Encode memo as hex
        }],
      });

      console.log('Transaction submitted:', txHash);

      // Wait for transaction receipt
      let receipt = null;
      let attempts = 0;
      const maxAttempts = 30; // 30 seconds timeout

      while (!receipt && attempts < maxAttempts) {
        try {
          receipt = await window.ethereum.request({
            method: 'eth_getTransactionReceipt',
            params: [txHash],
          });
          
          if (!receipt) {
            await new Promise(resolve => setTimeout(resolve, 1000));
            attempts++;
          }
        } catch (error) {
          console.error('Error getting receipt:', error);
          await new Promise(resolve => setTimeout(resolve, 1000));
          attempts++;
        }
      }

      if (!receipt) {
        throw new Error('Transaction receipt not received within timeout');
      }

      console.log('Transaction confirmed:', receipt);

      return {
        transactionHash: txHash,
        status: receipt.status === '0x1' ? 'success' : 'failed',
        receipt,
      };
    } catch (error: any) {
      console.error('Payment failed:', error);
      
      if (error.code === 4001) {
        throw new Error('Transaction rejected by user');
      }
      
      throw error;
    }
  }, [walletState.evmAddress]);

  const getBalance = useCallback(async (): Promise<number | null> => {
    if (!walletState.evmAddress) {
      return null;
    }

    if (typeof window.ethereum === 'undefined') {
      return null;
    }

    try {
      const balanceHex = await window.ethereum.request({
        method: 'eth_getBalance',
        params: [walletState.evmAddress, 'latest'],
      });

      // Convert from hex wei to HBAR (1 HBAR = 100,000,000 tinybar)
      const balanceTinybar = parseInt(balanceHex, 16);
      const balanceHbar = balanceTinybar / 100_000_000;

      return balanceHbar;
    } catch (error) {
      console.error('Failed to get balance:', error);
      return null;
    }
  }, [walletState.evmAddress]);

  return {
    walletState,
    isConnecting,
    isMetaMaskInstalled,
    connectMetaMask,
    disconnect,
    sendHbarPayment,
    getBalance,
    recheckMetaMask: checkMetaMaskInstalled,
  };
};
