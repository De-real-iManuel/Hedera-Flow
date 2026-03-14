/**
 * Consumption History List Component
 * 
 * Displays a list of historical consumption logs with signature verification status.
 * Features:
 * - Chronological list of consumption events
 * - Signature verification badges
 * - Token deduction information
 * - Refresh functionality
 * - Click to view details
 * 
 * Requirements: US-17, Task 2.7
 */

import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
import {
  History,
  RefreshCw,
  Zap,
  Clock,
  CheckCircle,
  XCircle,
  Loader2,
  AlertCircle,
} from 'lucide-react';
import { toast } from 'sonner';
import { ConsumptionLog } from './SmartMeterVerification';

interface ConsumptionHistoryListProps {
  meterId: string;
  onSelectLog?: (log: ConsumptionLog) => void;
  limit?: number;
}

export function ConsumptionHistoryList({
  meterId,
  onSelectLog,
  limit = 50,
}: ConsumptionHistoryListProps) {
  const [logs, setLogs] = useState<ConsumptionLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchConsumptionLogs = async (isRefresh = false) => {
    if (isRefresh) {
      setRefreshing(true);
    } else {
      setLoading(true);
    }
    setError(null);

    try {
      const response = await fetch(
        `/api/smart-meter/consumption-logs?meter_id=${meterId}&limit=${limit}`,
        {
          headers: {
            'Content-Type': 'application/json',
          },
        }
      );

      if (!response.ok) {
        throw new Error('Failed to fetch consumption logs');
      }

      const data = await response.json();
      setLogs(data.logs || []);

      if (isRefresh) {
        toast.success('History Refreshed', {
          description: `Loaded ${data.logs?.length || 0} consumption events`,
          duration: 2000,
        });
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load consumption history';
      setError(errorMessage);
      toast.error('Error Loading History', {
        description: errorMessage,
        duration: 4000,
      });
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    if (meterId) {
      fetchConsumptionLogs();
    }
  }, [meterId, limit]);

  const handleRefresh = () => {
    fetchConsumptionLogs(true);
  };

  const handleLogClick = (log: ConsumptionLog) => {
    if (onSelectLog) {
      onSelectLog(log);
    }
  };

  const formatTimestamp = (timestamp: number) => {
    return new Date(timestamp * 1000).toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const formatDate = (timestamp: number) => {
    return new Date(timestamp * 1000).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });
  };

  if (loading) {
    return (
      <Card className="w-full">
        <CardHeader>
          <div className="flex items-center gap-3">
            <History className="w-5 h-5 text-muted-foreground" />
            <CardTitle>Consumption History</CardTitle>
          </div>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center py-12">
            <Loader2 className="w-8 h-8 animate-spin text-muted-foreground" />
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className="w-full">
        <CardHeader>
          <div className="flex items-center gap-3">
            <History className="w-5 h-5 text-muted-foreground" />
            <CardTitle>Consumption History</CardTitle>
          </div>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col items-center justify-center py-12 gap-4">
            <AlertCircle className="w-12 h-12 text-red-500" />
            <p className="text-sm text-muted-foreground text-center">{error}</p>
            <Button onClick={handleRefresh} variant="outline" size="sm">
              <RefreshCw className="w-4 h-4 mr-2" />
              Try Again
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="w-full">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-blue-50 rounded-lg">
              <History className="w-5 h-5 text-blue-600" />
            </div>
            <div>
              <CardTitle>Consumption History</CardTitle>
              <CardDescription>
                {logs.length} consumption event{logs.length !== 1 ? 's' : ''} recorded
              </CardDescription>
            </div>
          </div>
          <Button
            onClick={handleRefresh}
            disabled={refreshing}
            variant="outline"
            size="sm"
          >
            <RefreshCw className={`w-4 h-4 mr-2 ${refreshing ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>
      </CardHeader>

      <CardContent>
        {logs.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-12 gap-3">
            <History className="w-12 h-12 text-muted-foreground opacity-50" />
            <p className="text-sm text-muted-foreground text-center">
              No consumption events recorded yet
            </p>
            <p className="text-xs text-muted-foreground text-center max-w-md">
              Consumption events will appear here once your smart meter logs electricity usage
            </p>
          </div>
        ) : (
          <ScrollArea className="h-[600px] pr-4">
            <div className="space-y-3">
              {logs.map((log, index) => {
                const isVerified = log.signature_valid;
                const showDateHeader =
                  index === 0 ||
                  formatDate(log.timestamp) !== formatDate(logs[index - 1].timestamp);

                return (
                  <div key={log.id}>
                    {showDateHeader && (
                      <div className="sticky top-0 bg-background py-2 z-10">
                        <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                          {formatDate(log.timestamp)}
                        </p>
                      </div>
                    )}

                    <div
                      onClick={() => handleLogClick(log)}
                      className={`
                        border rounded-lg p-4 cursor-pointer transition-all
                        hover:shadow-md hover:border-primary
                        ${isVerified ? 'border-green-200 bg-green-50/30' : 'border-red-200 bg-red-50/30'}
                      `}
                    >
                      <div className="flex items-start justify-between gap-3">
                        <div className="flex-1 space-y-2">
                          {/* Header */}
                          <div className="flex items-center justify-between">
                            <div className="flex items-center gap-2">
                              <Zap className="w-4 h-4 text-purple-600" />
                              <span className="font-bold text-lg">
                                {log.consumption_kwh.toFixed(2)} kWh
                              </span>
                            </div>
                            <Badge
                              variant={isVerified ? 'default' : 'destructive'}
                              className="text-xs"
                            >
                              {isVerified ? (
                                <>
                                  <CheckCircle className="w-3 h-3 mr-1" />
                                  Verified
                                </>
                              ) : (
                                <>
                                  <XCircle className="w-3 h-3 mr-1" />
                                  Invalid
                                </>
                              )}
                            </Badge>
                          </div>

                          {/* Timestamp */}
                          <div className="flex items-center gap-2 text-sm text-muted-foreground">
                            <Clock className="w-3 h-3" />
                            <span>{formatTimestamp(log.timestamp)}</span>
                          </div>

                          {/* Readings */}
                          <div className="flex items-center gap-4 text-xs text-muted-foreground">
                            <span>
                              Before: {log.reading_before?.toFixed(2) || 'N/A'} kWh
                            </span>
                            <span>→</span>
                            <span>
                              After: {log.reading_after?.toFixed(2) || 'N/A'} kWh
                            </span>
                          </div>

                          {/* Token Information */}
                          {log.token_id && (
                            <div className="pt-2 border-t border-gray-200">
                              <div className="flex items-center justify-between text-xs">
                                <span className="text-muted-foreground">Token:</span>
                                <span className="font-mono">{log.token_id}</span>
                              </div>
                              {log.units_deducted !== undefined && (
                                <div className="flex items-center justify-between text-xs mt-1">
                                  <span className="text-muted-foreground">Deducted:</span>
                                  <span className="font-semibold text-red-600">
                                    -{log.units_deducted.toFixed(2)} kWh
                                  </span>
                                </div>
                              )}
                              {log.units_remaining !== undefined && (
                                <div className="flex items-center justify-between text-xs mt-1">
                                  <span className="text-muted-foreground">Remaining:</span>
                                  <span className="font-semibold text-purple-600">
                                    {log.units_remaining.toFixed(2)} kWh
                                  </span>
                                </div>
                              )}
                            </div>
                          )}

                          {/* HCS Information */}
                          {log.hcs_sequence_number && (
                            <div className="pt-2 border-t border-gray-200">
                              <div className="flex items-center justify-between text-xs text-muted-foreground">
                                <span>HCS Sequence:</span>
                                <span className="font-mono">#{log.hcs_sequence_number}</span>
                              </div>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </ScrollArea>
        )}

        {logs.length > 0 && (
          <>
            <Separator className="my-4" />
            <div className="flex items-center justify-between text-xs text-muted-foreground">
              <span>
                Showing {logs.length} of {logs.length} event{logs.length !== 1 ? 's' : ''}
              </span>
              <span>Click any event to view details</span>
            </div>
          </>
        )}
      </CardContent>
    </Card>
  );
}
