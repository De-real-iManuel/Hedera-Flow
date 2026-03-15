/**
 * MetaMask + WalletConnect Integration Service
 * Handles MetaMask web extension and mobile app connections
 */

import { ethers } from 'ethers';

export interface WalletProvider {
  name: string;
  id: string;
  icon?: string;
  isInstalled: boolean;
  connect: () => Promise<WalletConnection>;
}

export interface WalletConnection {
  address: string;
  network: string;
  provider: string;
  chainId: number;
  signMessage: (message: string) => Promise<string>;
  disconnect: () => Promise<void>;
}

export interface TransactionRequest {
  to: string;
  value: string; // ETH amount in wei
  data?: string;
}

export interface TransactionResult {
  hash: string;
  status: 'pending' | 'success' | 'failed';
  blockNumber?: number;
  explorerUrl?: string;
}

class WalletIntegrationService {
  private connection: WalletConnection | null = null;
  private provider: ethers.BrowserProvider | null = null;
  private walletConnectProvider: any = null;

  /**
   * Debug method to check what's available on window object
   */
  debugWalletDetection(): void {
    if (typeof window === 'undefined') {
      console.log('Window object not available (SSR)');
      return;
    }

    console.log('=== Wallet Detection Debug ===');
    const ethereum = (window as any).ethereum;
    console.log('window.ethereum:', !!ethereum);
    
    if (ethereum) {
      console.log('ethereum.isMetaMask:', ethereum.isMetaMask);
      console.log('ethereum.isPhantom:', ethereum.isPhantom);
      console.log('ethereum.isBraveWallet:', ethereum.isBraveWallet);
      
      if (ethereum.providers) {
        console.log('Multiple providers detected:', ethereum.providers.length);
        ethereum.providers.forEach((provider: any, index: number) => {
          console.log(`Provider ${index}:`, {
            isMetaMask: provider.isMetaMask,
            isPhantom: provider.isPhantom,
            isBraveWallet: provider.isBraveWallet,
          });
        });
      }
    }
    
    console.log('MetaMask detected:', this.isMetaMaskInstalled());
    console.log('===============================');
  }

  /**
   * Check if MetaMask is installed
   */
  private isMetaMaskInstalled(): boolean {
    if (typeof window === 'undefined') return false;
    const ethereum = (window as any).ethereum;
    
    // Check if ethereum object exists and is MetaMask specifically
    if (!ethereum) return false;
    
    // Handle multiple wallet extensions
    if (ethereum.providers) {
      // Multiple wallets detected, find MetaMask
      return ethereum.providers.some((provider: any) => provider.isMetaMask);
    }
    
    // Single wallet, check if it's MetaMask
    return ethereum.isMetaMask === true;
  }

  /**
   * Get MetaMask provider specifically (handle multiple wallets)
   */
  private getMetaMaskProvider(): any {
    if (typeof window === 'undefined') return null;
    const ethereum = (window as any).ethereum;
    
    if (!ethereum) return null;
    
    // Handle multiple wallet extensions
    if (ethereum.providers) {
      return ethereum.providers.find((provider: any) => provider.isMetaMask);
    }
    
    // Single wallet
    return ethereum.isMetaMask ? ethereum : null;
  }

  /**
   * Get available wallet providers
   */
  getAvailableWallets(): WalletProvider[] {
    const wallets: WalletProvider[] = [];

    if (typeof window === 'undefined') {
      return wallets;
    }

    // MetaMask Web Extension
    if (this.isMetaMaskInstalled()) {
      wallets.push({
        name: 'MetaMask',
        id: 'metamask',
        icon: '/icons/metamask.svg',
        isInstalled: true,
        connect: () => this.connectMetaMask(),
      });
    }

    // Only show WalletConnect if user doesn't have MetaMask or wants mobile option
    wallets.push({
      name: 'WalletConnect (Mobile)',
      id: 'walletconnect',
      icon: '/icons/walletconnect.svg',
      isInstalled: true, // Always available
      connect: () => this.connectWalletConnect(),
    });

    console.log(`Found ${wallets.length} wallet option(s):`, wallets.map(w => w.name));
    return wallets;
  }

  /**
   * Connect to MetaMask
   */
  private async connectMetaMask(): Promise<WalletConnection> {
    const ethereum = this.getMetaMaskProvider();
    
    if (!ethereum) {
      throw new Error('MetaMask not found. Please install MetaMask extension.');
    }

    try {
      // Request account access
      const accounts = await ethereum.request({
        method: 'eth_requestAccounts',
      });

      if (!accounts || accounts.length === 0) {
        throw new Error('No accounts found in MetaMask');
      }

      // Get network info
      const chainId = await ethereum.request({ method: 'eth_chainId' });
      const networkId = parseInt(chainId, 16);

      this.provider = new ethers.BrowserProvider(ethereum);
      const signer = await this.provider.getSigner();

      const connection: WalletConnection = {
        address: accounts[0],
        network: this.getNetworkName(networkId),
        provider: 'metamask',
        chainId: networkId,
        signMessage: async (message: string) => {
          return await signer.signMessage(message);
        },
        disconnect: async () => {
          this.connection = null;
          this.provider = null;
        },
      };

      this.connection = connection;
      return connection;
    } catch (error) {
      console.error('MetaMask connection failed:', error);
      
      // Handle specific MetaMask errors
      if (error instanceof Error) {
        if (error.message.includes('User rejected')) {
          throw new Error('Connection cancelled by user');
        }
        if (error.message.includes('Already processing')) {
          throw new Error('MetaMask is busy. Please try again.');
        }
      }
      
      throw new Error(`Failed to connect to MetaMask: ${error}`);
    }
  }

  /**
   * Connect via WalletConnect
   */
  private async connectWalletConnect(): Promise<WalletConnection> {
    try {
      // Dynamic import to avoid SSR issues
      const { EthereumProvider } = await import('@walletconnect/ethereum-provider');
      
      const provider = await EthereumProvider.init({
        projectId: import.meta.env.VITE_WALLETCONNECT_PROJECT_ID || 'a410efc0d43c137138330074a67cdf07',
        chains: [1, 5, 11155111], // Mainnet, Goerli, Sepolia
        showQrModal: true,
        metadata: {
          name: 'Hedera Flow',
          description: 'Decentralized Utility Payment Platform',
          url: window.location.origin,
          icons: [`${window.location.origin}/logo.png`],
        },
        // Add connection options for better reliability
        relayUrl: 'wss://relay.walletconnect.com',
        logger: 'error', // Reduce logging noise
      });

      // Add connection timeout
      const connectPromise = provider.enable();
      const timeoutPromise = new Promise((_, reject) => {
        setTimeout(() => reject(new Error('Connection timeout after 30 seconds')), 30000);
      });

      const accounts = await Promise.race([connectPromise, timeoutPromise]) as string[];
      
      if (!accounts || accounts.length === 0) {
        throw new Error('No accounts found');
      }

      const chainId = provider.chainId;
      this.walletConnectProvider = provider;
      this.provider = new ethers.BrowserProvider(provider);
      const signer = await this.provider.getSigner();

      const connection: WalletConnection = {
        address: accounts[0],
        network: this.getNetworkName(chainId),
        provider: 'walletconnect',
        chainId: chainId,
        signMessage: async (message: string) => {
          return await signer.signMessage(message);
        },
        disconnect: async () => {
          if (this.walletConnectProvider) {
            await this.walletConnectProvider.disconnect();
            this.walletConnectProvider = null;
          }
          this.connection = null;
          this.provider = null;
        },
      };

      this.connection = connection;
      return connection;
    } catch (error) {
      console.error('WalletConnect connection failed:', error);
      
      // Provide more specific error messages
      if (error instanceof Error) {
        if (error.message.includes('timeout')) {
          throw new Error('Connection timed out. Please try again or use MetaMask instead.');
        }
        if (error.message.includes('reset')) {
          throw new Error('Connection was reset. Please refresh the page and try again.');
        }
        if (error.message.includes('WebSocket')) {
          throw new Error('Network connection issue. Please check your internet and try again.');
        }
      }
      
      throw new Error(`Failed to connect via WalletConnect: ${error}`);
    }
  }

  /**
   * Get network name from chain ID
   */
  private getNetworkName(chainId: number): string {
    switch (chainId) {
      case 1: return 'mainnet';
      case 5: return 'goerli';
      case 11155111: return 'sepolia';
      case 137: return 'polygon';
      case 80001: return 'mumbai';
      default: return `chain-${chainId}`;
    }
  }

  /**
   * Get current wallet connection
   */
  getCurrentConnection(): WalletConnection | null {
    return this.connection;
  }

  /**
   * Check if wallet is connected
   */
  isConnected(): boolean {
    return this.connection !== null;
  }

  /**
   * Send ETH transaction
   */
  async sendTransaction(request: TransactionRequest): Promise<TransactionResult> {
    if (!this.connection || !this.provider) {
      throw new Error('No wallet connected. Please connect a wallet first.');
    }

    try {
      const signer = await this.provider.getSigner();
      
      const tx = await signer.sendTransaction({
        to: request.to,
        value: request.value,
        data: request.data || '0x',
      });

      const result: TransactionResult = {
        hash: tx.hash,
        status: 'pending',
        explorerUrl: this.getExplorerUrl(tx.hash),
      };

      // Wait for confirmation
      tx.wait().then((receipt) => {
        result.status = receipt.status === 1 ? 'success' : 'failed';
        result.blockNumber = receipt.blockNumber;
      }).catch(() => {
        result.status = 'failed';
      });

      return result;
    } catch (error) {
      console.error('Transaction failed:', error);
      throw new Error(`Transaction failed: ${error}`);
    }
  }

  /**
   * Disconnect current wallet
   */
  async disconnect(): Promise<void> {
    if (this.connection) {
      await this.connection.disconnect();
    }
  }

  /**
   * Get network explorer URL for transaction
   */
  getExplorerUrl(txHash: string): string {
    const chainId = this.connection?.chainId || 1;
    switch (chainId) {
      case 1: return `https://etherscan.io/tx/${txHash}`;
      case 5: return `https://goerli.etherscan.io/tx/${txHash}`;
      case 11155111: return `https://sepolia.etherscan.io/tx/${txHash}`;
      case 137: return `https://polygonscan.com/tx/${txHash}`;
      case 80001: return `https://mumbai.polygonscan.com/tx/${txHash}`;
      default: return `https://etherscan.io/tx/${txHash}`;
    }
  }

  /**
   * Get network explorer URL for account
   */
  getAccountExplorerUrl(address: string): string {
    const chainId = this.connection?.chainId || 1;
    switch (chainId) {
      case 1: return `https://etherscan.io/address/${address}`;
      case 5: return `https://goerli.etherscan.io/address/${address}`;
      case 11155111: return `https://sepolia.etherscan.io/address/${address}`;
      case 137: return `https://polygonscan.com/address/${address}`;
      case 80001: return `https://mumbai.polygonscan.com/address/${address}`;
      default: return `https://etherscan.io/address/${address}`;
    }
  }
}

export const walletService = new WalletIntegrationService();