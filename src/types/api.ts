// API Response Types

export interface User {
  id: string;
  first_name?: string | null;
  last_name?: string | null;
  email: string;
  country_code: string;
  hedera_account_id: string | null;
  wallet_type: string | null;
  created_at: string;
  last_login: string | null;
  is_active: boolean;
  access_token?: string | null; // included in auth responses as cookie fallback
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
  first_name: string;
  last_name: string;
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
  id: string;
  bill_id: string;
  amount_hbar: number;
  amount_fiat: number;
  currency: string;
  exchange_rate: number;
  hedera_tx_id: string;
  consensus_timestamp: string;
  receipt_url: string;
  created_at: string;
}

export interface UtilityProvider {
  id: string;
  name: string;
  provider_name: string;
  country_code: string;
  state_province: string;
  is_active: boolean;
}

export interface ExchangeRate {
  currency: string;
  hbarPrice: number;
  source: string;
  fetchedAt: string;
}

export interface ApiError {
  detail: string;
  status_code: number;
}

export interface VerificationResponse {
  id: string;
  user_id: string;
  meter_id: string;
  reading_value: number;
  previous_reading?: number;
  consumption_kwh?: number;
  image_ipfs_hash: string;
  ocr_engine: 'tesseract' | 'google_vision';
  confidence: number;
  raw_ocr_text?: string;
  fraud_score: number;
  fraud_flags?: Record<string, any>;
  utility_reading?: number;
  utility_api_response?: Record<string, any>;
  status: 'VERIFIED' | 'WARNING' | 'DISCREPANCY' | 'FRAUD_DETECTED';
  hcs_topic_id: string;
  hcs_sequence_number: number;
  hcs_timestamp?: string;
  created_at: string;
  bill?: BillSummary;
}

export interface BillSummary {
  id: string;
  total_fiat: number;
  currency: string;
  amount_hbar?: number;
  exchange_rate?: number;
}
