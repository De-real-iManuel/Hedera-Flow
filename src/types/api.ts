// API Response Types

export interface User {
  id: string;
  email: string;
  country_code: string;
  hedera_account_id: string | null;
  wallet_type: string | null;
  created_at: string;
  last_login: string | null;
  is_active: boolean;
}

export interface AuthResponse {
  token: string;
  user: User;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  country_code: string;
  hedera_account_id?: string;
}

export interface Meter {
  id: string;
  user_id: string;
  meter_id: string;
  utility_provider_id: string;
  state_province: string;
  utility_provider: string;
  meter_type: 'prepaid' | 'postpaid';
  band_classification?: string;
  address?: string;
  is_primary: boolean;
  created_at: string;
  updated_at: string;
}

export interface MeterCreateRequest {
  meter_id: string;
  utility_provider_id: string;
  state_province: string;
  utility_provider: string;
  meter_type: 'prepaid' | 'postpaid';
  band_classification?: string;
  address?: string;
  is_primary: boolean;
}

export interface Bill {
  id: string;
  meter_id: string;
  billing_period_start: string;
  billing_period_end: string;
  reading_previous: number;
  reading_current: number;
  consumption_kwh: number;
  amount_due: number;
  currency: string;
  due_date: string;
  status: 'pending' | 'paid' | 'overdue' | 'disputed';
  created_at: string;
  updated_at: string;
}

export interface BillBreakdown {
  energy_charge: number;
  service_charge: number;
  vat: number;
  total: number;
  tariff_details: {
    tier: string;
    kwh: number;
    rate: number;
    amount: number;
  }[];
}

export interface Payment {
  id: string;
  bill_id: string;
  user_id: string;
  amount: number;
  currency: string;
  hedera_transaction_id: string;
  status: 'pending' | 'confirmed' | 'failed';
  payment_method: string;
  created_at: string;
  confirmed_at?: string;
}

export interface PaymentReceipt {
  payment: Payment;
  bill: Bill;
  reference_number: string;
}

export interface UtilityProvider {
  id: string;
  name: string;
  country_code: string;
  state_province: string;
  is_active: boolean;
}

export interface ApiError {
  detail: string;
  status_code: number;
}
