/**
 * Real-time Service
 * 
 * Handles real-time updates for multi-user smart meter simulations:
 * - WebSocket connections for live updates
 * - Room-based broadcasting for user isolation
 * - Fallback to polling for reliability
 * - Performance optimization for concurrent users
 */

import { useAppStore } from '@/stores/app-store';
import type { ConsumptionLog } from '@/lib/api/smart-meter';

export interface RealtimeUpdate {
  type: 'METER_UPDATE' | 'CONSUMPTION_LOG' | 'FRAUD_ALERT' | 'SYSTEM_STATUS';
  meterId: string;
  userId: string;
  timestamp: string;
  data: any;
}

export interface MeterUpdate {
  currentReading: number;
  consumptionRate: number;
  timestamp: string;
  status?: string;
}

export interface RoomSubscription {
  userId: string;
  meterId: string;
  callback: (update: RealtimeUpdate) => void;
  lastHeartbeat: Date;
}

export class RealtimeService {
  private websockets: Map<string, WebSocket> = new Map();
  private subscriptions: Map<string, RoomSubscription[]> = new Map();
  private pollingIntervals: Map<string, NodeJS.Timeout> = new Map();
  private heartbeatInterval?: NodeJS.Timeout;
  private store = useAppStore.getState();
  
  // Configuration
  private readonly WS_URL = process.env.VITE_WS_URL || 'ws://localhost:8001/ws';
  private readonly HEARTBEAT_INTERVAL = 30000; // 30 seconds
  private readonly RECONNECT_DELAY = 5000; // 5 seconds
  private readonly MAX_RECONNECT_ATTEMPTS = 5;

  constructor() {
    this.startHeartbeat();
  }

  /**
   * Subscribe to real-time updates for a meter
   */
  async subscribeToMeter(
    userId: string,
    meterId: string,
    callback: (update: RealtimeUpdate) => void
  ): Promise<void> {
    try {
      const roomKey = `meter:${meterId}`;
      const subscription: RoomSubscription = {
        userId,
        meterId,
        callback,
        lastHeartbeat: new Date(),
      };

      // Add to subscriptions
      const roomSubscriptions = this.subscriptions.get(roomKey) || [];
      roomSubscriptions.push(subscription);
      this.subscriptions.set(roomKey, roomSubscriptions);

      // Try WebSocket connection first
      await this.connectWebSocket(userId, meterId);

      // Fallback to polling if WebSocket fails
      if (!this.websockets.has(`${userId}:${meterId}`)) {
        this.startPolling(userId, meterId, callback);
      }

      // Update store
      this.store.addRealtimeConnection({
        userId,
        meterId,
        status: 'connected',
        lastHeartbeat: new Date(),
      });

      console.log(`✅ Subscribed to real-time updates for meter ${meterId} (user: ${userId})`);

    } catch (error) {
      console.error(`Failed to subscribe to meter ${meterId}:`, error);
      // Fallback to polling
      this.startPolling(userId, meterId, callback);
    }
  }

  /**
   * Unsubscribe from meter updates
   */
  async unsubscribeFromMeter(userId: string, meterId: string): Promise<void> {
    try {
      const roomKey = `meter:${meterId}`;
      const wsKey = `${userId}:${meterId}`;

      // Remove subscription
      const roomSubscriptions = this.subscriptions.get(roomKey) || [];
      const filteredSubscriptions = roomSubscriptions.filter(
        sub => !(sub.userId === userId && sub.meterId === meterId)
      );
      
      if (filteredSubscriptions.length > 0) {
        this.subscriptions.set(roomKey, filteredSubscriptions);
      } else {
        this.subscriptions.delete(roomKey);
      }

      // Close WebSocket if exists
      const ws = this.websockets.get(wsKey);
      if (ws) {
        ws.close();
        this.websockets.delete(wsKey);
      }

      // Stop polling
      const pollingInterval = this.pollingIntervals.get(wsKey);
      if (pollingInterval) {
        clearInterval(pollingInterval);
        this.pollingIntervals.delete(wsKey);
      }

      // Update store
      this.store.removeRealtimeConnection(userId, meterId);

      console.log(`✅ Unsubscribed from meter ${meterId} (user: ${userId})`);

    } catch (error) {
      console.error(`Failed to unsubscribe from meter ${meterId}:`, error);
    }
  }

  /**
   * Broadcast meter update to all subscribers
   */
  broadcastMeterUpdate(meterId: string, update: MeterUpdate): void {
    const roomKey = `meter:${meterId}`;
    const subscriptions = this.subscriptions.get(roomKey) || [];

    const realtimeUpdate: RealtimeUpdate = {
      type: 'METER_UPDATE',
      meterId,
      userId: '', // Will be set per subscriber
      timestamp: update.timestamp,
      data: update,
    };

    subscriptions.forEach(subscription => {
      try {
        realtimeUpdate.userId = subscription.userId;
        subscription.callback(realtimeUpdate);
        subscription.lastHeartbeat = new Date();
      } catch (error) {
        console.error(`Failed to broadcast to user ${subscription.userId}:`, error);
      }
    });
  }

  /**
   * Broadcast consumption log to subscribers
   */
  broadcastConsumptionLog(meterId: string, log: ConsumptionLog): void {
    const roomKey = `meter:${meterId}`;
    const subscriptions = this.subscriptions.get(roomKey) || [];

    const realtimeUpdate: RealtimeUpdate = {
      type: 'CONSUMPTION_LOG',
      meterId,
      userId: '', // Will be set per subscriber
      timestamp: log.timestamp,
      data: log,
    };

    subscriptions.forEach(subscription => {
      try {
        realtimeUpdate.userId = subscription.userId;
        subscription.callback(realtimeUpdate);
      } catch (error) {
        console.error(`Failed to broadcast consumption log to user ${subscription.userId}:`, error);
      }
    });
  }

  /**
   * Start broadcasting for a meter
   */
  async startMeterBroadcast(meterId: string): Promise<void> {
    // Broadcasting is handled by individual subscriptions
    console.log(`📡 Started broadcasting for meter ${meterId}`);
  }

  /**
   * Stop broadcasting for a meter
   */
  async stopMeterBroadcast(meterId: string): Promise<void> {
    const roomKey = `meter:${meterId}`;
    const subscriptions = this.subscriptions.get(roomKey) || [];

    // Notify all subscribers that broadcasting stopped
    const stopUpdate: RealtimeUpdate = {
      type: 'SYSTEM_STATUS',
      meterId,
      userId: '',
      timestamp: new Date().toISOString(),
      data: { status: 'BROADCAST_STOPPED' },
    };

    subscriptions.forEach(subscription => {
      try {
        stopUpdate.userId = subscription.userId;
        subscription.callback(stopUpdate);
      } catch (error) {
        console.error(`Failed to notify user ${subscription.userId}:`, error);
      }
    });

    console.log(`📡 Stopped broadcasting for meter ${meterId}`);
  }

  /**
   * Connect WebSocket for real-time updates
   */
  private async connectWebSocket(userId: string, meterId: string): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        const wsKey = `${userId}:${meterId}`;
        const wsUrl = `${this.WS_URL}/meter/${meterId}?userId=${userId}`;
        
        const ws = new WebSocket(wsUrl);
        let reconnectAttempts = 0;

        ws.onopen = () => {
          console.log(`🔌 WebSocket connected for meter ${meterId}`);
          this.websockets.set(wsKey, ws);
          this.store.updateConnectionStatus(userId, meterId, 'connected');
          resolve();
        };

        ws.onmessage = (event) => {
          try {
            const update: RealtimeUpdate = JSON.parse(event.data);
            this.handleWebSocketMessage(update);
          } catch (error) {
            console.error('Failed to parse WebSocket message:', error);
          }
        };

        ws.onclose = () => {
          console.log(`🔌 WebSocket disconnected for meter ${meterId}`);
          this.websockets.delete(wsKey);
          this.store.updateConnectionStatus(userId, meterId, 'disconnected');
          
          // Attempt reconnection
          if (reconnectAttempts < this.MAX_RECONNECT_ATTEMPTS) {
            reconnectAttempts++;
            setTimeout(() => {
              this.connectWebSocket(userId, meterId);
            }, this.RECONNECT_DELAY);
          }
        };

        ws.onerror = (error) => {
          console.error(`WebSocket error for meter ${meterId}:`, error);
          reject(error);
        };

        // Timeout for connection
        setTimeout(() => {
          if (ws.readyState !== WebSocket.OPEN) {
            ws.close();
            reject(new Error('WebSocket connection timeout'));
          }
        }, 10000);

      } catch (error) {
        reject(error);
      }
    });
  }

  /**
   * Handle incoming WebSocket messages
   */
  private handleWebSocketMessage(update: RealtimeUpdate): void {
    const roomKey = `meter:${update.meterId}`;
    const subscriptions = this.subscriptions.get(roomKey) || [];

    subscriptions.forEach(subscription => {
      if (subscription.userId === update.userId) {
        try {
          subscription.callback(update);
          subscription.lastHeartbeat = new Date();
        } catch (error) {
          console.error(`Failed to handle WebSocket message for user ${subscription.userId}:`, error);
        }
      }
    });
  }

  /**
   * Start polling fallback for unreliable connections
   */
  private startPolling(
    userId: string,
    meterId: string,
    callback: (update: RealtimeUpdate) => void
  ): void {
    const wsKey = `${userId}:${meterId}`;
    
    // Don't start polling if already exists
    if (this.pollingIntervals.has(wsKey)) {
      return;
    }

    console.log(`🔄 Starting polling fallback for meter ${meterId}`);

    const interval = setInterval(async () => {
      try {
        // Get current meter state
        const meter = this.store.getMeter(meterId);
        if (!meter) return;

        // Create update from current state
        const update: RealtimeUpdate = {
          type: 'METER_UPDATE',
          meterId,
          userId,
          timestamp: new Date().toISOString(),
          data: {
            currentReading: meter.currentReading,
            consumptionRate: meter.consumptionRate,
            status: meter.status,
          },
        };

        callback(update);

      } catch (error) {
        console.error(`Polling error for meter ${meterId}:`, error);
      }
    }, 5000); // Poll every 5 seconds

    this.pollingIntervals.set(wsKey, interval);
    this.store.updateConnectionStatus(userId, meterId, 'connected');
  }

  /**
   * Start heartbeat to maintain connections
   */
  private startHeartbeat(): void {
    this.heartbeatInterval = setInterval(() => {
      const now = new Date();
      
      // Check all subscriptions for stale connections
      this.subscriptions.forEach((subscriptions, roomKey) => {
        const activeSubscriptions = subscriptions.filter(sub => {
          const timeSinceHeartbeat = now.getTime() - sub.lastHeartbeat.getTime();
          return timeSinceHeartbeat < this.HEARTBEAT_INTERVAL * 2; // 2x heartbeat interval
        });

        if (activeSubscriptions.length !== subscriptions.length) {
          console.log(`🧹 Cleaned up ${subscriptions.length - activeSubscriptions.length} stale subscriptions for ${roomKey}`);
          this.subscriptions.set(roomKey, activeSubscriptions);
        }
      });

      // Send heartbeat to active WebSocket connections
      this.websockets.forEach((ws, key) => {
        if (ws.readyState === WebSocket.OPEN) {
          try {
            ws.send(JSON.stringify({ type: 'HEARTBEAT', timestamp: now.toISOString() }));
          } catch (error) {
            console.error(`Failed to send heartbeat to ${key}:`, error);
          }
        }
      });

    }, this.HEARTBEAT_INTERVAL);
  }

  /**
   * Get real-time service status
   */
  getStatus(): {
    activeConnections: number;
    activeSubscriptions: number;
    pollingConnections: number;
    websocketConnections: number;
    totalRooms: number;
  } {
    const totalSubscriptions = Array.from(this.subscriptions.values())
      .reduce((sum, subs) => sum + subs.length, 0);

    return {
      activeConnections: totalSubscriptions,
      activeSubscriptions: totalSubscriptions,
      pollingConnections: this.pollingIntervals.size,
      websocketConnections: this.websockets.size,
      totalRooms: this.subscriptions.size,
    };
  }

  /**
   * Clean up all connections and resources
   */
  async cleanup(): Promise<void> {
    // Clear heartbeat
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
    }

    // Close all WebSocket connections
    this.websockets.forEach((ws, key) => {
      try {
        ws.close();
      } catch (error) {
        console.error(`Failed to close WebSocket ${key}:`, error);
      }
    });
    this.websockets.clear();

    // Clear all polling intervals
    this.pollingIntervals.forEach((interval, key) => {
      clearInterval(interval);
    });
    this.pollingIntervals.clear();

    // Clear subscriptions
    this.subscriptions.clear();

    console.log('🧹 Real-time service cleaned up');
  }
}