/**
 * Smart Meter Domain Service
 * 
 * Core business logic for smart meter operations
 * Handles multi-user, multi-meter scenarios with proper separation of concerns
 */

import { useAppStore } from '@/stores/app-store';
import { smartMeterApi } from '@/lib/api/smart-meter';
import { ConsumptionEngine } from './consumption-engine.service';
import { CryptographicService } from './cryptographic.service';
import { HederaIntegrationService } from './hedera-integration.service';
import { RealtimeService } from './realtime.service';
import type { ConsumptionLog, ConsumptionRequest } from '@/lib/api/smart-meter';
import type { MeterState } from '@/stores/app-store';

export interface MeterInitializationConfig {
  meterId: string;
  meterNumber: string;
  userId: string;
  utilityProvider: string;
  region: string;
  autoStart?: boolean;
}

export interface SimulationConfig {
  updateInterval: number; // milliseconds
  logInterval: number; // milliseconds
  realisticPatterns: boolean;
  performanceMonitoring: boolean;
}

export interface PerformanceMetrics {
  logsPerMinute: number;
  averageResponseTime: number;
  errorRate: number;
  hederaTransactionThroughput: number;
  memoryUsage: number;
  cpuUsage: number;
}

export class SmartMeterDomainService {
  private consumptionEngine: ConsumptionEngine;
  private cryptographicService: CryptographicService;
  private hederaService: HederaIntegrationService;
  private realtimeService: RealtimeService;
  private store = useAppStore.getState();
  
  // Performance monitoring
  private performanceMonitor: Map<string, PerformanceMetrics> = new Map();
  private simulationIntervals: Map<string, NodeJS.Timeout> = new Map();
  private logIntervals: Map<string, NodeJS.Timeout> = new Map();

  constructor() {
    this.consumptionEngine = new ConsumptionEngine();
    this.cryptographicService = new CryptographicService();
    this.hederaService = new HederaIntegrationService();
    this.realtimeService = new RealtimeService();
    
    // Subscribe to store changes for reactive updates
    useAppStore.subscribe(
      (state) => state.meters,
      (meters) => this.handleMeterStateChanges(meters)
    );
  }

  /**
   * Initialize a smart meter with cryptographic keys and baseline readings
   */
  async initializeMeter(config: MeterInitializationConfig): Promise<MeterState> {
    try {
      // Generate or retrieve cryptographic keypair
      const keypair = await this.cryptographicService.ensureKeypair(config.meterId);
      
      // Initialize consumption engine for this meter
      await this.consumptionEngine.initializeMeter(config.meterId, {
        region: config.region,
        utilityProvider: config.utilityProvider,
        baselineReading: 1000.0, // Starting reading
      });
      
      // Create meter state
      const meterState: MeterState = {
        id: config.meterId,
        meterId: config.meterId,
        meterNumber: config.meterNumber,
        userId: config.userId,
        isSimulating: false,
        currentReading: 1000.0,
        lastLoggedReading: 1000.0,
        consumptionRate: 0.5,
        totalConsumed: 0,
        logsCount: 0,
        lastLogTime: null,
        publicKey: keypair.publicKey,
        status: 'idle',
      };
      
      // Add to store
      this.store.addMeter(meterState);
      this.store.addUserMeter(config.userId, config.meterId);
      
      // Auto-start if requested
      if (config.autoStart) {
        await this.startSimulation(config.meterId);
      }
      
      return meterState;
      
    } catch (error) {
      console.error('Failed to initialize meter:', error);
      throw new Error(`Meter initialization failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  /**
   * Start realistic consumption simulation for a meter
   */
  async startSimulation(meterId: string, config?: Partial<SimulationConfig>): Promise<void> {
    const meter = this.store.getMeter(meterId);
    if (!meter) {
      throw new Error(`Meter ${meterId} not found`);
    }

    if (meter.isSimulating) {
      console.warn(`Meter ${meterId} is already simulating`);
      return;
    }

    const simulationConfig: SimulationConfig = {
      updateInterval: 5000, // 5 seconds
      logInterval: 30000, // 30 seconds
      realisticPatterns: true,
      performanceMonitoring: true,
      ...config,
    };

    try {
      // Start simulation in store
      await this.store.startSimulation(meterId);
      
      // Initialize performance monitoring
      if (simulationConfig.performanceMonitoring) {
        this.initializePerformanceMonitoring(meterId);
      }
      
      // Start consumption updates
      const updateInterval = setInterval(() => {
        this.updateConsumption(meterId, simulationConfig);
      }, simulationConfig.updateInterval);
      
      // Start periodic logging
      const logInterval = setInterval(() => {
        this.logConsumption(meterId);
      }, simulationConfig.logInterval);
      
      // Store intervals for cleanup
      this.simulationIntervals.set(meterId, updateInterval);
      this.logIntervals.set(meterId, logInterval);
      
      // Setup real-time broadcasting
      await this.realtimeService.startMeterBroadcast(meterId);
      
      console.log(`✅ Started simulation for meter ${meterId}`);
      
    } catch (error) {
      console.error(`Failed to start simulation for meter ${meterId}:`, error);
      this.store.updateMeter(meterId, { 
        status: 'error', 
        error: error instanceof Error ? error.message : 'Simulation start failed' 
      });
      throw error;
    }
  }

  /**
   * Stop simulation for a meter
   */
  async stopSimulation(meterId: string): Promise<void> {
    try {
      // Clear intervals
      const updateInterval = this.simulationIntervals.get(meterId);
      const logInterval = this.logIntervals.get(meterId);
      
      if (updateInterval) {
        clearInterval(updateInterval);
        this.simulationIntervals.delete(meterId);
      }
      
      if (logInterval) {
        clearInterval(logInterval);
        this.logIntervals.delete(meterId);
      }
      
      // Stop real-time broadcasting
      await this.realtimeService.stopMeterBroadcast(meterId);
      
      // Update store
      await this.store.stopSimulation(meterId);
      
      // Clean up performance monitoring
      this.performanceMonitor.delete(meterId);
      
      console.log(`✅ Stopped simulation for meter ${meterId}`);
      
    } catch (error) {
      console.error(`Failed to stop simulation for meter ${meterId}:`, error);
      throw error;
    }
  }

  /**
   * Start multiple meter simulations concurrently
   */
  async startMultipleMeterSimulations(meterIds: string[], config?: Partial<SimulationConfig>): Promise<void> {
    console.log(`Starting ${meterIds.length} meter simulations concurrently...`);
    
    const startPromises = meterIds.map(meterId => 
      this.startSimulation(meterId, config).catch(error => {
        console.error(`Failed to start simulation for meter ${meterId}:`, error);
        return null; // Don't fail the entire batch
      })
    );
    
    await Promise.allSettled(startPromises);
    
    const successCount = meterIds.filter(id => this.store.getMeter(id)?.isSimulating).length;
    console.log(`✅ Started ${successCount}/${meterIds.length} meter simulations`);
  }

  /**
   * Update consumption reading with realistic patterns
   */
  private updateConsumption(meterId: string, config: SimulationConfig): void {
    const meter = this.store.getMeter(meterId);
    if (!meter || meter.status !== 'running') return;

    try {
      // Get realistic consumption rate
      const consumptionRate = config.realisticPatterns 
        ? this.consumptionEngine.getRealisticConsumptionRate(meterId)
        : 0.5; // Default rate
      
      // Calculate increment (interval in hours)
      const intervalHours = config.updateInterval / (1000 * 60 * 60);
      const increment = consumptionRate * intervalHours;
      
      // Update meter state
      this.store.updateMeter(meterId, {
        consumptionRate,
        currentReading: meter.currentReading + increment,
        totalConsumed: meter.totalConsumed + increment,
      });
      
      // Broadcast real-time update
      this.realtimeService.broadcastMeterUpdate(meterId, {
        currentReading: meter.currentReading + increment,
        consumptionRate,
        timestamp: new Date().toISOString(),
      });
      
      // Update performance metrics
      if (config.performanceMonitoring) {
        this.updatePerformanceMetrics(meterId);
      }
      
    } catch (error) {
      console.error(`Error updating consumption for meter ${meterId}:`, error);
      this.store.updateMeter(meterId, { 
        status: 'error', 
        error: 'Consumption update failed' 
      });
    }
  }

  /**
   * Log consumption data with cryptographic signature
   */
  private async logConsumption(meterId: string): Promise<void> {
    const meter = this.store.getMeter(meterId);
    if (!meter || meter.status !== 'running') return;

    // Skip if no significant consumption
    const consumptionKwh = meter.currentReading - meter.lastLoggedReading;
    if (consumptionKwh < 0.001) return;

    try {
      const startTime = Date.now();
      
      // Generate cryptographic signature
      const timestamp = new Date().toISOString();
      const signature = await this.cryptographicService.signConsumption({
        meterId: meter.meterId,
        consumption: consumptionKwh,
        timestamp,
        readingBefore: meter.lastLoggedReading,
        readingAfter: meter.currentReading,
      });

      // Prepare consumption request
      const consumptionRequest: ConsumptionRequest = {
        meter_id: meterId,
        consumption_kwh: consumptionKwh,
        timestamp,
        signature,
        public_key: meter.publicKey,
        reading_before: meter.lastLoggedReading,
        reading_after: meter.currentReading,
      };

      // Log to backend and Hedera
      const log = await smartMeterApi.logConsumption(consumptionRequest);
      
      // Update store
      this.store.addConsumptionLog(meterId, log);
      this.store.updateMeter(meterId, {
        lastLoggedReading: meter.currentReading,
      });
      
      // Log to Hedera HCS for immutable record
      await this.hederaService.logConsumptionToHCS(log);
      
      // Broadcast to real-time subscribers
      this.realtimeService.broadcastConsumptionLog(meterId, log);
      
      // Update performance metrics
      const responseTime = Date.now() - startTime;
      this.updateLogPerformance(meterId, responseTime, true);
      
      console.log(`✅ Logged consumption for meter ${meterId}: ${consumptionKwh.toFixed(3)} kWh`);
      
    } catch (error) {
      console.error(`Failed to log consumption for meter ${meterId}:`, error);
      this.updateLogPerformance(meterId, 0, false);
      
      // Don't stop simulation on logging errors, just log the error
      this.store.updateMeter(meterId, {
        error: `Logging failed: ${error instanceof Error ? error.message : 'Unknown error'}`,
      });
    }
  }

  /**
   * Initialize performance monitoring for a meter
   */
  private initializePerformanceMonitoring(meterId: string): void {
    this.performanceMonitor.set(meterId, {
      logsPerMinute: 0,
      averageResponseTime: 0,
      errorRate: 0,
      hederaTransactionThroughput: 0,
      memoryUsage: 0,
      cpuUsage: 0,
    });
  }

  /**
   * Update performance metrics
   */
  private updatePerformanceMetrics(meterId: string): void {
    const metrics = this.performanceMonitor.get(meterId);
    if (!metrics) return;

    // Update memory usage (simplified)
    metrics.memoryUsage = (performance as any).memory?.usedJSHeapSize || 0;
    
    // Update store simulation performance
    this.store.updateSimulationPerformance(meterId, {
      averageResponseTime: metrics.averageResponseTime,
      errorRate: metrics.errorRate,
      logsPerMinute: metrics.logsPerMinute,
    });
  }

  /**
   * Update logging performance metrics
   */
  private updateLogPerformance(meterId: string, responseTime: number, success: boolean): void {
    const metrics = this.performanceMonitor.get(meterId);
    if (!metrics) return;

    // Update response time (moving average)
    metrics.averageResponseTime = (metrics.averageResponseTime * 0.9) + (responseTime * 0.1);
    
    // Update error rate
    if (!success) {
      metrics.errorRate = Math.min(metrics.errorRate + 0.1, 1.0);
    } else {
      metrics.errorRate = Math.max(metrics.errorRate - 0.01, 0);
    }
    
    // Update logs per minute (simplified)
    metrics.logsPerMinute = (metrics.logsPerMinute * 0.95) + (success ? 2 : 0);
  }

  /**
   * Handle meter state changes reactively
   */
  private handleMeterStateChanges(meters: Map<string, MeterState>): void {
    // Update global performance metrics
    const activeMeterCount = Array.from(meters.values()).filter(m => m.isSimulating).length;
    const totalLogs = Array.from(meters.values()).reduce((sum, m) => sum + m.logsCount, 0);
    
    this.store.updatePerformanceMetrics({
      activeMeterCount,
      totalLogsGenerated: totalLogs,
    });
  }

  /**
   * Get comprehensive analytics for a user's meters
   */
  getAnalytics(userId: string) {
    return this.store.getConsumptionAnalytics(userId);
  }

  /**
   * Get system health metrics
   */
  getSystemHealth() {
    return this.store.getSystemHealth();
  }

  /**
   * Clean up resources
   */
  async cleanup(): Promise<void> {
    // Stop all simulations
    await this.store.stopAllSimulations();
    
    // Clear all intervals
    this.simulationIntervals.forEach(interval => clearInterval(interval));
    this.logIntervals.forEach(interval => clearInterval(interval));
    
    this.simulationIntervals.clear();
    this.logIntervals.clear();
    this.performanceMonitor.clear();
    
    // Cleanup services
    await this.realtimeService.cleanup();
    await this.hederaService.cleanup();
  }
}