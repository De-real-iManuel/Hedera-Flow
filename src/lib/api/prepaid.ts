import apiClient from '../api-client';

export interface PrepaidTokenPreview {
  amount_fiat: number;
  currency: string;
  amount_hbar: number;
  units_kwh: number;
  exchange_rate: number;
  tariff_rate: number;
}

export interface PrepaidToken {
  id: string;
  token_id: string;
  user_id: string;
  meter_id: string;
  amount_fiat: number;
  currency: string;
  amount_hbar: number;
  units_purchased: number;
  units_remaining: number;
  tariff_rate: number;
  exchange_rate: number;
  status: 'active' | 'low' | 'depleted';
  hedera_tx_id: string;
  hcs_sequence_number?: number;
  expires_at: string;
  created_at: string;
  updated_at: string;
}

export interface PrepaidBalance {
  meter_id: string;
  total_units: number;
  active_tokens: number;
  low_balance_alert: boolean;
  tokens: PrepaidToken[];
}

export interface BuyTokenRequest {
  meter_id: string;
  amount_fiat: number;
  currency: string;
  payment_method: 'HBAR';
}

export interface BuyTokenResponse {
  token: PrepaidToken;
  message: string;
  hcs_topic_id: string;
}

export const prepaidApi = {
  // Get preview of token purchase
  preview: async (meterId: string, amountFiat: number, currency: string): Promise<PrepaidTokenPreview> => {
    const response = await apiClient.post<PrepaidTokenPreview>('/prepaid/preview', {
      meter_id: meterId,
      amount_fiat: amountFiat,
      currency: currency,
    });
    return response.data;
  },

  // Buy prepaid token
  buy: async (data: BuyTokenRequest): Promise<BuyTokenResponse> => {
    const response = await apiClient.post<BuyTokenResponse>('/prepaid/buy', data);
    return response.data;
  },

  // Confirm token purchase with Hedera transaction ID
  confirm: async (meterId: string, hederaTxId: string): Promise<BuyTokenResponse> => {
    const response = await apiClient.post<BuyTokenResponse>('/prepaid/confirm', {
      meter_id: meterId,
      hedera_tx_id: hederaTxId,
    });
    return response.data;
  },

  // Get prepaid balance for a meter
  getBalance: async (meterId: string): Promise<PrepaidBalance> => {
    const response = await apiClient.get<PrepaidBalance>(`/prepaid/balance/${meterId}`);
    return response.data;
  },

  // Get specific token details
  getToken: async (tokenId: string): Promise<PrepaidToken> => {
    const response = await apiClient.get<PrepaidToken>(`/prepaid/tokens/${tokenId}`);
    return response.data;
  },

  // List all tokens for current user
  listTokens: async (meterId?: string): Promise<PrepaidToken[]> => {
    const params = meterId ? { meter_id: meterId } : {};
    const response = await apiClient.get<PrepaidToken[]>('/prepaid/tokens', { params });
    return response.data;
  },
};
