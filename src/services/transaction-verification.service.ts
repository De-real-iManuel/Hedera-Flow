/**
 * Transaction Verification Service
 * Verifies Hedera transactions using Mirror Node API
 */

export interface TransactionStatus {
  transactionId: string;
  status: 'pending' | 'success' | 'failed' | 'unknown';
  consensusTimestamp?: string;
  result?: string;
  transfers?: Array<{
    account: string;
    amount: number;
  }>;
  memo?: string;
  explorerUrl: string;
}

export interface MirrorNodeResponse {
  transactions: Array<{
    transaction_id: string;
    consensus_timestamp: string;
    result: string;
    transfers: Array<{
      account: string;
      amount: number;
    }>;
    memo_base64?: string;
  }>;
}

class TransactionVerificationService {
  private readonly MIRROR_NODE_URL = 'https://testnet.mirrornode.hedera.com'; // Change for mainnet
  private readonly NETWORK = 'testnet'; // Change for mainnet

  /**
   * Verify a transaction by ID
   */
  async verifyTransaction(transactionId: string): Promise<TransactionStatus> {
    try {
      const response = await fetch(
        `${this.MIRROR_NODE_URL}/api/v1/transactions/${transactionId}`,
        {
          method: 'GET',
          headers: {
            'Accept': 'application/json',
          },
        }
      );

      if (!response.ok) {
        if (response.status === 404) {
          return {
            transactionId,
            status: 'pending',
            explorerUrl: this.getExplorerUrl(transactionId),
          };
        }
        throw new Error(`Mirror node request failed: ${response.status}`);
      }

      const data: MirrorNodeResponse = await response.json();
      
      if (!data.transactions || data.transactions.length === 0) {
        return {
          transactionId,
          status: 'pending',
          explorerUrl: this.getExplorerUrl(transactionId),
        };
      }

      const transaction = data.transactions[0];
      
      return {
        transactionId,
        status: transaction.result === 'SUCCESS' ? 'success' : 'failed',
        consensusTimestamp: transaction.consensus_timestamp,
        result: transaction.result,
        transfers: transaction.transfers,
        memo: transaction.memo_base64 ? atob(transaction.memo_base64) : undefined,
        explorerUrl: this.getExplorerUrl(transactionId),
      };

    } catch (error) {
      console.error('Transaction verification failed:', error);
      return {
        transactionId,
        status: 'unknown',
        explorerUrl: this.getExplorerUrl(transactionId),
      };
    }
  }

  /**
   * Poll transaction status until confirmed or timeout
   */
  async pollTransactionStatus(
    transactionId: string,
    maxAttempts: number = 30,
    intervalMs: number = 2000
  ): Promise<TransactionStatus> {
    for (let attempt = 0; attempt < maxAttempts; attempt++) {
      const status = await this.verifyTransaction(transactionId);
      
      if (status.status === 'success' || status.status === 'failed') {
        return status;
      }

      // Wait before next attempt
      await new Promise(resolve => setTimeout(resolve, intervalMs));
    }

    // Timeout reached
    return {
      transactionId,
      status: 'pending',
      explorerUrl: this.getExplorerUrl(transactionId),
    };
  }

  /**
   * Verify payment transaction matches expected parameters
   */
  async verifyPaymentTransaction(
    transactionId: string,
    expectedAmount: number,
    expectedRecipient: string,
    expectedSender?: string
  ): Promise<{
    isValid: boolean;
    status: TransactionStatus;
    errors: string[];
  }> {
    const status = await this.verifyTransaction(transactionId);
    const errors: string[] = [];

    if (status.status !== 'success') {
      errors.push(`Transaction not successful: ${status.result || 'pending'}`);
      return { isValid: false, status, errors };
    }

    if (!status.transfers || status.transfers.length === 0) {
      errors.push('No transfers found in transaction');
      return { isValid: false, status, errors };
    }

    // Find the transfer to the expected recipient
    const recipientTransfer = status.transfers.find(
      transfer => transfer.account === expectedRecipient && transfer.amount > 0
    );

    if (!recipientTransfer) {
      errors.push(`No transfer found to expected recipient: ${expectedRecipient}`);
      return { isValid: false, status, errors };
    }

    // Convert tinybar to HBAR (1 HBAR = 100,000,000 tinybar)
    const actualAmount = recipientTransfer.amount / 100_000_000;
    const tolerance = 0.00000001; // 1 tinybar tolerance

    if (Math.abs(actualAmount - expectedAmount) > tolerance) {
      errors.push(
        `Amount mismatch: expected ${expectedAmount} HBAR, got ${actualAmount} HBAR`
      );
      return { isValid: false, status, errors };
    }

    // Verify sender if provided
    if (expectedSender) {
      const senderTransfer = status.transfers.find(
        transfer => transfer.account === expectedSender && transfer.amount < 0
      );

      if (!senderTransfer) {
        errors.push(`No transfer found from expected sender: ${expectedSender}`);
        return { isValid: false, status, errors };
      }
    }

    return { isValid: true, status, errors: [] };
  }

  /**
   * Get account balance from Mirror Node
   */
  async getAccountBalance(accountId: string): Promise<{
    balance: number; // HBAR
    timestamp: string;
  } | null> {
    try {
      const response = await fetch(
        `${this.MIRROR_NODE_URL}/api/v1/accounts/${accountId}`,
        {
          method: 'GET',
          headers: {
            'Accept': 'application/json',
          },
        }
      );

      if (!response.ok) {
        throw new Error(`Account query failed: ${response.status}`);
      }

      const data = await response.json();
      
      return {
        balance: data.balance.balance / 100_000_000, // Convert tinybar to HBAR
        timestamp: data.balance.timestamp,
      };

    } catch (error) {
      console.error('Account balance query failed:', error);
      return null;
    }
  }

  /**
   * Get recent transactions for an account
   */
  async getAccountTransactions(
    accountId: string,
    limit: number = 10
  ): Promise<TransactionStatus[]> {
    try {
      const response = await fetch(
        `${this.MIRROR_NODE_URL}/api/v1/transactions?account.id=${accountId}&limit=${limit}&order=desc`,
        {
          method: 'GET',
          headers: {
            'Accept': 'application/json',
          },
        }
      );

      if (!response.ok) {
        throw new Error(`Transactions query failed: ${response.status}`);
      }

      const data: MirrorNodeResponse = await response.json();
      
      return data.transactions.map(tx => ({
        transactionId: tx.transaction_id,
        status: tx.result === 'SUCCESS' ? 'success' : 'failed',
        consensusTimestamp: tx.consensus_timestamp,
        result: tx.result,
        transfers: tx.transfers,
        memo: tx.memo_base64 ? atob(tx.memo_base64) : undefined,
        explorerUrl: this.getExplorerUrl(tx.transaction_id),
      }));

    } catch (error) {
      console.error('Account transactions query failed:', error);
      return [];
    }
  }

  /**
   * Get explorer URL for transaction
   */
  private getExplorerUrl(transactionId: string): string {
    return `https://hashscan.io/${this.NETWORK}/transaction/${transactionId}`;
  }

  /**
   * Get explorer URL for account
   */
  getAccountExplorerUrl(accountId: string): string {
    return `https://hashscan.io/${this.NETWORK}/account/${accountId}`;
  }

  /**
   * Validate transaction ID format
   */
  isValidTransactionId(transactionId: string): boolean {
    // Hedera transaction ID format: 0.0.X-SSSSSSSSSS-NNNNNNNNN
    const pattern = /^0\.0\.\d+-\d{10}-\d{9}$/;
    return pattern.test(transactionId);
  }

  /**
   * Validate account ID format
   */
  isValidAccountId(accountId: string): boolean {
    // Hedera account ID format: 0.0.X
    const pattern = /^0\.0\.\d+$/;
    return pattern.test(accountId);
  }
}

export const transactionVerificationService = new TransactionVerificationService();