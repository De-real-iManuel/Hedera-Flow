/**
 * SmartMeterSimulator
 *
 * All simulation state lives on the backend (in-process).
 * The component polls /simulator/tick every 5 s while running.
 * No local consumption math — the server drives everything.
 */

import { useState, useEffect, useRef, useCallback } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Separator } from '@/components/ui/separator';
import {
  Activity, Play, Pause, RotateCcw, Zap,
  TrendingUp, Shield, CheckCircle, Loader2,
} from 'lucide-react';
import { toast } from 'sonner';
import { smartMeterApi } from '@/lib/api/smart-meter';
import type { ConsumptionLog, SimulatorState } from '@/lib/api/smart-meter';

export interface SmartMeterSimulatorProps {
  meterId: string;
  meterNumber: string;
  onConsumptionLogged?: (log: ConsumptionLog) => void;
  autoStart?: boolean;
}

const TICK_INTERVAL_MS = 5000;
const TICK_SECONDS = 5;

export function SmartMeterSimulator({
  meterId,
  meterNumber,
  onConsumptionLogged,
  autoStart = false,
}: SmartMeterSimulatorProps) {
  const [state, setState] = useState<SimulatorState>({
    running: false,
    meter_id: meterId,
    current_reading: 1000,
    last_logged_reading: 1000,
    total_consumed: 0,
    logs_count: 0,
    consumption_rate: 0,
    last_log_at: null,
  });
  const [loading, setLoading] = useState(false);
  const tickRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // ------------------------------------------------------------------
  // Sync with backend on mount
  // ------------------------------------------------------------------
  useEffect(() => {
    smartMeterApi.getSimulatorStatus(meterId)
      .then(s => {
        setState(s);
        if (s.running) startPolling();
      })
      .catch(() => {/* meter may not have a simulator yet */});

    if (autoStart) handleStart();

    return () => stopPolling();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [meterId]);

  // ------------------------------------------------------------------
  // Polling
  // ------------------------------------------------------------------
  const stopPolling = () => {
    if (tickRef.current) {
      clearInterval(tickRef.current);
      tickRef.current = null;
    }
  };

  const startPolling = useCallback(() => {
    stopPolling();
    tickRef.current = setInterval(async () => {
      try {
        const res = await smartMeterApi.tickSimulator(meterId, TICK_SECONDS);
        setState(res.state);

        if (res.auto_logged) {
          const log = res.auto_logged;
          toast.success('Consumption logged to Hedera HCS', {
            description: `${log.consumption_kwh.toFixed(3)} kWh · seq #${log.hcs_sequence_number ?? '—'}`,
            duration: 4000,
          });
          if (onConsumptionLogged) {
            // Minimal shape for the callback
            onConsumptionLogged({
              consumption_log_id: log.consumption_log_id,
              meter_id: meterId,
              consumption_kwh: log.consumption_kwh,
              timestamp: Math.floor(Date.now() / 1000),
              signature_valid: true,
              hcs_sequence_number: log.hcs_sequence_number,
            });
          }
        }
      } catch (err) {
        console.error('Tick failed:', err);
      }
    }, TICK_INTERVAL_MS);
  }, [meterId, onConsumptionLogged]);

  // ------------------------------------------------------------------
  // Controls
  // ------------------------------------------------------------------
  const handleStart = async () => {
    setLoading(true);
    try {
      const s = await smartMeterApi.startSimulator(meterId);
      setState(s);
      startPolling();
      toast.success('Smart meter simulation started', {
        description: 'Logs to HCS every 0.1 kWh consumed',
      });
    } catch (err) {
      toast.error('Failed to start simulator', {
        description: err instanceof Error ? err.message : 'Unknown error',
      });
    } finally {
      setLoading(false);
    }
  };

  const handleStop = async () => {
    setLoading(true);
    stopPolling();
    try {
      const s = await smartMeterApi.stopSimulator(meterId);
      setState(s);
      toast.info('Smart meter simulation stopped');
    } catch (err) {
      toast.error('Failed to stop simulator');
    } finally {
      setLoading(false);
    }
  };

  const handleReset = async () => {
    stopPolling();
    setLoading(true);
    try {
      // Stop on backend first (ignore error if not running)
      await smartMeterApi.stopSimulator(meterId).catch(() => {});
    } finally {
      setState({
        running: false,
        meter_id: meterId,
        current_reading: 1000,
        last_logged_reading: 1000,
        total_consumed: 0,
        logs_count: 0,
        consumption_rate: 0,
        last_log_at: null,
      });
      setLoading(false);
      toast.info('Smart meter simulation reset');
    }
  };

  const handleLogNow = async () => {
    if (!state.running) return;
    setLoading(true);
    try {
      const res = await smartMeterApi.tickSimulator(meterId, TICK_SECONDS);
      setState(res.state);
      if (res.auto_logged) {
        toast.success('Manually triggered log sent to HCS');
      } else {
        toast.info('Tick advanced — not enough delta to log yet');
      }
    } catch (err) {
      toast.error('Manual log failed');
    } finally {
      setLoading(false);
    }
  };

  // ------------------------------------------------------------------
  // Derived values
  // ------------------------------------------------------------------
  const delta = state.current_reading - state.last_logged_reading;
  const progressPct = Math.min((delta / 0.1) * 100, 100);

  return (
    <Card className="w-full">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-blue-100 rounded-lg">
              <Activity className="w-6 h-6 text-blue-600" />
            </div>
            <div>
              <CardTitle>Smart Meter Simulator</CardTitle>
              <CardDescription>
                Realistic consumption patterns with cryptographic verification
              </CardDescription>
            </div>
          </div>
          <Badge variant={state.running ? 'default' : 'secondary'} className="gap-1">
            {state.running ? <Play className="w-3 h-3" /> : <Pause className="w-3 h-3" />}
            {state.running ? 'Running' : 'Stopped'}
          </Badge>
        </div>
      </CardHeader>

      <CardContent className="space-y-6">
        {/* Stats grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="p-3 bg-blue-50 rounded-lg">
            <div className="flex items-center gap-2 mb-1">
              <Zap className="w-4 h-4 text-blue-600" />
              <span className="text-sm font-medium">Current Reading</span>
            </div>
            <p className="text-xl font-bold text-blue-900">
              {state.current_reading.toFixed(3)} kWh
            </p>
          </div>

          <div className="p-3 bg-green-50 rounded-lg">
            <div className="flex items-center gap-2 mb-1">
              <TrendingUp className="w-4 h-4 text-green-600" />
              <span className="text-sm font-medium">Consumption Rate</span>
            </div>
            <p className="text-xl font-bold text-green-900">
              {(state.consumption_rate ?? 0).toFixed(2)} kWh/h
            </p>
          </div>

          <div className="p-3 bg-purple-50 rounded-lg">
            <div className="flex items-center gap-2 mb-1">
              <Activity className="w-4 h-4 text-purple-600" />
              <span className="text-sm font-medium">Total Consumed</span>
            </div>
            <p className="text-xl font-bold text-purple-900">
              {state.total_consumed.toFixed(3)} kWh
            </p>
          </div>

          <div className="p-3 bg-orange-50 rounded-lg">
            <div className="flex items-center gap-2 mb-1">
              <Shield className="w-4 h-4 text-orange-600" />
              <span className="text-sm font-medium">Logs Created</span>
            </div>
            <p className="text-xl font-bold text-orange-900">
              {state.logs_count}
            </p>
          </div>
        </div>

        {/* Progress to next log */}
        <div className="space-y-2">
          <div className="flex justify-between text-sm">
            <span>Consumption since last log</span>
            <span>{delta.toFixed(3)} kWh</span>
          </div>
          <Progress value={progressPct} className="h-2" />
          <p className="text-xs text-muted-foreground">
            Next log triggers at 0.1 kWh threshold
          </p>
        </div>

        <Separator />

        {/* Controls */}
        <div className="flex gap-3">
          <Button
            onClick={state.running ? handleStop : handleStart}
            className="flex-1"
            variant={state.running ? 'destructive' : 'default'}
            disabled={loading}
          >
            {loading ? (
              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
            ) : state.running ? (
              <Pause className="w-4 h-4 mr-2" />
            ) : (
              <Play className="w-4 h-4 mr-2" />
            )}
            {state.running ? 'Stop Simulation' : 'Start Simulation'}
          </Button>

          <Button onClick={handleReset} variant="outline" disabled={loading}>
            <RotateCcw className="w-4 h-4 mr-2" />
            Reset
          </Button>

          <Button
            onClick={handleLogNow}
            variant="outline"
            disabled={loading || !state.running}
          >
            {loading ? (
              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
            ) : (
              <Shield className="w-4 h-4 mr-2" />
            )}
            Log Now
          </Button>
        </div>

        {/* Last log */}
        {state.last_log_at && (
          <div className="p-3 bg-green-50 border border-green-200 rounded-lg">
            <div className="flex items-center gap-2 mb-1">
              <CheckCircle className="w-4 h-4 text-green-600" />
              <span className="text-sm font-medium text-green-900">Last Log</span>
            </div>
            <p className="text-sm text-green-800">
              {new Date(state.last_log_at).toLocaleString()} — verified and logged to Hedera HCS
            </p>
          </div>
        )}

        {/* Security info */}
        <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg">
          <div className="flex items-center gap-2 mb-2">
            <Shield className="w-4 h-4 text-blue-600" />
            <span className="text-sm font-medium text-blue-900">Cryptographic Security</span>
          </div>
          <div className="space-y-1 text-xs text-blue-800">
            <p>• Consumption data signed via AWS KMS HSM (or ED25519 fallback)</p>
            <p>• Private keys never leave the HSM or touch application memory</p>
            <p>• Invalid signatures are rejected and flagged as potential fraud</p>
            <p>• All verifications logged immutably to Hedera Consensus Service</p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
