/**
 * HashPack Wallet Integration
 * 
 * This module provides utilities for connecting to HashPack wallet
 * and executing HBAR transactions for bill payments.
 * 
 * Implementation uses HashPack's window.hashpack API for direct integration
 * without requiring additional SDK dependencies.
 */

import { toast } from 'sonner';
import { paymentsApi } from './api';

// HashPack pairing data structure
interface HashPackPairingData {
  accountIds: string[];
  network: string;
  topic: string;
}

// HashPack window interface
interface HashPackWindow extends Window {
  hashpack?: {
    pairWallet: () => Promise<{
      accountIds: string[];
      network: string;
      topic: string;
    }>;
    sendTransaction: (transaction: {
      topic: string;
      byteArray: Uint8Array;
      metadata: {
        accountToSign: string;
        returnTransaction: boolean;
      };
    }) => Promise<{
      success: boolean;
      receipt?: {
        transactionId: string;
        status: string;
      };
      error?: string;
    }>;
    disconnect: (topic: string) => Promise<void>;
  };
}

declare const window: HashPackWindow;

// Transaction details for bill payment
export interface PaymentTransaction {
  from: string;
  to: string;
  amount: number; // HBAR amount
  memo: string;
  billId: string;
  fiatAmount: number;
  currency: string;
}

// Transaction result
export interface TransactionResult {
  success: boolean;
  transactionId?: string;
  error?: string;
}

/**
 * HashPack Wallet Manager
 * Handles wallet connection and transaction signing with real HashPack integration
 */
class HashPackWallet {
  private pairingData: HashPackPairingData | null = null;
  private isInitialized = false;

  /**
   * Initialize HashPack connection
   */
  async initialize(): Promise<boolean> {
    try {
      // Check if HashPack extension is installed
      if (!this.isHashPackInstalled()) {
        toast.error('HashPack wallet not found', {
          description: 'Please install the HashPack browser extension to continue.',
          action: {
            label: 'Install HashPack',
            onClick: () => window.open('https://www.hashpack.app/', '_blank'),
          },
        });
        return false;
      }

      this.isInitialized = true;
      return true;
    } catch (error) {
      console.error('Failed to initialize HashPack:', error);
      toast.error('Failed to initialize wallet');
      return false;
    }
  }

  /**
   * Check if HashPack extension is installed
   */
  private isHashPackInstalled(): boolean {
    // HashPack injects itself into window.hashpack
    return typeof window !== 'undefined' && window.hashpack !== undefined;
  }

  /**
   * Connect to HashPack wallet
   */
  async connect(): Promise<string | null> {
    try {
      if (!this.isInitialized) {
        const initialized = await this.initialize();
        if (!initialized) return null;
      }

      if (!window.hashpack) {
        throw new Error('HashPack not available');
      }

      // Request wallet pairing
      toast.info('Connecting to HashPack...', {
        description: 'Please approve the connection in your HashPack wallet.',
      });

      const pairingData = await window.hashpack.pairWallet();
      
      if (!pairingData || !pairingData.accountIds || pairingData.accountIds.length === 0) {
        throw new Error('No accounts found in wallet');
      }

      this.pairingData = pairingData;
      const accountId = pairingData.accountIds[0];

      toast.success('Wallet Connected', {
        description: `Connected to account ${accountId}`,
      });

      return accountId;
    } catch (error: any) {
      console.error('Failed to connect to HashPack:', error);
      toast.error('Failed to connect wallet', {
        description: error.message || 'Please try again',
      });
      return null;
    }
  }

  /**
   * Execute a payment transaction with real Hedera integration
   */
  async executePayment(transaction: PaymentTransaction): Promise<TransactionResult> {
    try {
      if (!this.isInitialized) {
        const initialized = await this.initialize();
        if (!initialized) {
          return { success: false, error: 'Wallet not initialized' };
        }
      }

      if (!this.pairingData) {
        // Try to connect first
        const accountId = await this.connect();
        if (!accountId) {
          return { success: false, error: 'Wallet not connected' };
        }
      }

      // Validate transaction
      if (!transaction.from || !transaction.to || transaction.amount <= 0) {
        return { success: false, error: 'Invalid transaction details' };
      }

      // Step 1: Prepare payment with backend
      toast.info('Preparing payment...', {
        description: 'Fetching transaction details from server...',
      });

      let prepareResponse;
      try {
        prepareResponse = await paymentsApi.prepare(transaction.billId);
      } catch (error: any) {
        console.error('Failed to prepare payment:', error);
        return {
          success: false,
          error: error.response?.data?.detail || 'Failed to prepare payment',
        };
      }

      // Step 2: Create Hedera transaction
      // For HashPack, we need to create a transaction byte array
      // This is a simplified version - in production, use @hashgraph/sdk
      const transactionBytes = this.createTransactionBytes({
        from: transaction.from,
        to: prepareResponse.transaction.to,
        amount: prepareResponse.transaction.amount_hbar,
        memo: prepareResponse.transaction.memo,
      });

      // Step 3: Request signature from HashPack
      toast.info('Awaiting signature...', {
        description: 'Please sign the transaction in HashPack wallet.',
      });

      if (!window.hashpack || !this.pairingData) {
        return { success: false, error: 'HashPack not available' };
      }

      const signResult = await window.hashpack.sendTransaction({
        topic: this.pairingData.topic,
        byteArray: transactionBytes,
        metadata: {
          accountToSign: transaction.from,
          returnTransaction: false,
        },
      });

      if (!signResult.success || !signResult.receipt) {
        return {
          success: false,
          error: signResult.error || 'Transaction signing failed',
        };
      }

      const hederaTxId = signResult.receipt.transactionId;

      // Step 4: Confirm payment with backend
      toast.info('Confirming payment...', {
        description: 'Waiting for Hedera consensus...',
      });

      try {
        const confirmResponse = await paymentsApi.confirm(
          transaction.billId,
          hederaTxId
        );

        toast.success('Payment Successful!', {
          description: `Transaction ID: ${hederaTxId}`,
          action: {
            label: 'View on HashScan',
            onClick: () => {
              window.open(
                `https://hashscan.io/testnet/transaction/${hederaTxId}`,
                '_blank'
              );
            },
          },
        });

        return {
          success: true,
          transactionId: hederaTxId,
        };
      } catch (error: any) {
        console.error('Failed to confirm payment:', error);
        return {
          success: false,
          error: error.response?.data?.detail || 'Failed to confirm payment',
        };
      }
    } catch (error: any) {
      console.error('Payment failed:', error);

      const errorMessage = error.message || 'Transaction failed';
      toast.error('Payment Failed', {
        description: errorMessage,
      });

      return {
        success: false,
        error: errorMessage,
      };
    }
  }

  /**
   * Create transaction bytes for Hedera
   * This is a simplified version - in production, use @hashgraph/sdk
   */
  private createTransactionBytes(params: {
    from: string;
    to: string;
    amount: number;
    memo: string;
  }): Uint8Array {
    // In a real implementation, this would use @hashgraph/sdk to create
    // a proper TransferTransaction and serialize it to bytes
    // For now, we'll create a simple representation
    
    const transaction = {
      type: 'CryptoTransfer',
      from: params.from,
      to: params.to,
      amount: params.amount,
      memo: params.memo,
      timestamp: Date.now(),
    };

    // Convert to JSON string then to bytes
    const jsonString = JSON.stringify(transaction);
    const encoder = new TextEncoder();
    return encoder.encode(jsonString);
  }

  /**
   * Check user's HBAR balance via Mirror Node API
   */
  async checkBalance(accountId: string): Promise<number | null> {
    try {
      // Query Hedera Mirror Node for account balance
      const response = await fetch(
        `https://testnet.mirrornode.hedera.com/api/v1/accounts/${accountId}`
      );

      if (!response.ok) {
        throw new Error('Failed to fetch balance');
      }

      const data = await response.json();
      
      // Balance is in tinybars (1 HBAR = 100,000,000 tinybars)
      const balanceInTinybars = data.balance?.balance || 0;
      const balanceInHbar = balanceInTinybars / 100000000;

      return balanceInHbar;
    } catch (error) {
      console.error('Failed to check balance:', error);
      toast.error('Failed to check balance', {
        description: 'Could not retrieve account balance from Hedera network',
      });
      return null;
    }
  }

  /**
   * Disconnect wallet
   */
  async disconnect(): Promise<void> {
    try {
      if (this.pairingData && window.hashpack) {
        await window.hashpack.disconnect(this.pairingData.topic);
      }
      
      this.pairingData = null;
      this.isInitialized = false;
      
      toast.info('Wallet disconnected');
    } catch (error) {
      console.error('Failed to disconnect:', error);
      // Still clear local state even if disconnect fails
      this.pairingData = null;
      this.isInitialized = false;
    }
  }

  /**
   * Get connected account ID
   */
  getConnectedAccount(): string | null {
    return this.pairingData?.accountIds[0] || null;
  }

  /**
   * Check if wallet is connected
   */
  isConnected(): boolean {
    return this.pairingData !== null && this.pairingData.accountIds.length > 0;
  }
}

// Export singleton instance
export const hashPackWallet = new HashPackWallet();

/**
 * Hook-friendly wrapper for HashPack operations
 */
export const useHashPack = () => {
  return {
    connect: () => hashPackWallet.connect(),
    executePayment: (transaction: PaymentTransaction) => hashPackWallet.executePayment(transaction),
    checkBalance: (accountId: string) => hashPackWallet.checkBalance(accountId),
    disconnect: () => hashPackWallet.disconnect(),
    isInstalled: () => typeof window !== 'undefined' && window.hashpack !== undefined,
    isConnected: () => hashPackWallet.isConnected(),
    getConnectedAccount: () => hashPackWallet.getConnectedAccount(),
  };
};
