/**
 * Smart Meter Verification Page
 * 
 * Displays smart meter consumption verification with:
 * - Selected consumption log details
 * - Signature verification
 * - Consumption history list
 * 
 * Requirements: US-17, Task 2.7
 */

import { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { SmartMeterVerification, ConsumptionLog } from '@/components/SmartMeterVerification';
import { ConsumptionHistoryList } from '@/components/ConsumptionHistoryList';
import { Card, CardContent } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Loader2, AlertCircle } from 'lucide-react';

export default function SmartMeterVerifyPage() {
  const [searchParams] = useSearchParams();
  const meterId = searchParams.get('meter_id');
  const logId = searchParams.get('log_id');

  const [selectedLog, setSelectedLog] = useState<ConsumptionLog | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // If a specific log_id is provided, fetch that log
    if (logId && meterId) {
      fetchSpecificLog(logId);
    } else if (meterId) {
      // Otherwise, fetch the most recent log for the meter
      fetchMostRecentLog(meterId);
    } else {
      setLoading(false);
      setError('No meter ID provided');
    }
  }, [logId, meterId]);

  const fetchSpecificLog = async (id: string) => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`/api/smart-meter/consumption-logs?meter_id=${meterId}&limit=100`);
      
      if (!response.ok) {
        throw new Error('Failed to fetch consumption log');
      }

      const data = await response.json();
      const log = data.logs?.find((l: ConsumptionLog) => l.id === id);

      if (log) {
        setSelectedLog(log);
      } else {
        setError('Consumption log not found');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load consumption log');
    } finally {
      setLoading(false);
    }
  };

  const fetchMostRecentLog = async (meter: string) => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`/api/smart-meter/consumption-logs?meter_id=${meter}&limit=1`);
      
      if (!response.ok) {
        throw new Error('Failed to fetch consumption logs');
      }

      const data = await response.json();
      
      if (data.logs && data.logs.length > 0) {
        setSelectedLog(data.logs[0]);
      } else {
        setError('No consumption logs found for this meter');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load consumption logs');
    } finally {
      setLoading(false);
    }
  };

  const handleSelectLog = (log: ConsumptionLog) => {
    setSelectedLog(log);
    // Scroll to top to show the selected log details
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  if (!meterId) {
    return (
      <div className="container mx-auto px-4 py-8 max-w-7xl">
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            No meter ID provided. Please select a meter to view consumption verification.
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-8 max-w-7xl">
        <Card>
          <CardContent className="flex items-center justify-center py-12">
            <Loader2 className="w-8 h-8 animate-spin text-muted-foreground" />
          </CardContent>
        </Card>
      </div>
    );
  }

  if (error && !selectedLog) {
    return (
      <div className="container mx-auto px-4 py-8 max-w-7xl">
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8 max-w-7xl">
      <div className="mb-6">
        <h1 className="text-3xl font-bold mb-2">Smart Meter Verification</h1>
        <p className="text-muted-foreground">
          Cryptographically verified consumption data with signature validation
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Selected Log Details */}
        <div className="lg:col-span-1">
          {selectedLog ? (
            <SmartMeterVerification consumptionLog={selectedLog} />
          ) : (
            <Card>
              <CardContent className="flex items-center justify-center py-12">
                <p className="text-muted-foreground">Select a consumption event to view details</p>
              </CardContent>
            </Card>
          )}
        </div>

        {/* Consumption History List */}
        <div className="lg:col-span-1">
          <ConsumptionHistoryList
            meterId={meterId}
            onSelectLog={handleSelectLog}
            limit={50}
          />
        </div>
      </div>
    </div>
  );
}
