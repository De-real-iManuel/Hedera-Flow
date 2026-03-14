/**
 * Global Application Store
 * 
 * Centralized state management using Zustand for:
 * - Smart meter simulations
 * - User management
 * - Real-time updates
 * - Multi-tenant support
 */

import { create } from 'zustand';
import { devtools, subscribeWithSelector } from 'zustand/middleware';
import { immer } from 'zustand/middleware/immer';
import type { ConsumptionLog } from '@/lib/api/smart-meter';

// Core Types
export interface MeterState {
  id: string;
  meterId: string;
  meterNumber: string;
  userId: string;
  isSimulating: boolean;
  currentReading: number;
  lastLoggedReading: number;
  consumptionRate: number;
  totalConsumed: number;
  logsCount: number;
  lastLogTime: Date | null;
  publicKey: string;
  status: 'idle' | 'running' | 'paused' | 'error';
  error?: string;
}

export interface SimulationState {
  meterId: string;
  intervalId?: NodeJS.Timeout;
  logIntervalId?: NodeJS.Timeout;
  startTime: Date;
  isLogging: boolean;
  performance: {
    logsPerMinute: number;
    averageResponseTime: number;
    errorRate: number;
  };
}

export interface UserState {
  id: string;
  email: string;
  hederaAccountId?: string;
  activeMeters: string[];
  totalConsumption: number;
  totalTokensPurchased: number;
  isOnline: boolean;
  lastActivity: Date;
}

export interface RealtimeConnection {
  userId: string;
  meterId: string;
  socket?: WebSocket;
  status: 'connected' | 'disconnected' | 'reconnecting';
  lastHeartbeat: Date;
}

// Store Interface
interface AppStore {
  // State
  meters: Map<string, MeterState>;
  simulations: Map<string, SimulationState>;
  consumptionLogs: Map<string, ConsumptionLog[]>;
  users: Map<string, UserState>;
  currentUser: UserState | null;
  realtimeConnections: Map<string, RealtimeConnection>;
  
  // Performance Metrics
  performance: {
    activeMeterCount: number;
    totalLogsGenerated: number;
    averageSimulationLoad: number;
    hederaTransactionThroughput: number;
  };
  
  // Actions - Meter Management
  addMeter: (meter: MeterState) => void;
  updateMeter: (meterId: string, updates: Partial<MeterState>) => void;
  removeMeter: (meterId: string) => void;
  getMeter: (meterId: string) => MeterState | undefined;
  getUserMeters: (userId: string) => MeterState[];
  
  // Actions - Simulation Management
  startSimulation: (meterId: string) => Promise<void>;
  stopSimulation: (meterId: string) => Promise<void>;
  pauseSimulation: (meterId: string) => void;
  resumeSimulation: (meterId: string) => void;
  updateSimulationPerformance: (meterId: string, metrics: Partial<SimulationState['performance']>) => void;
  
  // Actions - Consumption Logs
  addConsumptionLog: (meterId: string, log: ConsumptionLog) => void;
  getConsumptionLogs: (meterId: string) => ConsumptionLog[];
  clearConsumptionLogs: (meterId: string) => void;
  
  // Actions - User Management
  setCurrentUser: (user: UserState) => void;
  updateUser: (userId: string, updates: Partial<UserState>) => void;
  addUserMeter: (userId: string, meterId: string) => void;
  removeUserMeter: (userId: string, meterId: string) => void;
  
  // Actions - Real-time Connections
  addRealtimeConnection: (connection: RealtimeConnection) => void;
  updateConnectionStatus: (userId: string, meterId: string, status: RealtimeConnection['status']) => void;
  removeRealtimeConnection: (userId: string, meterId: string) => void;
  
  // Actions - Performance
  updatePerformanceMetrics: (metrics: Partial<AppStore['performance']>) => void;
  getSystemHealth: () => {
    activeMeterCount: number;
    averageLoad: number;
    errorRate: number;
    throughput: number;
  };
  
  // Actions - Bulk Operations
  startMultipleMeterSimulations: (meterIds: string[]) => Promise<void>;
  stopAllSimulations: () => Promise<void>;
  resetAllMeters: () => void;
  
  // Actions - Analytics
  getConsumptionAnalytics: (userId: string) => {
    totalConsumption: number;
    averageDaily: number;
    peakUsage: number;
    costEstimate: number;
  };
}

// Create Store
export const useAppStore = create<AppStore>()(
  devtools(
    subscribeWithSelector(
      immer((set, get) => ({
        // Initial State
        meters: new Map(),
        simulations: new Map(),
        consumptionLogs: new Map(),
        users: new Map(),
        currentUser: null,
        realtimeConnections: new Map(),
        performance: {
          activeMeterCount: 0,
          totalLogsGenerated: 0,
          averageSimulationLoad: 0,
          hederaTransactionThroughput: 0,
        },
        
        // Meter Management Actions
        addMeter: (meter) => set((state) => {
          state.meters.set(meter.id, meter);
          state.performance.activeMeterCount = state.meters.size;
        }),
        
        updateMeter: (meterId, updates) => set((state) => {
          const meter = state.meters.get(meterId);
          if (meter) {
            Object.assign(meter, updates);
          }
        }),
        
        removeMeter: (meterId) => set((state) => {
          state.meters.delete(meterId);
          state.simulations.delete(meterId);
          state.consumptionLogs.delete(meterId);
          state.performance.activeMeterCount = state.meters.size;
        }),
        
        getMeter: (meterId) => {
          return get().meters.get(meterId);
        },
        
        getUserMeters: (userId) => {
          const meters = Array.from(get().meters.values());
          return meters.filter(meter => meter.userId === userId);
        },
        
        // Simulation Management Actions
        startSimulation: async (meterId) => {
          const meter = get().meters.get(meterId);
          if (!meter) return;
          
          set((state) => {
            const meter = state.meters.get(meterId);
            if (meter) {
              meter.isSimulating = true;
              meter.status = 'running';
            }
            
            state.simulations.set(meterId, {
              meterId,
              startTime: new Date(),
              isLogging: false,
              performance: {
                logsPerMinute: 0,
                averageResponseTime: 0,
                errorRate: 0,
              },
            });
          });
        },
        
        stopSimulation: async (meterId) => {
          const simulation = get().simulations.get(meterId);
          if (simulation) {
            if (simulation.intervalId) clearInterval(simulation.intervalId);
            if (simulation.logIntervalId) clearInterval(simulation.logIntervalId);
          }
          
          set((state) => {
            const meter = state.meters.get(meterId);
            if (meter) {
              meter.isSimulating = false;
              meter.status = 'idle';
            }
            state.simulations.delete(meterId);
          });
        },
        
        pauseSimulation: (meterId) => set((state) => {
          const meter = state.meters.get(meterId);
          if (meter) {
            meter.status = 'paused';
          }
        }),
        
        resumeSimulation: (meterId) => set((state) => {
          const meter = state.meters.get(meterId);
          if (meter) {
            meter.status = 'running';
          }
        }),
        
        updateSimulationPerformance: (meterId, metrics) => set((state) => {
          const simulation = state.simulations.get(meterId);
          if (simulation) {
            Object.assign(simulation.performance, metrics);
          }
        }),
        
        // Consumption Log Actions
        addConsumptionLog: (meterId, log) => set((state) => {
          const logs = state.consumptionLogs.get(meterId) || [];
          logs.unshift(log); // Add to beginning for chronological order
          
          // Keep only last 100 logs per meter for performance
          if (logs.length > 100) {
            logs.splice(100);
          }
          
          state.consumptionLogs.set(meterId, logs);
          state.performance.totalLogsGenerated += 1;
          
          // Update meter state
          const meter = state.meters.get(meterId);
          if (meter) {
            meter.logsCount += 1;
            meter.lastLogTime = new Date();
          }
        }),
        
        getConsumptionLogs: (meterId) => {
          return get().consumptionLogs.get(meterId) || [];
        },
        
        clearConsumptionLogs: (meterId) => set((state) => {
          state.consumptionLogs.delete(meterId);
        }),
        
        // User Management Actions
        setCurrentUser: (user) => set((state) => {
          state.currentUser = user;
          state.users.set(user.id, user);
        }),
        
        updateUser: (userId, updates) => set((state) => {
          const user = state.users.get(userId);
          if (user) {
            Object.assign(user, updates);
            if (state.currentUser?.id === userId) {
              Object.assign(state.currentUser, updates);
            }
          }
        }),
        
        addUserMeter: (userId, meterId) => set((state) => {
          const user = state.users.get(userId);
          if (user && !user.activeMeters.includes(meterId)) {
            user.activeMeters.push(meterId);
          }
        }),
        
        removeUserMeter: (userId, meterId) => set((state) => {
          const user = state.users.get(userId);
          if (user) {
            user.activeMeters = user.activeMeters.filter(id => id !== meterId);
          }
        }),
        
        // Real-time Connection Actions
        addRealtimeConnection: (connection) => set((state) => {
          const key = `${connection.userId}-${connection.meterId}`;
          state.realtimeConnections.set(key, connection);
        }),
        
        updateConnectionStatus: (userId, meterId, status) => set((state) => {
          const key = `${userId}-${meterId}`;
          const connection = state.realtimeConnections.get(key);
          if (connection) {
            connection.status = status;
            connection.lastHeartbeat = new Date();
          }
        }),
        
        removeRealtimeConnection: (userId, meterId) => set((state) => {
          const key = `${userId}-${meterId}`;
          state.realtimeConnections.delete(key);
        }),
        
        // Performance Actions
        updatePerformanceMetrics: (metrics) => set((state) => {
          Object.assign(state.performance, metrics);
        }),
        
        getSystemHealth: () => {
          const state = get();
          const activeSimulations = Array.from(state.simulations.values());
          const totalErrors = activeSimulations.reduce((sum, sim) => sum + sim.performance.errorRate, 0);
          
          return {
            activeMeterCount: state.performance.activeMeterCount,
            averageLoad: state.performance.averageSimulationLoad,
            errorRate: activeSimulations.length > 0 ? totalErrors / activeSimulations.length : 0,
            throughput: state.performance.hederaTransactionThroughput,
          };
        },
        
        // Bulk Operations
        startMultipleMeterSimulations: async (meterIds) => {
          const { startSimulation } = get();
          await Promise.all(meterIds.map(id => startSimulation(id)));
        },
        
        stopAllSimulations: async () => {
          const { stopSimulation, simulations } = get();
          const meterIds = Array.from(simulations.keys());
          await Promise.all(meterIds.map(id => stopSimulation(id)));
        },
        
        resetAllMeters: () => set((state) => {
          state.meters.clear();
          state.simulations.clear();
          state.consumptionLogs.clear();
          state.performance = {
            activeMeterCount: 0,
            totalLogsGenerated: 0,
            averageSimulationLoad: 0,
            hederaTransactionThroughput: 0,
          };
        }),
        
        // Analytics
        getConsumptionAnalytics: (userId) => {
          const state = get();
          const userMeters = Array.from(state.meters.values()).filter(m => m.userId === userId);
          const totalConsumption = userMeters.reduce((sum, meter) => sum + meter.totalConsumed, 0);
          
          // Calculate analytics from consumption logs
          const allLogs = userMeters.flatMap(meter => state.consumptionLogs.get(meter.id) || []);
          const dailyConsumption = allLogs.reduce((sum, log) => sum + log.consumption_kwh, 0);
          const peakUsage = Math.max(...allLogs.map(log => log.consumption_kwh), 0);
          
          return {
            totalConsumption,
            averageDaily: dailyConsumption / Math.max(allLogs.length, 1),
            peakUsage,
            costEstimate: totalConsumption * 0.12, // $0.12 per kWh estimate
          };
        },
      }))
    ),
    {
      name: 'hedera-flow-store',
      partialize: (state) => ({
        // Persist only essential data
        currentUser: state.currentUser,
        performance: state.performance,
      }),
    }
  )
);

// Selectors for optimized re-renders
export const useCurrentUser = () => useAppStore(state => state.currentUser);
export const useUserMeters = (userId: string) => useAppStore(state => state.getUserMeters(userId));
export const useMeterState = (meterId: string) => useAppStore(state => state.getMeter(meterId));
export const useConsumptionLogs = (meterId: string) => useAppStore(state => state.getConsumptionLogs(meterId));
export const useSystemHealth = () => useAppStore(state => state.getSystemHealth());
export const usePerformanceMetrics = () => useAppStore(state => state.performance);