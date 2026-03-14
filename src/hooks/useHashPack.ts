import { useState, useEffect, useCallback } from 'react';
import { HashConnect, HashConnectTypes, MessageTypes } from '@hashgraph/hedera-wallet-connect';

interface HashPackState {
  accountId: string | null;
  isConnected: boolean;
  isConnecting: boolean;
  error: string | null;
}

export const useHashPack = () => {
  const [state, setState] = useState<HashPackState>({
    accountId: null,
    isConnected: false,
    isConnecting: false,
    error: null,
  });
  
  const [hashConnect, setHashConnect] = useState<HashConnect | null>(null);
  const [pairingData, setPairingData] = useState<HashConnectTypes.SavedPairingData | null>(null);

  // Initialize HashConnect
  useEffect(() => {
    const init = async () => {
      try {
        const hc = new HashConnect();
        
        // Initialize with app metadata
        const appMetadata: HashConnectTypes.AppMetadata = {
          name: "Hedera Flow",
          description: "Blockchain-powered utility payments platform",
          icon: window.location.origin + "/logo.png",
          url: window.location.origin
        };

        await hc.init(appMetadata, "testnet", false);
        
        // Listen for pairing events
        hc.pairingEvent.on((data) => {
          console.log('HashPack paired:', data);
          setPairingData(data);
          
          if (data.accountIds && data.accountIds.length > 0) {
            setState(prev => ({
              ...prev,
              accountId: data.accountIds[0],
              isConnected: true,
              isConnecting: false,
            }));
          }
        });

        // Listen for disconnect events
        hc.disconnectionEvent.on(() => {
          console.log('HashPack disconnected');
          setState({
            accountId: null,
            isConnected: false,
            isConnecting: false,
            error: null,
          });
          setPairingData(null);
        });

        setHashConnect(hc);
        
        // Check for existing pairing
        const savedPairings = hc.hcData.savedPairings;
        if (savedPairings && savedPairings.length > 0) {
          const pairing = savedPairings[0];
          setPairingData(pairing);
          setState(prev => ({
            ...prev,
            accountId: pairing.accountIds[0],
            isConnected: true,
          }));
        }
      } catch (error) {
        console.error('HashConnect initialization error:', error);
        setState(prev => ({
          ...prev,
          error: 'Failed to initialize HashPack connection',
        }));
      }
    };

    init();

    return () => {
      // Cleanup
      if (hashConnect) {
        hashConnect.disconnect();
      }
    };
  }, []);

  // Connect to HashPack wallet
  const connect = useCallback(async () => {
    if (!hashConnect) {
      setState(prev => ({ ...prev, error: 'HashConnect not initialized' }));
      return;
    }

    try {
      setState(prev => ({ ...prev, isConnecting: true, error: null }));
      
      // Connect to extension
      await hashConnect.connectToLocalWallet();
      
      // The pairing event will update the state
    } catch (error: any) {
      console.error('HashPack connection error:', error);
      setState(prev => ({
        ...prev,
        isConnecting: false,
        error: error.message || 'Failed to connect to HashPack',
      }));
    }
  }, [hashConnect]);

  // Disconnect from HashPack
  const disconnect = useCallback(async () => {
    if (!hashConnect || !pairingData) return;

    try {
      await hashConnect.disconnect(pairingData.topic);
      setState({
        accountId: null,
        isConnected: false,
        isConnecting: false,
        error: null,
      });
      setPairingData(null);
    } catch (error: any) {
      console.error('HashPack disconnection error:', error);
      setState(prev => ({
        ...prev,
        error: error.message || 'Failed to disconnect from HashPack',
      }));
    }
  }, [hashConnect, pairingData]);

  // Send HBAR payment
  const sendHbarPayment = useCallback(async (params: {
    to: string;
    amount: number;
    memo: string;
  }) => {
    if (!hashConnect || !pairingData || !state.accountId) {
      throw new Error('HashPack not connected');
    }

    try {
      console.log('Preparing HBAR payment:', params);

      // Convert HBAR to tinybars (1 HBAR = 100,000,000 tinybars)
      const amountInTinybars = Math.floor(params.amount * 100000000);

      // Create transaction
      const transaction: MessageTypes.Transaction = {
        topic: pairingData.topic,
        byteArray: new Uint8Array(), // Will be populated by HashConnect
        metadata: {
          accountToSign: state.accountId,
          returnTransaction: false,
        }
      };

      // Build transfer transaction
      const transferTransaction = {
        transfers: [
          {
            accountId: state.accountId,
            amount: -amountInTinybars, // Negative for sender
          },
          {
            accountId: params.to,
            amount: amountInTinybars, // Positive for receiver
          }
        ],
        memo: params.memo,
      };

      console.log('Sending transaction:', transferTransaction);

      // Send transaction through HashConnect
      const response = await hashConnect.sendTransaction(
        pairingData.topic,
        transferTransaction
      );

      console.log('Transaction response:', response);

      if (response.success) {
        return {
          status: 'success' as const,
          transactionHash: response.receipt?.transactionId || '',
          receipt: response.receipt,
        };
      } else {
        throw new Error(response.error?.message || 'Transaction failed');
      }
    } catch (error: any) {
      console.error('HashPack payment error:', error);
      throw new Error(error.message || 'Failed to send payment');
    }
  }, [hashConnect, pairingData, state.accountId]);

  // Get account balance
  const getBalance = useCallback(async (): Promise<number | null> => {
    if (!state.accountId) return null;

    try {
      // Query Mirror Node for account balance
      const response = await fetch(
        `https://testnet.mirrornode.hedera.com/api/v1/accounts/${state.accountId}`
      );
      
      if (!response.ok) {
        throw new Error('Failed to fetch balance');
      }

      const data = await response.json();
      const balanceInTinybars = data.balance?.balance || 0;
      const balanceInHbar = balanceInTinybars / 100000000;
      
      return balanceInHbar;
    } catch (error) {
      console.error('Error fetching balance:', error);
      return null;
    }
  }, [state.accountId]);

  return {
    // State
    accountId: state.accountId,
    isConnected: state.isConnected,
    isConnecting: state.isConnecting,
    error: state.error,
    
    // Methods
    connect,
    disconnect,
    sendHbarPayment,
    getBalance,
  };
};

export default useHashPack;
