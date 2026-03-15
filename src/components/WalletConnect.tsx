import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Wallet, ExternalLink, CheckCircle, AlertCircle, Loader2, RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { useToast } from "@/hooks/use-toast";
import { walletService, WalletProvider, WalletConnection } from "@/services/wallet-integration.service";

interface WalletConnectProps {
  onConnect?: (connection: WalletConnection) => void;
  onDisconnect?: () => void;
  showBalance?: boolean;
}

function WalletConnect({ onConnect, onDisconnect, showBalance = true }: WalletConnectProps) {
  const [availableWallets, setAvailableWallets] = useState<WalletProvider[]>([]);
  const [currentConnection, setCurrentConnection] = useState<WalletConnection | null>(null);
  const [isConnecting, setIsConnecting] = useState(false);
  const [connectingWallet, setConnectingWallet] = useState<string | null>(null);
  const { toast } = useToast();

  useEffect(() => {
    // Debug wallet detection
    walletService.debugWalletDetection();
    
    // Get available wallets on component mount
    const wallets = walletService.getAvailableWallets();
    setAvailableWallets(wallets);

    // Check if already connected
    const connection = walletService.getCurrentConnection();
    if (connection) {
      setCurrentConnection(connection);
    }
  }, []);

  const handleConnect = async (wallet: WalletProvider) => {
    setIsConnecting(true);
    setConnectingWallet(wallet.id);

    try {
      const connection = await wallet.connect();
      setCurrentConnection(connection);
      
      toast({
        title: "Wallet Connected",
        description: `Successfully connected to ${wallet.name}`,
      });

      onConnect?.(connection);
    } catch (error) {
      console.error("Wallet connection failed:", error);
      toast({
        title: "Connection Failed",
        description: error instanceof Error ? error.message : "Failed to connect wallet",
        variant: "destructive",
      });
    } finally {
      setIsConnecting(false);
      setConnectingWallet(null);
    }
  };

  const handleDisconnect = async () => {
    try {
      await walletService.disconnect();
      setCurrentConnection(null);
      
      toast({
        title: "Wallet Disconnected",
        description: "Successfully disconnected from wallet",
      });

      onDisconnect?.();
    } catch (error) {
      console.error("Disconnect failed:", error);
      toast({
        title: "Disconnect Failed",
        description: "Failed to disconnect wallet",
        variant: "destructive",
      });
    }
  };

  const refreshWallets = () => {
    walletService.debugWalletDetection();
    const wallets = walletService.getAvailableWallets();
    setAvailableWallets(wallets);
    
    toast({
      title: "Wallets Refreshed",
      description: `Found ${wallets.length} wallet(s). Check console for debug info.`,
    });
  };

  const formatAccountId = (accountId: string) => {
    if (accountId.length <= 12) return accountId;
    return `${accountId.slice(0, 6)}...${accountId.slice(-6)}`;
  };

  if (currentConnection) {
    return (
      <Card className="border-2 border-green-200 bg-green-50">
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <CheckCircle className="w-5 h-5 text-green-600" />
              <CardTitle className="text-lg text-green-900">Wallet Connected</CardTitle>
            </div>
            <Badge variant="default" className="bg-green-600">
              {currentConnection.provider}
            </Badge>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <div className="flex items-center justify-between text-sm">
              <span className="text-green-700">Address:</span>
              <div className="flex items-center gap-2">
                <span className="font-mono text-green-900">
                  {formatAccountId(currentConnection.address)}
                </span>
                <a
                  href={walletService.getAccountExplorerUrl(currentConnection.address)}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-green-600 hover:text-green-800"
                >
                  <ExternalLink className="w-3 h-3" />
                </a>
              </div>
            </div>
            <div className="flex items-center justify-between text-sm">
              <span className="text-green-700">Network:</span>
              <Badge variant="outline" className="text-green-700 border-green-300">
                {currentConnection.network}
              </Badge>
            </div>
          </div>

          <Button
            variant="outline"
            size="sm"
            onClick={handleDisconnect}
            className="w-full border-green-300 text-green-700 hover:bg-green-100"
          >
            Disconnect Wallet
          </Button>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Wallet className="w-5 h-5" />
          Connect Wallet
        </CardTitle>
        <p className="text-sm text-muted-foreground">
          Connect your wallet to make payments
        </p>
      </CardHeader>
      <CardContent className="space-y-3">
        {availableWallets.length === 0 ? (
          <div className="text-center py-6 space-y-3">
            <AlertCircle className="w-12 h-12 text-muted-foreground mx-auto" />
            <div>
              <p className="font-medium text-foreground">No Wallets Found</p>
              <p className="text-sm text-muted-foreground">
                Please install MetaMask or use WalletConnect for mobile
              </p>
            </div>
            <div className="space-y-2">
              <p className="text-xs text-muted-foreground">Supported wallets:</p>
              <div className="flex flex-wrap gap-2 justify-center">
                <Badge variant="outline">MetaMask</Badge>
                <Badge variant="outline">WalletConnect</Badge>
                <Badge variant="outline">Mobile Wallets</Badge>
              </div>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={refreshWallets}
              className="mt-4"
            >
              <RefreshCw className="w-4 h-4 mr-2" />
              Refresh Wallets
            </Button>
          </div>
        ) : (
          <div className="space-y-2">
            <AnimatePresence>
              {availableWallets.map((wallet) => (
                <motion.div
                  key={wallet.id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                >
                  <Button
                    variant="outline"
                    className="w-full justify-start h-auto p-4"
                    onClick={() => handleConnect(wallet)}
                    disabled={isConnecting}
                  >
                    <div className="flex items-center gap-3 w-full">
                      {wallet.icon && (
                        <img
                          src={wallet.icon}
                          alt={wallet.name}
                          className="w-6 h-6"
                          onError={(e) => {
                            // Fallback to wallet icon if image fails to load
                            (e.target as HTMLImageElement).style.display = 'none';
                          }}
                        />
                      )}
                      <Wallet className="w-5 h-5 text-muted-foreground" />
                      <div className="flex-1 text-left">
                        <p className="font-medium">{wallet.name}</p>
                        <p className="text-xs text-muted-foreground">
                          {wallet.isInstalled ? 'Ready to connect' : 'Not installed'}
                        </p>
                      </div>
                      {isConnecting && connectingWallet === wallet.id && (
                        <Loader2 className="w-4 h-4 animate-spin" />
                      )}
                    </div>
                  </Button>
                </motion.div>
              ))}
            </AnimatePresence>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

export default WalletConnect;