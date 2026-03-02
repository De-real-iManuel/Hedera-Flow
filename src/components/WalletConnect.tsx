import { motion } from 'framer-motion';
import { Wallet, Loader2, AlertCircle, ExternalLink } from 'lucide-react';
import { useHashPackDirect } from '@/hooks/useHashPackDirect';

interface WalletConnectProps {
  onSuccess?: () => void;
}

const WalletConnect = ({ onSuccess }: WalletConnectProps) => {
  const { isConnecting, connectHashPack, isHashPackInstalled } = useHashPackDirect();

  return (
    <div className="space-y-3">
      {/* Show warning if HashPack not detected */}
      {!isHashPackInstalled && !isConnecting && (
        <div className="p-4 rounded-lg bg-amber-50 border border-amber-200">
          <div className="flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
            <div className="flex-1">
              <p className="text-sm font-medium text-amber-900">
                HashPack Extension Not Detected
              </p>
              <p className="text-xs text-amber-700 mt-1">
                Please install the HashPack browser extension to connect your wallet.
              </p>
              <a
                href="https://www.hashpack.app/download"
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1 text-xs text-amber-800 hover:text-amber-900 font-medium mt-2 hover:underline"
              >
                Download HashPack
                <ExternalLink className="w-3 h-3" />
              </a>
            </div>
          </div>
        </div>
      )}

      {/* HashPack Connect Button */}
      <motion.button
        type="button"
        onClick={connectHashPack}
        disabled={isConnecting}
        whileHover={{ scale: isConnecting ? 1 : 1.02 }}
        whileTap={{ scale: isConnecting ? 1 : 0.98 }}
        className={`w-full py-4 rounded-2xl border-2 font-semibold text-base flex items-center justify-center gap-3 transition-all ${
          isConnecting
            ? 'bg-gray-100 border-gray-200 text-gray-400 cursor-not-allowed'
            : 'bg-gradient-to-r from-purple-600 to-blue-600 border-transparent text-white hover:shadow-lg'
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
            <span>Connect HashPack Wallet</span>
          </>
        )}
      </motion.button>

      {/* Info text */}
      <div className="text-xs text-center text-muted-foreground space-y-1">
        <p>
          {isHashPackInstalled 
            ? 'Click above to connect your HashPack wallet' 
            : 'Install HashPack extension first, then refresh this page'}
        </p>
        {isHashPackInstalled && (
          <p className="text-green-600 font-medium">
            ✓ HashPack detected
          </p>
        )}
      </div>
    </div>
  );
};

export default WalletConnect;
