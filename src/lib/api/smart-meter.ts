import apiClient from '../api-client';

export interface SmartMeterKeypair {
  meter_id: string;
  public_key: string;
  algorithm: string;
  created_at: string;
}

export interface ConsumptionLog {
  id: string;
  meter_id: string;
  consumption_kwh: number;
  timestamp: string;
  signature: string;
  signature_valid: boolean;
  reading_before: number;
  reading_after: number;
  units_deducted?: number;
  units_remaining?: number;
  hcs_topic_id?: string;
  hcs_sequence_number?: number;
}

export interface ConsumptionRequest {
  meter_id: string;
  consumption_kwh: number;
  timestamp: string;
  signature: string;
  public_key: string;
  reading_before: number;
  reading_after: number;
}

export interface SignatureVerificationRequest {
  meter_id: string;
  consumption_kwh: number;
  timestamp: string;
  signature: string;
  public_key: string;
}

export interface SignatureVerificationResult {
  valid: boolean;
  meter_id: string;
  consumption_kwh: number;
  timestamp: string;
  signature: string;
  algorithm: string;
  error?: string;
}

export interface ConsumptionHistory {
  logs: ConsumptionLog[];
  total_consumption: number;
  average_daily: number;
  peak_consumption: number;
  total_cost: number;
}

export const smartMeterApi = {
  // Generate keypair for a meter
  generateKeypair: async (meterId: string): Promise<SmartMeterKeypair> => {
    const response = await apiClient.post<SmartMeterKeypair>('/smart-meter/generate-keypair', {
      meter_id: meterId,
    });
    return response.data;
  },

  // Get public key for a meter
  getPublicKey: async (meterId: string): Promise<string> => {
    const response = await apiClient.get<{ public_key: string }>(`/smart-meter/public-key/${meterId}`);
    return response.data.public_key;
  },

  // Log consumption data
  logConsumption: async (data: ConsumptionRequest): Promise<ConsumptionLog> => {
    const response = await apiClient.post<ConsumptionLog>('/smart-meter/consume', data);
    return response.data;
  },

  // Verify signature
  verifySignature: async (data: SignatureVerificationRequest): Promise<SignatureVerificationResult> => {
    const response = await apiClient.post<SignatureVerificationResult>('/smart-meter/verify-signature', data);
    return response.data;
  },

  // Get consumption logs for a meter
  getConsumptionLogs: async (meterId: string, limit?: number, offset?: number): Promise<ConsumptionLog[]> => {
    const params = new URLSearchParams();
    if (limit) params.append('limit', limit.toString());
    if (offset) params.append('offset', offset.toString());
    
    const response = await apiClient.get<ConsumptionLog[]>(`/smart-meter/consumption-logs/${meterId}?${params}`);
    return response.data;
  },

  // Get consumption history with analytics
  getConsumptionHistory: async (
    meterId: string, 
    dateFrom?: string, 
    dateTo?: string
  ): Promise<ConsumptionHistory> => {
    const params = new URLSearchParams();
    if (dateFrom) params.append('date_from', dateFrom);
    if (dateTo) params.append('date_to', dateTo);
    
    const response = await apiClient.get<ConsumptionHistory>(`/smart-meter/consumption-history/${meterId}?${params}`);
    return response.data;
  },
};