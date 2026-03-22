/**
 * Smart Meter Simulator Component
 * 
 * Simulates realistic smart meter consumption data with cryptographic signatures
 * Features:
 * - Realistic consumption patterns (daily/hourly variations)
 * - Automatic consumption logging
 * - Real-time meter readings
 * - Signature generation and verification
 */

import { useState, useEffect, useRef } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Separator } from '@/components/ui/separator';
import {
  Activity,
  Play,
  Pause,
  RotateCcw,
  Zap,
  TrendingUp,
  Clock,
  Shield,
  CheckCircle,
  AlertTriangle,
  Loader2,
} from 'lucide-react';
import { toast } from 'sonner';
import { smartMeterApi } from '@/lib/api/smart-meter';
import type { ConsumptionLog } from '@/lib/api/smart-meter';

export interface SmartMeterSimulatorProps {
  meterId: string;
  meterNumber: string;
  onConsumptionLogged?: (log: ConsumptionLog) => void;
  autoStart?: boolean;
}

export function SmartMeterSimulator({
  meterId,
  meterNumber,
  onConsumptionLogged,
  autoStart = false,
}: SmartMeterSimulatorProps) {
  const [isRunning, setIsRunning] = useState(autoStart);
  const [currentReading, setCurrentReading] = useState(1000.0); // Starting reading in kWh
  const [lastLoggedReading, setLastLoggedReading] = useState(1000.0);
  const [consumptionRate, setConsumptionRate] = useState(0.5); // kWh per hour
  const [totalConsumed, setTotalConsumed] = useState(0);
  const [logsCount, setLogsCount] = useState(0);
  const [lastLogTime, setLastLogTime] = useState<Date | null>(null);
  const [isLogging, setIsLogging] = useState(false);
  const [publicKey, setPublicKey] = useState<string>('');
  
  const intervalRef = useRef<NodeJS.Timeout>();
  const logIntervalRef = useRef<NodeJS.Timeout>();

  // Initialize public key
  useEffect(() => {
    const initializeKeypair = async () => {
      try {
        // Try to get existing public key
        const existingKey = await smartMeterApi.getPublicKey(meterId);
        setPublicKey(existingKey);
      } catch (error) {
        try {
          // Generate new keypair if none exists
          const keypair = await smartMeterApi.generateKeypair(meterId);
          setPublicKey(keypair.public_key);
          toast.success('Smart meter keypair generated', {
            description: 'Cryptographic keys created for secure consumption logging',
          });
        } catch (genError) {
          console.error('Failed to initialize keypair:', genError);
          toast.error('Failed to initialize smart meter security');
        }
      }
    };

    initializeKeypair();
  }, [meterId]);

  // Simulate realistic consumption patterns
  const getRealisticConsumptionRate = () => {
    const hour = new Date().getHours();
    const dayOfWeek = new Date().getDay();
    
    // Base consumption rate (kWh per hour)
    let baseRate = 0.3;
    
    // Higher consumption during peak hours (7-9 AM, 6-10 PM)
    if ((hour >= 7 && hour <= 9) || (hour >= 18 && hour <= 22)) {
      baseRate *= 2.5;
    }
    // Lower consumption during night (11 PM - 6 AM)
    else if (hour >= 23 || hour <= 6) {
      baseRate *= 0.4;
    }
    // Moderate consumption during day
    else {
      baseRate *= 1.2;
    }
    
    // Weekend patterns (slightly higher consumption)
    if (dayOfWeek === 0 || dayOfWeek === 6) {
      baseRate *= 1.3;
    }
    
    // Add some randomness (±20%)
    const randomFactor = 0.8 + Math.random() * 0.4;
    
    return baseRate * randomFactor;
  };

  // Start/stop simulation
  const toggleSimulation = () => {
    if (isRunning) {
      stopSimulation();
    } else {
      startSimulation();
    }
  };

  const startSimulation = () => {
    if (!publicKey) {
      toast.error('Smart meter not initialized', {
        description: 'Please wait for keypair generation to complete',
      });
      return;
    }

    setIsRunning(true);
    
    // Update consumption every 5 seconds (simulating real-time)
    intervalRef.current = setInterval(() => {
      const rate = getRealisticConsumptionRate();
      setConsumptionRate(rate);
      
      // Increment reading (5 seconds = 5/3600 hours)
      const increment = rate * (5 / 3600);
      setCurrentReading(prev => prev + increment);
      setTotalConsumed(prev => prev + increment);
    }, 5000);

    // No fixed-time log interval — logging is triggered by 0.1 kWh threshold in useEffect

    toast.success('Smart meter simulation started', {
      description: 'Will log to HCS every 0.1 kWh consumed',
    });
  };

  const stopSimulation = () => {
    setIsRunning(false);
    
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
    }
    if (logIntervalRef.current) {
      clearInterval(logIntervalRef.current);
    }

    toast.info('Smart meter simulation stopped');
  };

  const resetSimulation = () => {
    stopSimulation();
    setCurrentReading(1000.0);
    setLastLoggedReading(1000.0);
    setTotalConsumed(0);
    setLogsCount(0);
    setLastLogTime(null);
    
    toast.info('Smart meter simulation reset');
  };

  // Auto-log when consumption crosses 0.1 kWh threshold
  useEffect(() => {
    if (!isRunning || isLogging) return;
    const delta = currentReading - lastLoggedReading;
    if (delta >= 0.1) {
      logConsumption();
    }
  }, [currentReading]);

  // Log consumption to backend with real ED25519 signature
  const logConsumption = async () => {
    if (isLogging || !publicKey) return;
    
    setIsLogging(true);
    
    try {
      const readingBefore = lastLoggedReading;
      const readingAfter = currentReading;
      const consumptionKwh = readingAfter - readingBefore;
      
      if (consumptionKwh < 0.001) {
        setIsLogging(false);
        return;
      }

      const timestamp = Math.floor(Date.now() / 1000); // Unix timestamp (int)

      // Step 1: Get real ED25519 signature from server
      const signed = await smartMeterApi.signConsumption({
        meter_id: meterId,
        consumption_kwh: consumptionKwh,
        timestamp,
        reading_before: readingBefore,
        reading_after: readingAfter,
      });

      // Step 2: Submit consumption with real signature
      const log = await smartMeterApi.logConsumption({
        meter_id: meterId,
        consumption_kwh: consumptionKwh,
        timestamp,
        signature: signed.signature,
        public_key: signed.public_key,
        reading_before: readingBefore,
        reading_after: readingAfter,
      });
      
      setLastLoggedReading(readingAfter);
      setLogsCount(prev => prev + 1);
      setLastLogTime(new Date());
      
      if (onConsumptionLogged) {
        onConsumptionLogged(log);
      }

      toast.success('Consumption logged to Hedera HCS', {
        description: `${consumptionKwh.toFixed(3)} kWh · seq #${log.hcs_sequence_number ?? '—'}`,
        duration: 4000,
      });
      
    } catch (error) {
      console.error('Failed to log consumption:', error);
      toast.error('Failed to log consumption', {
        description: error instanceof Error ? error.message : 'Unknown error',
      });
    } finally {
      setIsLogging(false);
    }
  };

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
      if (logIntervalRef.current) clearInterval(logIntervalRef.current);
    };
  }, []);

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
          <Badge variant={isRunning ? "default" : "secondary"} className="gap-1">
            {isRunning ? <Play className="w-3 h-3" /> : <Pause className="w-3 h-3" />}
            {isRunning ? 'Running' : 'Stopped'}
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Current Status */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="p-3 bg-blue-50 rounded-lg">
            <div className="flex items-center gap-2 mb-1">
              <Zap className="w-4 h-4 text-blue-600" />
              <span className="text-sm font-medium">Current Reading</span>
            </div>
            <p className="text-xl font-bold text-blue-900">
              {currentReading.toFixed(3)} kWh
            </p>
          </div>
          
          <div className="p-3 bg-green-50 rounded-lg">
            <div className="flex items-center gap-2 mb-1">
              <TrendingUp className="w-4 h-4 text-green-600" />
              <span className="text-sm font-medium">Consumption Rate</span>
            </div>
            <p className="text-xl font-bold text-green-900">
              {consumptionRate.toFixed(2)} kWh/h
            </p>
          </div>
          
          <div className="p-3 bg-purple-50 rounded-lg">
            <div className="flex items-center gap-2 mb-1">
              <Activity className="w-4 h-4 text-purple-600" />
              <span className="text-sm font-medium">Total Consumed</span>
            </div>
            <p className="text-xl font-bold text-purple-900">
              {totalConsumed.toFixed(3)} kWh
            </p>
          </div>
          
          <div className="p-3 bg-orange-50 rounded-lg">
            <div className="flex items-center gap-2 mb-1">
              <Shield className="w-4 h-4 text-orange-600" />
              <span className="text-sm font-medium">Logs Created</span>
            </div>
            <p className="text-xl font-bold text-orange-900">
              {logsCount}
            </p>
          </div>
        </div>

        {/* Consumption Progress */}
        <div className="space-y-2">
          <div className="flex justify-between text-sm">
            <span>Consumption since last log</span>
            <span>{(currentReading - lastLoggedReading).toFixed(3)} kWh</span>
          </div>
          <Progress 
            value={Math.min(((currentReading - lastLoggedReading) / 0.1) * 100, 100)} 
            className="h-2"
          />
          <p className="text-xs text-muted-foreground">
            Next log when consumption reaches ~0.1 kWh or after 30 seconds
          </p>
        </div>

        <Separator />

        {/* Controls */}
        <div className="flex gap-3">
          <Button
            onClick={toggleSimulation}
            className="flex-1"
            variant={isRunning ? "destructive" : "default"}
          >
            {isRunning ? (
              <>
                <Pause className="w-4 h-4 mr-2" />
                Stop Simulation
              </>
            ) : (
              <>
                <Play className="w-4 h-4 mr-2" />
                Start Simulation
              </>
            )}
          </Button>
          
          <Button onClick={resetSimulation} variant="outline">
            <RotateCcw className="w-4 h-4 mr-2" />
            Reset
          </Button>
          
          <Button 
            onClick={logConsumption} 
            variant="outline"
            disabled={isLogging || !isRunning}
          >
            {isLogging ? (
              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
            ) : (
              <Shield className="w-4 h-4 mr-2" />
            )}
            Log Now
          </Button>
        </div>

        {/* Last Log Info */}
        {lastLogTime && (
          <div className="p-3 bg-green-50 border border-green-200 rounded-lg">
            <div className="flex items-center gap-2 mb-1">
              <CheckCircle className="w-4 h-4 text-green-600" />
              <span className="text-sm font-medium text-green-900">Last Log</span>
            </div>
            <p className="text-sm text-green-800">
              {lastLogTime.toLocaleString()} - Consumption verified and logged to Hedera HCS
            </p>
          </div>
        )}

        {/* Security Info */}
        <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg">
          <div className="flex items-center gap-2 mb-2">
            <Shield className="w-4 h-4 text-blue-600" />
            <span className="text-sm font-medium text-blue-900">Cryptographic Security</span>
          </div>
          <div className="space-y-1 text-xs text-blue-800">
            <p>• All consumption data is signed with ED25519 cryptography</p>
            <p>• Signatures are verified before accepting any consumption logs</p>
            <p>• Invalid signatures are rejected and flagged as potential fraud</p>
            <p>• All verifications are logged immutably to Hedera Consensus Service</p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}