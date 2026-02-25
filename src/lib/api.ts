import apiClient from './api-client';
import type {
  AuthResponse,
  LoginRequest,
  RegisterRequest,
  User,
  Meter,
  MeterCreateRequest,
  Bill,
  BillBreakdown,
  Payment,
  PaymentReceipt,
  UtilityProvider,
} from '@/types/api';

// Auth API
export const authApi = {
  login: async (data: LoginRequest): Promise<AuthResponse> => {
    const formData = new URLSearchParams();
    formData.append('username', data.email);
    formData.append('password', data.password);
    
    const response = await apiClient.post<AuthResponse>('/auth/login', formData, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    });
    return response.data;
  },

  register: async (data: RegisterRequest): Promise<AuthResponse> => {
    const response = await apiClient.post<AuthResponse>('/auth/register', data);
    return response.data;
  },

  getCurrentUser: async (): Promise<User> => {
    const response = await apiClient.get<User>('/auth/me');
    return response.data;
  },

  logout: () => {
    localStorage.removeItem('auth_token');
    localStorage.removeItem('user');
  },
};

// Meters API
export const metersApi = {
  create: async (data: MeterCreateRequest): Promise<Meter> => {
    const response = await apiClient.post<Meter>('/meters', data);
    return response.data;
  },

  list: async (): Promise<Meter[]> => {
    const response = await apiClient.get<Meter[]>('/meters');
    return response.data;
  },

  get: async (meterId: string): Promise<Meter> => {
    const response = await apiClient.get<Meter>(`/meters/${meterId}`);
    return response.data;
  },

  update: async (meterId: string, data: Partial<MeterCreateRequest>): Promise<Meter> => {
    const response = await apiClient.put<Meter>(`/meters/${meterId}`, data);
    return response.data;
  },

  delete: async (meterId: string): Promise<void> => {
    await apiClient.delete(`/meters/${meterId}`);
  },
};

// Bills API
export const billsApi = {
  list: async (meterId?: string): Promise<Bill[]> => {
    const params = meterId ? { meter_id: meterId } : {};
    const response = await apiClient.get<Bill[]>('/bills', { params });
    return response.data;
  },

  get: async (billId: string): Promise<Bill> => {
    const response = await apiClient.get<Bill>(`/bills/${billId}`);
    return response.data;
  },

  getBreakdown: async (billId: string): Promise<BillBreakdown> => {
    const response = await apiClient.get<BillBreakdown>(`/bills/${billId}/breakdown`);
    return response.data;
  },
};

// Payments API
export const paymentsApi = {
  prepare: async (billId: string): Promise<{ payment_id: string; amount: number }> => {
    const response = await apiClient.post(`/payments/prepare`, { bill_id: billId });
    return response.data;
  },

  confirm: async (paymentId: string, transactionId: string): Promise<Payment> => {
    const response = await apiClient.post<Payment>(`/payments/confirm`, {
      payment_id: paymentId,
      hedera_transaction_id: transactionId,
    });
    return response.data;
  },

  get: async (paymentId: string): Promise<Payment> => {
    const response = await apiClient.get<Payment>(`/payments/${paymentId}`);
    return response.data;
  },

  getReceipt: async (paymentId: string): Promise<PaymentReceipt> => {
    const response = await apiClient.get<PaymentReceipt>(`/payments/${paymentId}/receipt`);
    return response.data;
  },

  list: async (): Promise<Payment[]> => {
    const response = await apiClient.get<Payment[]>('/payments');
    return response.data;
  },
};

// Utility Providers API
export const utilityProvidersApi = {
  list: async (countryCode?: string, stateProvince?: string): Promise<UtilityProvider[]> => {
    const params: Record<string, string> = {};
    if (countryCode) params.country_code = countryCode;
    if (stateProvince) params.state_province = stateProvince;
    
    const response = await apiClient.get<UtilityProvider[]>('/utility-providers', { params });
    return response.data;
  },

  get: async (providerId: string): Promise<UtilityProvider> => {
    const response = await apiClient.get<UtilityProvider>(`/utility-providers/${providerId}`);
    return response.data;
  },
};

// Verification API (OCR meter scanning)
export const verificationApi = {
  scanMeter: async (imageFile: File): Promise<{ reading: number; confidence: number }> => {
    const formData = new FormData();
    formData.append('image', imageFile);
    
    const response = await apiClient.post('/verify/scan', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },
};

// Health check
export const healthApi = {
  check: async (): Promise<{ status: string; timestamp: string }> => {
    const response = await apiClient.get('/health');
    return response.data;
  },
};
