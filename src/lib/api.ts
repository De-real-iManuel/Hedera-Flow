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
  ExchangeRate,
  VerificationResponse,
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

  walletConnect: async (data: {
    hedera_account_id: string;
    signature: string;
    message: string;
  }): Promise<AuthResponse> => {
    const response = await apiClient.post<AuthResponse>('/auth/wallet-connect', data);
    return response.data;
  },

  getCurrentUser: async (): Promise<User> => {
    // Check if user is stored in localStorage (temporary until JWT middleware is integrated)
    const storedUser = localStorage.getItem('user');
    if (storedUser) {
      return JSON.parse(storedUser);
    }
    
    // If no stored user, try to fetch from backend (will fail until JWT middleware is integrated)
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
  prepare: async (billId: string): Promise<{
    bill: {
      id: string;
      total_fiat: number;
      currency: string;
      consumption_kwh: number;
    };
    transaction: {
      from: string;
      to: string;
      amount_hbar: number;
      memo: string;
    };
    exchange_rate: {
      currency: string;
      hbar_price: number;
      source: string;
      fetched_at: string;
      expires_at: string;
    };
    minimum_hbar: number;
  }> => {
    const response = await apiClient.post(`/payments/prepare`, { bill_id: billId });
    return response.data;
  },

  confirm: async (billId: string, hederaTxId: string): Promise<{
    payment: PaymentReceipt;
    message: string;
  }> => {
    const response = await apiClient.post(`/payments/confirm`, {
      bill_id: billId,
      hedera_tx_id: hederaTxId,
    });
    return response.data;
  },

  get: async (paymentId: string): Promise<PaymentReceipt> => {
    const response = await apiClient.get<PaymentReceipt>(`/payments/${paymentId}`);
    return response.data;
  },

  getReceipt: async (paymentId: string): Promise<PaymentReceipt> => {
    const response = await apiClient.get<PaymentReceipt>(`/payments/${paymentId}/receipt`);
    return response.data;
  },

  list: async (): Promise<PaymentReceipt[]> => {
    const response = await apiClient.get<PaymentReceipt[]>('/payments');
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
  scanMeter: async (meterId: string, imageFile: File, ocrReading?: number, ocrConfidence?: number): Promise<VerificationResponse> => {
    const formData = new FormData();
    formData.append('meter_id', meterId);
    formData.append('image', imageFile);
    
    if (ocrReading !== undefined) {
      formData.append('ocr_reading', ocrReading.toString());
    }
    if (ocrConfidence !== undefined) {
      formData.append('ocr_confidence', ocrConfidence.toString());
    }
    
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

// Exchange Rate API
export const exchangeRateApi = {
  get: async (currency: string): Promise<ExchangeRate> => {
    const response = await apiClient.get<ExchangeRate>(`/exchange-rate/${currency.toUpperCase()}`);
    return response.data;
  },
};

// Prepaid API
export { prepaidApi } from './api/prepaid';

// User Profile API
export interface NotificationPreferences {
  bill_reminders: boolean;
  payment_confirmations: boolean;
  subsidy_updates: boolean;
  email_notifications: boolean;
  push_notifications: boolean;
}

export interface UserPreferences {
  theme: string;
  language: string;
  currency_display: string;
  notifications: NotificationPreferences;
}

export interface SecuritySettings {
  biometric_enabled: boolean;
  pin_enabled: boolean;
  two_factor_enabled: boolean;
}

export interface UserProfile {
  id: string;
  email: string;
  first_name?: string;
  last_name?: string;
  country_code: string;
  hedera_account_id?: string;
  wallet_type?: string;
  created_at: string;
  last_login?: string;
  is_active: boolean;
  preferences: UserPreferences;
  security: SecuritySettings;
}

export interface UpdateProfileRequest {
  first_name?: string;
  last_name?: string;
  email?: string;
}

export const userApi = {
  getProfile: async (): Promise<UserProfile> => {
    const response = await apiClient.get<UserProfile>('/user/profile');
    return response.data;
  },

  updateProfile: async (data: UpdateProfileRequest): Promise<UserProfile> => {
    const response = await apiClient.put<UserProfile>('/user/profile', data);
    return response.data;
  },

  getPreferences: async (): Promise<UserPreferences> => {
    const response = await apiClient.get<UserPreferences>('/user/preferences');
    return response.data;
  },

  updatePreferences: async (preferences: UserPreferences): Promise<UserPreferences> => {
    const response = await apiClient.put<UserPreferences>('/user/preferences', preferences);
    return response.data;
  },

  getNotifications: async (): Promise<NotificationPreferences> => {
    const response = await apiClient.get<NotificationPreferences>('/user/notifications');
    return response.data;
  },

  updateNotifications: async (notifications: NotificationPreferences): Promise<NotificationPreferences> => {
    const response = await apiClient.put<NotificationPreferences>('/user/notifications', notifications);
    return response.data;
  },

  getSecurity: async (): Promise<SecuritySettings> => {
    const response = await apiClient.get<SecuritySettings>('/user/security');
    return response.data;
  },

  updateSecurity: async (security: SecuritySettings): Promise<SecuritySettings> => {
    const response = await apiClient.put<SecuritySettings>('/user/security', security);
    return response.data;
  },
};
