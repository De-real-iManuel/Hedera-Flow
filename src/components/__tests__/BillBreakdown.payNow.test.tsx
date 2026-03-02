import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BillBreakdown, type BillBreakdownData } from '../BillBreakdown';
import * as hashpackModule from '@/lib/hashpack';
import * as apiModule from '@/lib/api';

// Mock the hashpack module
vi.mock('@/lib/hashpack', () => ({
  useHashPack: vi.fn(),
  hashPackWallet: {
    connect: vi.fn(),
    executePayment: vi.fn(),
    checkBalance: vi.fn(),
    disconnect: vi.fn(),
  },
}));

// Mock the API module
vi.mock('@/lib/api', () => ({
  exchangeRateApi: {
    get: vi.fn(),
  },
}));

// Mock sonner toast
vi.mock('sonner', () => ({
  toast: {
    error: vi.fn(),
    success: vi.fn(),
    info: vi.fn(),
  },
}));

describe('BillBreakdown - Pay Now Button', () => {
  const mockBillData: BillBreakdownData = {
    consumptionKwh: 500,
    baseCharge: 70.5,
    taxes: 14.9,
    totalFiat: 85.4,
    currency: 'EUR',
    rateStructureType: 'flat',
  };

  const mockExchangeRate = {
    currency: 'EUR',
    hbarPrice: 0.34,
    source: 'coingecko',
    fetchedAt: new Date().toISOString(),
  };

  const mockHashPack = {
    connect: vi.fn(),
    executePayment: vi.fn(),
    checkBalance: vi.fn(),
    disconnect: vi.fn(),
    isInstalled: vi.fn(() => true),
  };

  beforeEach(() => {
    vi.clearAllMocks();
    
    // Setup default mocks
    vi.mocked(hashpackModule.useHashPack).mockReturnValue(mockHashPack);
    vi.mocked(apiModule.exchangeRateApi.get).mockResolvedValue(mockExchangeRate);
    
    mockHashPack.connect.mockResolvedValue('0.0.123456');
    mockHashPack.checkBalance.mockResolvedValue(1000);
    mockHashPack.executePayment.mockResolvedValue({
      success: true,
      transactionId: '0.0.999999@1234567890.123',
    });
  });

  it('should render Pay Now button when billId is provided', async () => {
    render(
      <BillBreakdown
        data={mockBillData}
        showHbarConversion={true}
        billId="BILL-ES-2024-001"
        utilityAccountId="0.0.999999"
      />
    );

    // Wait for exchange rate to load and button to appear
    await waitFor(() => {
      expect(screen.getByText(/Pay Now with HashPack/i)).toBeInTheDocument();
    }, { timeout: 10000 });
  });

  it('should not render Pay Now button when billId is not provided', async () => {
    render(
      <BillBreakdown
        data={mockBillData}
        showHbarConversion={true}
      />
    );

    // Wait for exchange rate to load
    await waitFor(() => {
      expect(screen.getByText(/HBAR Amount/i)).toBeInTheDocument();
    }, { timeout: 10000 });

    // Button should not be present
    expect(screen.queryByText(/Pay Now with HashPack/i)).not.toBeInTheDocument();
  });

  it('should show transaction details below button', async () => {
    render(
      <BillBreakdown
        data={mockBillData}
        showHbarConversion={true}
        billId="BILL-ES-2024-001"
      />
    );

    // Wait for exchange rate to load
    await waitFor(() => {
      expect(screen.getByText(/Transaction will be submitted to Hedera Testnet/i)).toBeInTheDocument();
      expect(screen.getByText(/Consensus time: 3-5 seconds/i)).toBeInTheDocument();
    }, { timeout: 10000 });
  });

  it('should show HashPack installation prompt when not installed', async () => {
    mockHashPack.isInstalled.mockReturnValue(false);
    
    render(
      <BillBreakdown
        data={mockBillData}
        showHbarConversion={true}
        billId="BILL-ES-2024-001"
      />
    );

    // Wait for exchange rate to load
    await waitFor(() => {
      expect(screen.getByText(/HashPack wallet not detected/i)).toBeInTheDocument();
      expect(screen.getByText(/Install HashPack/i)).toBeInTheDocument();
    }, { timeout: 10000 });
  });
});

