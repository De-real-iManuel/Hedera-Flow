/**
 * Consumption History Component
 * 
 * Displays smart meter consumption logs with analytics and verification status
 * Features:
 * - Real-time consumption data
 * - Signature verification status
 * - Consumption analytics and trends
 * - Token deduction tracking
 * - Blockchain verification links
 */

import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Separator } from '@/components/ui/separator';
import {
  Activity,
  TrendingUp,
  TrendingDown,
  Shield,
  CheckCircle,
  XCircle,
  ExternalLink,
  Calendar,
  Zap,
  AlertTriangle,
  Loader2,
  RefreshCw,
} from 'lucide-react';
import { toast } from 'sonner';
import { smartMeterApi } from '@/lib/api/smart-meter';
import type { ConsumptionLog, ConsumptionHistory } from '@/lib/api/smart-meter';
import { format, subDays, startOfDay, endOfDay } from 'date-fns';

export interface ConsumptionHistoryProps {
  meterId: string;
  refreshTrigger?: number; // Used to trigger refresh from parent
}

export function ConsumptionHistory({ meterId, refreshTrigger }: ConsumptionHistoryProps) {
  const [logs, setLogs] = useState<ConsumptionLog[]>([]);
  const [history, setHistory] = useState<ConsumptionHistory | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Filters
  const [dateFrom, setDateFrom] = useState(format(subDays(new Date(), 7), 'yyyy-MM-dd'));
  const [dateTo, setDateTo] = useState(format(new Date(), 'yyyy-MM-dd'));

  // Load consumption data
  const loadConsumptionData = async (showRefreshing = false) => {
    try {
      if (showRefreshing) {
        setRefreshing(true);
      } else {
        setLoading(true);
      }
      setError(null);

      // Load both logs and history analytics
      const [logsData, historyData] = await Promise.all([
        smartMeterApi.getConsumptionLogs(meterId, 50, 0),
        smartMeterApi.getConsumptionHistory(meterId, dateFrom, dateTo),
      ]);

      setLogs(logsData);
      setHistory(historyData);

    } catch (err) {
      console.error('Failed to load consumption data:', err);
      setError(err instanceof Error ? err.message : 'Failed to load consumption data');
      toast.error('Failed to load consumption data', {
        description: err instanceof Error ? err.message : 'Unknown error',
      });
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  // Initial load
  useEffect(() => {
    loadConsumptionData();
  }, [meterId, dateFrom, dateTo]);

  // Refresh when trigger changes
  useEffect(() => {
    if (refreshTrigger && refreshTrigger > 0) {
      loadConsumptionData(true);
    }
  }, [refreshTrigger]);

  // Manual refresh
  const handleRefresh = () => {
    loadConsumptionData(true);
  };

  // Apply date filters
  const applyFilters = () => {
    loadConsumptionData();
  };

  // Get verification status badge
  const getVerificationBadge = (log: ConsumptionLog) => {
    if (log.signature_valid) {
      return (
        <Badge className="bg-green-500 text-white gap-1">
          <CheckCircle className="w-3 h-3" />
          Verified
        </Badge>
      );
    } else {
      return (
        <Badge className="bg-red-500 text-white gap-1">
          <XCircle className="w-3 h-3" />
          Invalid
        </Badge>
      );
    }
  };

  // Format consumption value
  const formatConsumption = (kwh: number) => {
    return `${kwh.toFixed(3)} kWh`;
  };

  if (loading) {
    return (
      <Card>
        <CardContent className="py-12 text-center">
          <Loader2 className="w-8 h-8 animate-spin mx-auto mb-4 text-blue-600" />
          <p className="text-muted-foreground">Loading consumption history...</p>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card>
        <CardContent className="py-12 text-center">
          <AlertTriangle className="w-16 h-16 mx-auto mb-4 text-red-500" />
          <h3 className="text-lg font-semibold mb-2">Failed to Load Data</h3>
          <p className="text-muted-foreground mb-4">{error}</p>
          <Button onClick={() => loadConsumptionData()} variant="outline">
            <RefreshCw className="w-4 h-4 mr-2" />
            Try Again
          </Button>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Analytics Overview */}
      {history && (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>Consumption Analytics</CardTitle>
                <CardDescription>
                  Analysis for {format(new Date(dateFrom), 'MMM d')} - {format(new Date(dateTo), 'MMM d, yyyy')}
                </CardDescription>
              </div>
              <Button
                onClick={handleRefresh}
                variant="outline"
                size="sm"
                disabled={refreshing}
              >
                {refreshing ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <RefreshCw className="w-4 h-4" />
                )}
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="p-3 bg-blue-50 rounded-lg">
                <div className="flex items-center gap-2 mb-1">
                  <Activity className="w-4 h-4 text-blue-600" />
                  <span className="text-sm font-medium">Total Consumption</span>
                </div>
                <p className="text-2xl font-bold text-blue-900">
                  {history.total_consumption.toFixed(2)} kWh
                </p>
              </div>
              
              <div className="p-3 bg-green-50 rounded-lg">
                <div className="flex items-center gap-2 mb-1">
                  <TrendingUp className="w-4 h-4 text-green-600" />
                  <span className="text-sm font-medium">Daily Average</span>
                </div>
                <p className="text-2xl font-bold text-green-900">
                  {history.average_daily.toFixed(2)} kWh
                </p>
              </div>
              
              <div className="p-3 bg-orange-50 rounded-lg">
                <div className="flex items-center gap-2 mb-1">
                  <Zap className="w-4 h-4 text-orange-600" />
                  <span className="text-sm font-medium">Peak Usage</span>
                </div>
                <p className="text-2xl font-bold text-orange-900">
                  {history.peak_consumption.toFixed(3)} kWh
                </p>
              </div>
              
              <div className="p-3 bg-purple-50 rounded-lg">
                <div className="flex items-center gap-2 mb-1">
                  <TrendingDown className="w-4 h-4 text-purple-600" />
                  <span className="text-sm font-medium">Total Cost</span>
                </div>
                <p className="text-2xl font-bold text-purple-900">
                  ${history.total_cost.toFixed(2)}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Filters */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Calendar className="w-5 h-5" />
            Date Range Filter
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex gap-4 items-end">
            <div className="flex-1">
              <Label htmlFor="dateFrom">From Date</Label>
              <Input
                id="dateFrom"
                type="date"
                value={dateFrom}
                onChange={(e) => setDateFrom(e.target.value)}
              />
            </div>
            <div className="flex-1">
              <Label htmlFor="dateTo">To Date</Label>
              <Input
                id="dateTo"
                type="date"
                value={dateTo}
                onChange={(e) => setDateTo(e.target.value)}
              />
            </div>
            <Button onClick={applyFilters}>
              Apply Filter
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Consumption Logs */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Shield className="w-5 h-5" />
            Consumption Logs
          </CardTitle>
          <CardDescription>
            Cryptographically verified smart meter readings
          </CardDescription>
        </CardHeader>
        <CardContent>
          {logs.length === 0 ? (
            <div className="text-center py-12">
              <Activity className="w-16 h-16 mx-auto mb-4 text-muted-foreground" />
              <h3 className="text-lg font-semibold mb-2">No Consumption Logs</h3>
              <p className="text-muted-foreground">
                Start the smart meter simulator to generate consumption data
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              {logs.map((log) => (
                <Card key={log.id} className="hover:shadow-md transition-shadow">
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-2">
                          <div className="p-2 bg-blue-100 rounded-lg">
                            <Zap className="w-4 h-4 text-blue-600" />
                          </div>
                          <div>
                            <p className="font-semibold">
                              {formatConsumption(log.consumption_kwh)}
                            </p>
                            <p className="text-sm text-muted-foreground">
                              {format(new Date(log.timestamp), 'PPP p')}
                            </p>
                          </div>
                          {getVerificationBadge(log)}
                        </div>
                        
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                          <div>
                            <p className="text-muted-foreground">Reading Before</p>
                            <p className="font-semibold">{log.reading_before.toFixed(3)} kWh</p>
                          </div>
                          <div>
                            <p className="text-muted-foreground">Reading After</p>
                            <p className="font-semibold">{log.reading_after.toFixed(3)} kWh</p>
                          </div>
                          {log.units_deducted && (
                            <div>
                              <p className="text-muted-foreground">Units Deducted</p>
                              <p className="font-semibold text-red-600">
                                -{log.units_deducted.toFixed(3)} kWh
                              </p>
                            </div>
                          )}
                          {log.units_remaining !== undefined && (
                            <div>
                              <p className="text-muted-foreground">Units Remaining</p>
                              <p className="font-semibold text-green-600">
                                {log.units_remaining.toFixed(3)} kWh
                              </p>
                            </div>
                          )}
                        </div>
                      </div>
                      
                      <div className="flex flex-col gap-2 ml-4">
                        {log.hcs_sequence_number && (
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => {
                              // In a real implementation, this would link to Hedera Mirror Node
                              toast.info('Blockchain verification', {
                                description: `HCS Sequence: ${log.hcs_sequence_number}`,
                              });
                            }}
                          >
                            <ExternalLink className="w-3 h-3 mr-1" />
                            HCS
                          </Button>
                        )}
                        
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => {
                            navigator.clipboard.writeText(log.signature);
                            toast.success('Signature copied to clipboard');
                          }}
                        >
                          <Shield className="w-3 h-3 mr-1" />
                          Signature
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}