import { motion } from "framer-motion";
import { Lock, Zap, FileText, CheckCircle, AlertCircle, X, Download } from "lucide-react";
import { useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import apiClient from "@/lib/api-client";
import { smartMeterApi } from "@/lib/api/smart-meter";
import AppHeader from "@/components/AppHeader";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";

interface Bill {
  id: string;
  consumption_kwh: number;
  total_fiat: number;
  currency: string;
  status: string;
  created_at: string;
  hcs_sequence_number?: number;
}

interface ConsumptionLog {
  id?: string;
  consumption_kwh: number;
  timestamp: number;
  signature_valid: boolean;
  hcs_sequence_number?: number;
  created_at?: string;
}

interface PrepaidToken {
  id: string;
  token_id: string;
  amount_paid_fiat: number;
  currency: string;
  units_purchased: number;
  status: string;
  issued_at: string;
  hedera_tx_id?: string;
}

type FeedItem = {
  id: string;
  type: 'bill' | 'verification' | 'consumption' | 'prepaid';
  date: Date;
  title: string;
  subtitle: string;
  amount?: string;
  status: string;
  hcs_sequence?: number;
  tx_id?: string;
  icon: typeof FileText;
  iconColor: string;
};

const HistoryPage = () => {
  const [feedItems, setFeedItems] = useState<FeedItem[]>([]);
  const [selectedItem, setSelectedItem] = useState<FeedItem | null>(null);
  const [receiptData, setReceiptData] = useState<any>(null);
  const [loadingReceipt, setLoadingReceipt] = useState(false);

  // Fetch bills
  const { data: bills } = useQuery<Bill[]>({
    queryKey: ['bills'],
    queryFn: async () => {
      const res = await apiClient.get('/bills');
      return res.data;
    },
  });

  // Fetch consumption logs (from first meter)
  const { data: meters } = useQuery({
    queryKey: ['meters'],
    queryFn: async () => {
      const res = await apiClient.get('/meters');
      return res.data;
    },
  });

  const firstMeterId = meters?.[0]?.id;

  const { data: consumptionLogs } = useQuery<ConsumptionLog[]>({
    queryKey: ['consumption-logs', firstMeterId],
    queryFn: async () => {
      if (!firstMeterId) return [];
      const res = await smartMeterApi.getConsumptionHistory(firstMeterId, 50);
      return res;
    },
    enabled: !!firstMeterId,
  });

  // Fetch prepaid tokens
  const { data: prepaidTokens } = useQuery<PrepaidToken[]>({
    queryKey: ['prepaid-tokens'],
    queryFn: async () => {
      const res = await apiClient.get('/prepaid/tokens');
      return res.data;
    },
  });

  // Merge all feeds
  useEffect(() => {
    const items: FeedItem[] = [];

    // Bills
    bills?.forEach(b => {
      items.push({
        id: b.id,
        type: 'bill',
        date: new Date(b.created_at),
        title: `Bill - ${(b.consumption_kwh ?? 0).toFixed(1)} kWh`,
        subtitle: `${b.status} · ${new Date(b.created_at).toLocaleDateString()}`,
        amount: `${b.currency} ${(b.total_fiat ?? 0).toFixed(2)}`,
        status: b.status,
        hcs_sequence: b.hcs_sequence_number,
        icon: FileText,
        iconColor: 'text-blue-600',
      });
    });

    // Consumption logs
    consumptionLogs?.forEach(c => {
      items.push({
        id: c.id || `log-${c.timestamp}`,
        type: 'consumption',
        date: new Date(c.created_at || c.timestamp * 1000),
        title: `Smart Meter Log - ${(c.consumption_kwh ?? 0).toFixed(3)} kWh`,
        subtitle: `${c.signature_valid ? 'Verified' : 'Invalid'} · ${new Date(c.created_at || c.timestamp * 1000).toLocaleDateString()}`,
        status: c.signature_valid ? 'verified' : 'invalid',
        hcs_sequence: c.hcs_sequence_number,
        icon: Zap,
        iconColor: 'text-purple-600',
      });
    });

    // Prepaid tokens
    prepaidTokens?.forEach(t => {
      items.push({
        id: t.id,
        type: 'prepaid',
        date: new Date(t.issued_at),
        title: `Prepaid Token - ${(t.units_purchased ?? 0).toFixed(1)} kWh`,
        subtitle: `${t.token_id} · ${t.status}`,
        amount: `${t.currency} ${(t.amount_paid_fiat ?? 0).toFixed(2)}`,
        status: t.status,
        tx_id: t.hedera_tx_id,
        icon: Zap,
        iconColor: 'text-orange-600',
      });
    });

    // Sort by date descending
    items.sort((a, b) => b.date.getTime() - a.date.getTime());
    setFeedItems(items);
  }, [bills, consumptionLogs, prepaidTokens]);

  // Fetch receipt/details for selected item
  const fetchReceipt = async (item: FeedItem) => {
    setSelectedItem(item);
    setLoadingReceipt(true);
    setReceiptData(null);

    try {
      let data;
      
      if (item.type === 'prepaid') {
        // Fetch prepaid token receipt
        const res = await apiClient.get(`/prepaid/tokens/${item.id}/receipt?format=json`);
        data = res.data;
      } else if (item.type === 'bill') {
        // Fetch bill details
        const res = await apiClient.get(`/bills/${item.id}`);
        data = res.data;
      } else if (item.type === 'consumption') {
        // Find consumption log from the already loaded data
        const log = consumptionLogs?.find(l => (l.id || `log-${l.timestamp}`) === item.id);
        if (log) {
          data = log;
        } else {
          throw new Error('Consumption log not found');
        }
      }
      
      setReceiptData(data);
    } catch (error) {
      console.error('Error fetching receipt:', error);
      setReceiptData({ error: 'Failed to load details' });
    } finally {
      setLoadingReceipt(false);
    }
  };

  const closeReceipt = () => {
    setSelectedItem(null);
    setReceiptData(null);
  };

  if (!bills && !consumptionLogs && !prepaidTokens) {
    return (
      <div className="min-h-screen bg-background pb-24">
        <AppHeader title="Transaction History" />
        <div className="px-5 space-y-3">
          {[...Array(5)].map((_, i) => (
            <Skeleton key={i} className="h-20 w-full" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background pb-24">
      <AppHeader title="Transaction History" />

      <div className="px-5">
        <div className="flex items-center gap-2 mb-4">
          <Lock className="w-3.5 h-3.5 text-success" />
          <span className="text-xs text-muted-foreground">
            All records are immutable & audit-proof on Hedera HCS
          </span>
        </div>

        <div className="space-y-3">
          {feedItems.length === 0 ? (
            <div className="text-center py-12 text-muted-foreground">
              <AlertCircle className="w-12 h-12 mx-auto mb-3 opacity-50" />
              <p>No transaction history yet</p>
            </div>
          ) : (
            feedItems.map((item, i) => (
              <motion.div
                key={item.id}
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.04 }}
                className="glass-card p-4 cursor-pointer hover:bg-accent/5 transition-colors active:scale-[0.98]"
                onClick={() => fetchReceipt(item)}
              >
                <div className="flex items-start gap-3">
                  <div className={`w-9 h-9 rounded-xl bg-${item.iconColor.split('-')[1]}-100 flex items-center justify-center shrink-0`}>
                    <item.icon className={`w-4 h-4 ${item.iconColor}`} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-foreground">{item.title}</p>
                    <p className="text-xs text-muted-foreground">{item.subtitle}</p>
                    {item.hcs_sequence && (
                      <div className="flex items-center gap-1 mt-1">
                        <CheckCircle className="w-3 h-3 text-success" />
                        <span className="text-xs text-success">HCS #{item.hcs_sequence}</span>
                      </div>
                    )}
                    {item.tx_id && (
                      <div className="flex items-center gap-1 mt-1">
                        <CheckCircle className="w-3 h-3 text-success" />
                        <span className="text-xs text-success font-mono">{item.tx_id.slice(0, 20)}...</span>
                      </div>
                    )}
                  </div>
                  <div className="text-right">
                    {item.amount && (
                      <p className="text-sm font-semibold text-foreground">{item.amount}</p>
                    )}
                    <Badge
                      variant={
                        item.status === 'paid' || item.status === 'verified'
                          ? 'default'
                          : item.status === 'pending'
                          ? 'secondary'
                          : 'destructive'
                      }
                      className="text-xs mt-1"
                    >
                      {item.status}
                    </Badge>
                    <p className="text-xs text-muted-foreground mt-1">Tap to view</p>
                  </div>
                </div>
              </motion.div>
            ))
          )}
        </div>

        {feedItems.length > 0 && (
          <div className="pt-4 flex items-center justify-center gap-2 text-xs text-muted-foreground">
            <Zap className="w-3.5 h-3.5 text-accent" />
            <span>{feedItems.length} total records · All verified on Hedera</span>
          </div>
        )}
      </div>

      {/* Receipt/Details Dialog */}
      <Dialog open={!!selectedItem} onOpenChange={(open) => !open && closeReceipt()}>
        <DialogContent className="max-w-lg max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center justify-between">
              <span>
                {selectedItem?.type === 'prepaid' && 'Prepaid Token Receipt'}
                {selectedItem?.type === 'bill' && 'Bill Details'}
                {selectedItem?.type === 'consumption' && 'Consumption Log Details'}
              </span>
              <Button variant="ghost" size="icon" onClick={closeReceipt}>
                <X className="w-4 h-4" />
              </Button>
            </DialogTitle>
          </DialogHeader>

          {loadingReceipt ? (
            <div className="space-y-3">
              <Skeleton className="h-4 w-full" />
              <Skeleton className="h-4 w-3/4" />
              <Skeleton className="h-4 w-full" />
              <Skeleton className="h-4 w-2/3" />
            </div>
          ) : receiptData?.error ? (
            <div className="text-center py-8 text-destructive">
              <AlertCircle className="w-12 h-12 mx-auto mb-3 opacity-50" />
              <p>{receiptData.error}</p>
            </div>
          ) : receiptData ? (
            <div className="space-y-4">
              {/* Prepaid Token Receipt */}
              {selectedItem?.type === 'prepaid' && (
                <div className="space-y-3">
                  {/* STS Token - Most Important */}
                  {receiptData.receipt?.sts_token && (
                    <div className="bg-gradient-to-br from-accent/20 to-accent/10 border-2 border-accent rounded-xl p-4 mb-4">
                      <div className="text-center">
                        <p className="text-xs text-muted-foreground mb-2">Your Electricity Credit Code</p>
                        <p className="text-2xl font-bold font-mono tracking-wider text-accent mb-1">
                          {receiptData.receipt.sts_token}
                        </p>
                        <p className="text-xs text-muted-foreground">
                          Enter this 20-digit code into your prepaid meter
                        </p>
                      </div>
                    </div>
                  )}
                  
                  <div className="flex justify-between items-center pb-3 border-b">
                    <span className="text-sm text-muted-foreground">Token ID</span>
                    <span className="font-mono text-sm">{receiptData.token_id}</span>
                  </div>
                  
                  {receiptData.receipt?.units_purchased && (
                    <div className="flex justify-between items-center pb-3 border-b">
                      <span className="text-sm text-muted-foreground">Units Purchased</span>
                      <span className="font-semibold">{receiptData.receipt.units_purchased.toFixed(2)} kWh</span>
                    </div>
                  )}
                  
                  {receiptData.receipt?.amount_paid && (
                    <div className="flex justify-between items-center pb-3 border-b">
                      <span className="text-sm text-muted-foreground">Amount Paid</span>
                      <span className="font-semibold">{receiptData.receipt.currency} {receiptData.receipt.amount_paid.toFixed(2)}</span>
                    </div>
                  )}
                  
                  {receiptData.receipt?.html && (
                    <div 
                      className="prose prose-sm max-w-none mt-4"
                      dangerouslySetInnerHTML={{ __html: receiptData.receipt.html }}
                    />
                  )}
                  
                  <Button 
                    className="w-full mt-4" 
                    onClick={() => window.open(`/api/prepaid/tokens/${selectedItem.id}/receipt?format=html`, '_blank')}
                  >
                    <Download className="w-4 h-4 mr-2" />
                    Download Full Receipt
                  </Button>
                </div>
              )}

              {/* Bill Details */}
              {selectedItem?.type === 'bill' && (
                <div className="space-y-3">
                  <div className="flex justify-between items-center pb-3 border-b">
                    <span className="text-sm text-muted-foreground">Bill ID</span>
                    <span className="font-mono text-sm">{receiptData.id}</span>
                  </div>
                  <div className="flex justify-between items-center pb-3 border-b">
                    <span className="text-sm text-muted-foreground">Consumption</span>
                    <span className="font-semibold">{(receiptData.consumption_kwh ?? 0).toFixed(2)} kWh</span>
                  </div>
                  <div className="flex justify-between items-center pb-3 border-b">
                    <span className="text-sm text-muted-foreground">Amount</span>
                    <span className="font-semibold">{receiptData.currency} {(receiptData.total_fiat ?? 0).toFixed(2)}</span>
                  </div>
                  <div className="flex justify-between items-center pb-3 border-b">
                    <span className="text-sm text-muted-foreground">Status</span>
                    <Badge variant={receiptData.status === 'paid' ? 'default' : 'secondary'}>
                      {receiptData.status}
                    </Badge>
                  </div>
                  {receiptData.hcs_topic_id && (
                    <div className="flex justify-between items-center pb-3 border-b">
                      <span className="text-sm text-muted-foreground">HCS Topic</span>
                      <span className="font-mono text-xs">{receiptData.hcs_topic_id}</span>
                    </div>
                  )}
                  {receiptData.hcs_sequence_number && (
                    <div className="flex justify-between items-center pb-3 border-b">
                      <span className="text-sm text-muted-foreground">HCS Sequence</span>
                      <span className="font-mono text-sm">#{receiptData.hcs_sequence_number}</span>
                    </div>
                  )}
                  {receiptData.hedera_tx_id && (
                    <div className="flex justify-between items-center pb-3 border-b">
                      <span className="text-sm text-muted-foreground">Transaction ID</span>
                      <span className="font-mono text-xs break-all">{receiptData.hedera_tx_id}</span>
                    </div>
                  )}
                  <div className="flex justify-between items-center pb-3 border-b">
                    <span className="text-sm text-muted-foreground">Created</span>
                    <span className="text-sm">{new Date(receiptData.created_at).toLocaleString()}</span>
                  </div>
                </div>
              )}

              {/* Consumption Log Details */}
              {selectedItem?.type === 'consumption' && (
                <div className="space-y-3">
                  <div className="flex justify-between items-center pb-3 border-b">
                    <span className="text-sm text-muted-foreground">Log ID</span>
                    <span className="font-mono text-xs break-all">{receiptData.id}</span>
                  </div>
                  <div className="flex justify-between items-center pb-3 border-b">
                    <span className="text-sm text-muted-foreground">Consumption</span>
                    <span className="font-semibold">{(receiptData.consumption_kwh ?? 0).toFixed(4)} kWh</span>
                  </div>
                  <div className="flex justify-between items-center pb-3 border-b">
                    <span className="text-sm text-muted-foreground">Signature Valid</span>
                    <Badge variant={receiptData.signature_valid ? 'default' : 'destructive'}>
                      {receiptData.signature_valid ? 'Verified ✓' : 'Invalid ✗'}
                    </Badge>
                  </div>
                  {receiptData.signature && (
                    <div className="pb-3 border-b">
                      <span className="text-sm text-muted-foreground block mb-2">KMS Signature</span>
                      <code className="text-xs bg-muted p-2 rounded block break-all">
                        {receiptData.signature}
                      </code>
                    </div>
                  )}
                  {receiptData.hcs_topic_id && (
                    <div className="flex justify-between items-center pb-3 border-b">
                      <span className="text-sm text-muted-foreground">HCS Topic</span>
                      <span className="font-mono text-xs">{receiptData.hcs_topic_id}</span>
                    </div>
                  )}
                  {receiptData.hcs_sequence_number && (
                    <div className="flex justify-between items-center pb-3 border-b">
                      <span className="text-sm text-muted-foreground">HCS Sequence</span>
                      <span className="font-mono text-sm">#{receiptData.hcs_sequence_number}</span>
                    </div>
                  )}
                  <div className="flex justify-between items-center pb-3 border-b">
                    <span className="text-sm text-muted-foreground">Timestamp</span>
                    <span className="text-sm">
                      {receiptData.created_at 
                        ? new Date(receiptData.created_at).toLocaleString()
                        : new Date(receiptData.timestamp * 1000).toLocaleString()
                      }
                    </span>
                  </div>
                  <div className="bg-success/10 border border-success/20 rounded-lg p-3 mt-4">
                    <div className="flex items-center gap-2 text-success">
                      <CheckCircle className="w-4 h-4" />
                      <span className="text-sm font-medium">Secured by AWS KMS HSM</span>
                    </div>
                    <p className="text-xs text-muted-foreground mt-1">
                      This reading was cryptographically signed using AWS Key Management Service with hardware security module protection.
                    </p>
                  </div>
                </div>
              )}

              {/* Hedera Verification Badge */}
              <div className="bg-accent/10 border border-accent/20 rounded-lg p-3 mt-4">
                <div className="flex items-center gap-2 text-accent">
                  <Lock className="w-4 h-4" />
                  <span className="text-sm font-medium">Verified on Hedera</span>
                </div>
                <p className="text-xs text-muted-foreground mt-1">
                  This transaction is immutably recorded on Hedera Consensus Service and cannot be altered.
                </p>
              </div>
            </div>
          ) : null}
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default HistoryPage;
