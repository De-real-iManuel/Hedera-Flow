import apiClient from '../api-client';

export interface SmartMeterKeypair {
  meter_id: string;
  public_key: string;
  algorithm: string;
  created_at: string;
  kms_key_id?: string;
}

export interface ConsumptionLog {
  consumption_log_id: string;
  meter_id: string;
  consumption_kwh: number;
  timestamp: number;
  signature_valid: boolean;
  reading_before?: number;
  reading_after?: number;
  units_deducted?: number;
  units_remaining?: number;
  hcs_topic_id?: string;
  hcs_sequence_number?: number;
  token_deduction?: Record<string, unknown>;
}

export interface ConsumptionRequest {
  meter_id: string;
  consumption_kwh: number;
  timestamp: number;
  signature: string;
  public_key: string;
  reading_before?: number;
  reading_after?: number;
}

export interface SignConsumptionRequest {
  meter_id: string;
  consumption_kwh: number;
  timestamp: number;
  reading_before?: number;
  reading_after?: number;
}

export interface SignConsumptionResponse {
  meter_id: string;
  consumption_kwh: number;
  timestamp: number;
  signature: string;
  public_key: string;
  message_hash: string;
  reading_before?: number;
  reading_after?: number;
}

export interface SignatureVerificationRequest {
  meter_id: string;
  consumption_kwh: number;
  timestamp: number;
  signature: string;
  public_key?: string;
}

export interface SignatureVerificationResult {
  valid: boolean;
  meter_id: string;
  consumption_kwh: number;
  timestamp: number;
  message_hash: string;
  algorithm: string;
  error?: string;
}

export interface SimulatorState {
  running: boolean;
  meter_id: string;
  current_reading: number;
  last_logged_reading: number;
  total_consumed: number;
  logs_count: number;
  consumption_rate?: number;
  started_at?: string;
  last_log_at?: string | null;
}

export interface SimulatorTickResponse {
  state: SimulatorState;
  auto_logged: {
    consumption_log_id: string;
    consumption_kwh: number;
    hcs_sequence_number?: number;
  } | null;
}

export const smartMeterApi = {
  generateKeypair: async (meterId: string): Promise<SmartMeterKeypair> => {
    const res = await apiClient.post<SmartMeterKeypair>('/smart-meter/generate-keypair', { meter_id: meterId });
    return res.data;
  },

  getPublicKey: async (meterId: string): Promise<string> => {
    const res = await apiClient.get<{ public_key: string }>(`/smart-meter/public-key/${meterId}`);
    return res.data.public_key;
  },

  signConsumption: async (data: SignConsumptionRequest): Promise<SignConsumptionResponse> => {
    const res = await apiClient.post<SignConsumptionResponse>('/smart-meter/sign', data);
    return res.data;
  },

  logConsumption: async (data: ConsumptionRequest): Promise<ConsumptionLog> => {
    const res = await apiClient.post<ConsumptionLog>('/smart-meter/consume', data);
    return res.data;
  },

  verifySignature: async (data: SignatureVerificationRequest): Promise<SignatureVerificationResult> => {
    const res = await apiClient.post<SignatureVerificationResult>('/smart-meter/verify-signature', data);
    return res.data;
  },

  getConsumptionHistory: async (meterId: string, limit = 10): Promise<ConsumptionLog[]> => {
    const res = await apiClient.get<ConsumptionLog[]>(`/smart-meter/consumption-history/${meterId}?limit=${limit}`);
    return res.data;
  },

  getConsumptionLogs: async (meterId: string, limit = 50): Promise<{ logs: ConsumptionLog[]; total: number }> => {
    const res = await apiClient.get<{ logs: ConsumptionLog[]; total: number }>(`/smart-meter/consumption-logs?meter_id=${meterId}&limit=${limit}`);
    return res.data;
  },

  // Simulator API
  startSimulator: async (meterId: string): Promise<SimulatorState> => {
    const res = await apiClient.post<SimulatorState>('/smart-meter/simulator/start', { meter_id: meterId });
    return res.data;
  },

  stopSimulator: async (meterId: string): Promise<SimulatorState> => {
    const res = await apiClient.post<SimulatorState>('/smart-meter/simulator/stop', { meter_id: meterId });
    return res.data;
  },

  getSimulatorStatus: async (meterId: string): Promise<SimulatorState> => {
    const res = await apiClient.get<SimulatorState>(`/smart-meter/simulator/status/${meterId}`);
    return res.data;
  },

  tickSimulator: async (meterId: string, seconds = 5): Promise<SimulatorTickResponse> => {
    const res = await apiClient.post<SimulatorTickResponse>('/smart-meter/simulator/tick', {
      meter_id: meterId,
      seconds,
    });
    return res.data;
  },
};
