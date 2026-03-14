/**
 * Transaction History Component
 * 
 * Displays paginated list of prepaid token transactions with filtering
 * Features:
 * - Status filtering (all, active, depleted, expired)
 * - Date range filtering
 * - Pagination
 * - Receipt viewing and downloading
 * - Transaction details modal
 */

import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Separator } from '@/components/ui/separator';
import {
  History,
  Filter,
  Download,
  Mail,
  ExternalLink,
  Calendar,
  Zap,
  Clock,
  AlertCircle,
  Loader2,
  Receipt,
  Eye,
  ChevronLeft,
  ChevronRight,
  Printer,
} from 'lucide-react';
import { toast } from 'sonner';
import { prepaidApi } from '@/lib/api/prepaid';
import type { PrepaidToken } from '@/lib/api/prepaid';
import { ReceiptPrint } from '@/components/ReceiptPrint';
import { format } from 'date-fns';

export interface TransactionHistoryProps {
  meterId?: string;
  showFilters?: boolean;
  pageSize?: number;
}

export function TransactionHistory({
  meterId,
  showFilters = true,
  pageSize = 20,
}: TransactionHistoryProps) {
  const [transactions, setTransactions] = useState<PrepaidToken[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Filters
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [dateFromFilter, setDateFromFilter] = useState<string>('');
  const [dateToFilter, setDateToFilter] = useState<string>('');
  
  // Pagination
  const [currentPage, setCurrentPage] = useState(1);
  const [totalTransactions, setTotalTransactions] = useState(0);
  const [hasMore, setHasMore] = useState(false);

  // Load transactions
  const loadTransactions = async (page: number = 1, append: boolean = false) => {
    try {
      setLoading(true);
      setError(null);
      
      const offset = (page - 1) * pageSize;
      const params = {
        meterId,
        status: statusFilter === 'all' ? undefined : statusFilter,
        dateFrom: dateFromFilter || undefined,
        dateTo: dateToFilter || undefined,
        limit: pageSize,
        offset,
      };
      
      const data = await prepaidApi.listTokens(params);
      
      if (append) {
        setTransactions(prev => [...prev, ...data]);
      } else {
        setTransactions(data);
      }
      
      setHasMore(data.length === pageSize);
      setTotalTransactions(prev => append ? prev + data.length : data.length);
      
    } catch (err) {
      console.error('Failed to load transactions:', err);
      setError(err instanceof Error ? err.message : 'Failed to load transactions');
    } finally {
      setLoading(false);
    }
  };

  // Load more transactions (pagination)
  const loadMore = () => {
    const nextPage = currentPage + 1;
    setCurrentPage(nextPage);
    loadTransactions(nextPage, true);
  };

  // Apply filters
  const applyFilters = () => {
    setCurrentPage(1);
    setTransactions([]);
    loadTransactions(1, false);
  };

  // Clear filters
  const clearFilters = () => {
    setStatusFilter('all');
    setDateFromFilter('');
    setDateToFilter('');
    setCurrentPage(1);
    setTransactions([]);
    loadTransactions(1, false);
  };

  // Download receipt
  const downloadReceipt = async (transaction: PrepaidToken, format: 'html' | 'text' = 'html') => {
    try {
      const receipt = await prepaidApi.getReceipt(transaction.token_id, format);
      
      const blob = new Blob([receipt as string], {
        type: format === 'html' ? 'text/html' : 'text/plain',
      });
      
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `receipt-${transaction.token_id}.${format}`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      
      toast.success('Receipt downloaded successfully');
      
    } catch (err) {
      console.error('Failed to download receipt:', err);
      toast.error('Failed to download receipt', {
        description: err instanceof Error ? err.message : 'Unknown error',
      });
    }
  };

  // Get status color
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'bg-green-500 text-white';
      case 'low': return 'bg-yellow-500 text-white';
      case 'depleted': return 'bg-red-500 text-white';
      case 'expired': return 'bg-gray-500 text-white';
      case 'cancelled': return 'bg-gray-400 text-white';
      default: return 'bg-gray-500 text-white';
    }
  };

  // Format currency
  const formatCurrency = (amount: number, currency: string) => {
    const symbols: Record<string, string> = {
      EUR: '€',
      USD: '$',
      INR: '₹',
      BRL: 'R$',
      NGN: '₦',
    };
    const symbol = symbols[currency] || currency;
    return `${symbol}${amount.toLocaleString(undefined, {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    })}`;
  };

  // Initial load
  useEffect(() => {
    loadTransactions();
  }, [meterId]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-blue-100 rounded-lg">
            <History className="w-6 h-6 text-blue-600" />
          </div>
          <div>
            <h2 className="text-2xl font-bold text-gray-900">Transaction History</h2>
            <p className="text-muted-foreground">
              {totalTransactions} transaction{totalTransactions !== 1 ? 's' : ''} found
            </p>
          </div>
        </div>
      </div>

      {/* Filters */}
      {showFilters && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Filter className="w-5 h-5" />
              Filters
            </CardTitle>
            <CardDescription>
              Filter transactions by status and date range
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              {/* Status Filter */}
              <div className="space-y-2">
                <Label htmlFor="status">Status</Label>
                <Select value={statusFilter} onValueChange={setStatusFilter}>
                  <SelectTrigger>
                    <SelectValue placeholder="All statuses" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Statuses</SelectItem>
                    <SelectItem value="active">Active</SelectItem>
                    <SelectItem value="low">Low Balance</SelectItem>
                    <SelectItem value="depleted">Depleted</SelectItem>
                    <SelectItem value="expired">Expired</SelectItem>
                    <SelectItem value="cancelled">Cancelled</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              {/* Date From */}
              <div className="space-y-2">
                <Label htmlFor="dateFrom">From Date</Label>
                <Input
                  id="dateFrom"
                  type="date"
                  value={dateFromFilter}
                  onChange={(e) => setDateFromFilter(e.target.value)}
                />
              </div>

              {/* Date To */}
              <div className="space-y-2">
                <Label htmlFor="dateTo">To Date</Label>
                <Input
                  id="dateTo"
                  type="date"
                  value={dateToFilter}
                  onChange={(e) => setDateToFilter(e.target.value)}
                />
              </div>

              {/* Filter Actions */}
              <div className="space-y-2">
                <Label>&nbsp;</Label>
                <div className="flex gap-2">
                  <Button onClick={applyFilters} size="sm">
                    Apply
                  </Button>
                  <Button onClick={clearFilters} variant="outline" size="sm">
                    Clear
                  </Button>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Error State */}
      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Loading State */}
      {loading && transactions.length === 0 && (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
          <span className="ml-3 text-muted-foreground">Loading transactions...</span>
        </div>
      )}

      {/* Empty State */}
      {!loading && transactions.length === 0 && !error && (
        <Card>
          <CardContent className="py-12 text-center">
            <History className="w-16 h-16 mx-auto mb-4 text-muted-foreground" />
            <h3 className="text-xl font-semibold mb-2">No Transactions Found</h3>
            <p className="text-muted-foreground mb-6">
              {statusFilter !== 'all' || dateFromFilter || dateToFilter
                ? 'No transactions match your current filters.'
                : 'You haven\'t made any token purchases yet.'}
            </p>
            {statusFilter !== 'all' || dateFromFilter || dateToFilter ? (
              <Button onClick={clearFilters} variant="outline">
                Clear Filters
              </Button>
            ) : null}
          </CardContent>
        </Card>
      )}

      {/* Transaction List */}
      {transactions.length > 0 && (
        <div className="space-y-4">
          {transactions.map((transaction) => (
            <Card key={transaction.id} className="hover:shadow-md transition-shadow">
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  {/* Transaction Info */}
                  <div className="flex-1 space-y-2">
                    <div className="flex items-center gap-3">
                      <div className="p-2 bg-purple-100 rounded-lg">
                        <Zap className="w-5 h-5 text-purple-600" />
                      </div>
                      <div>
                        <h3 className="font-semibold text-lg">
                          {transaction.token_id}
                        </h3>
                        {transaction.sts_token && (
                          <p className="text-sm font-mono text-blue-600 bg-blue-50 px-2 py-1 rounded mt-1 inline-block">
                            STS: {transaction.sts_token}
                          </p>
                        )}
                        <p className="text-sm text-muted-foreground mt-1">
                          {transaction.issued_at ? (() => {
                            try {
                              const date = new Date(transaction.issued_at);
                              return isNaN(date.getTime()) ? 'Date unavailable' : format(date, 'PPP p');
                            } catch {
                              return 'Date unavailable';
                            }
                          })() : 'Date unavailable'}
                        </p>
                      </div>
                      <Badge className={getStatusColor(transaction.status)}>
                        {transaction.status}
                      </Badge>
                    </div>

                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                      <div>
                        <p className="text-muted-foreground">Amount Paid</p>
                        <p className="font-semibold">
                          {formatCurrency(transaction.amount_paid_fiat, transaction.currency)}
                        </p>
                        {transaction.amount_paid_hbar && (
                          <p className="text-xs text-muted-foreground">
                            {transaction.amount_paid_hbar.toFixed(6)} ℏ
                          </p>
                        )}
                      </div>
                      <div>
                        <p className="text-muted-foreground">Units</p>
                        <p className="font-semibold">
                          {transaction.units_remaining.toFixed(2)} / {transaction.units_purchased.toFixed(2)} kWh
                        </p>
                        <p className="text-xs text-muted-foreground">
                          Remaining / Purchased
                        </p>
                      </div>
                      <div>
                        <p className="text-muted-foreground">Expires</p>
                        <p className="font-semibold">
                          {(() => {
                            try {
                              const date = new Date(transaction.expires_at);
                              return isNaN(date.getTime()) ? 'Invalid date' : format(date, 'PP');
                            } catch {
                              return 'Invalid date';
                            }
                          })()}
                        </p>
                      </div>
                      <div>
                        <p className="text-muted-foreground">Transaction</p>
                        {transaction.hedera_tx_id ? (
                          <Button
                            variant="link"
                            size="sm"
                            className="p-0 h-auto text-blue-600"
                            onClick={() => window.open(
                              `https://hashscan.io/testnet/transaction/${transaction.hedera_tx_id}`,
                              '_blank'
                            )}
                          >
                            <ExternalLink className="w-3 h-3 mr-1" />
                            View on HashScan
                          </Button>
                        ) : (
                          <p className="text-sm text-muted-foreground">Pending</p>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="flex items-center gap-2 ml-4">
                    {/* Print Receipt */}
                    <ReceiptPrint 
                      transaction={transaction}
                      trigger={
                        <Button variant="outline" size="sm">
                          <Printer className="w-4 h-4 mr-1" />
                          Receipt
                        </Button>
                      }
                    />

                    {/* Quick Download */}
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => downloadReceipt(transaction)}
                    >
                      <Download className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}

          {/* Load More */}
          {hasMore && (
            <div className="flex justify-center pt-4">
              <Button
                onClick={loadMore}
                variant="outline"
                disabled={loading}
              >
                {loading ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Loading...
                  </>
                ) : (
                  <>
                    <ChevronRight className="w-4 h-4 mr-2" />
                    Load More
                  </>
                )}
              </Button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}