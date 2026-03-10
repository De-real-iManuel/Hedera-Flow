import { motion } from 'framer-motion';
import { Wallet, Loader2, ExternalLink } from 'lucide-react';
import { useMetaMaskHedera } from '@/hooks/useMetaMaskHedera';

interface WalletConnectProps {
  onSuccess?: () => void;
}

const WalletConnect = ({ onSuccess }: WalletConnectProps) => {
  const { 
    isConnecting, 
    connectMetaMask, 
    isMetaMaskInstalled,
    recheckMetaMask 
  } = useMetaMaskHedera();

  return (
    <div className="space-y-3">
      {!isMetaMaskInstalled && (
        <div className="p-3 rounded-lg bg-amber-50 border border-amber-200 text-xs">
          <p className="font-medium text-amber-900">MetaMask Not Detected</p>
          <p className="text-amber-700 mt-1">Please install MetaMask to connect your wallet.</p>
          <a
            href="https://metamask.io/download/"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1 text-amber-800 hover:text-amber-900 font-medium hover:underline mt-2"
          >
            Download MetaMask
            <ExternalLink className="w-3 h-3" />
          </a>
        </div>
      )}

      <motion.button
        type="button"
        onClick={connectMetaMask}
        disabled={isConnecting}
        whileHover={{ scale: isConnecting ? 1 : 1.02 }}
        whileTap={{ scale: isConnecting ? 1 : 0.98 }}
        className={`w-full py-4 rounded-2xl border-2 font-semibold text-base flex items-center justify-center gap-3 transition-all ${
          isConnecting
            ? 'bg-gray-100 border-gray-200 text-gray-400 cursor-not-allowed'
            : 'bg-gradient-to-r from-orange-500 to-orange-600 border-transparent text-white hover:shadow-lg'
        }`}
      >
        {isConnecting ? (
          <>
            <Loader2 className="w-5 h-5 animate-spin" />
            <span>Connecting...</span>
          </>
        ) : (
          <>
            <div className="w-6 h-6 rounded-lg bg-white/20 flex items-center justify-center">
              <Wallet className="w-4 h-4" />
            </div>
            <span>Connect with MetaMask</span>
          </>
        )}
      </motion.button>

      <p className="text-xs text-center text-muted-foreground">
        Connect MetaMask to Hedera Testnet for payments
      </p>
    </div>
  );
};

export default WalletConnect;
