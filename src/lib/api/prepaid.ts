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
  sts_token?: string | null;
  user_id: string;
  meter_id: string;
  amount_paid_fiat: number;
  currency: string;
  amount_paid_hbar: number | null;
  units_purchased: number;
  units_remaining: number;
  tariff_rate: number;
  exchange_rate: number;
  status: 'active' | 'low' | 'depleted' | 'expired' | 'cancelled';
  hedera_tx_id: string | null;
  hedera_consensus_timestamp?: string | null;
  hcs_topic_id?: string | null;
  hcs_sequence_number?: number | null;
  issued_at: string;
  expires_at: string;
  depleted_at?: string | null;
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
  transaction: {
    from: string;
    to: string;
    amount_hbar?: number;
    amount_usdc?: number;
    memo: string;
  };
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
  confirm: async (tokenId: string, hederaTxId: string): Promise<BuyTokenResponse> => {
    const formData = new FormData();
    formData.append('token_id', tokenId);
    formData.append('hedera_tx_id', hederaTxId);
    
    const response = await apiClient.post<BuyTokenResponse>('/prepaid/confirm-payment', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
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
  listTokens: async (params?: {
    meterId?: string;
    status?: string;
    dateFrom?: string;
    dateTo?: string;
    limit?: number;
    offset?: number;
  }): Promise<PrepaidToken[]> => {
    const queryParams = new URLSearchParams();
    
    if (params?.meterId) queryParams.append('meter_id', params.meterId);
    if (params?.status) queryParams.append('status', params.status);
    if (params?.dateFrom) queryParams.append('date_from', params.dateFrom);
    if (params?.dateTo) queryParams.append('date_to', params.dateTo);
    if (params?.limit) queryParams.append('limit', params.limit.toString());
    if (params?.offset) queryParams.append('offset', params.offset.toString());
    
    const response = await apiClient.get<PrepaidToken[]>(`/prepaid/tokens?${queryParams}`);
    return response.data;
  },

  // Get receipt for a token
  getReceipt: async (tokenId: string, format: 'html' | 'text' | 'json' = 'html'): Promise<string | object> => {
    const response = await apiClient.get(`/prepaid/tokens/${tokenId}/receipt?format=${format}`);
    return response.data;
  },

  // Email receipt for a token
  emailReceipt: async (tokenId: string, emailAddress: string): Promise<{ message: string; sent_at: string }> => {
    const formData = new FormData();
    formData.append('email_address', emailAddress);
    
    const response = await apiClient.post(`/prepaid/tokens/${tokenId}/receipt/email`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },
};
