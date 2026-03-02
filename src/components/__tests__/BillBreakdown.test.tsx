import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BillBreakdown, BillBreakdownData } from '../BillBreakdown';
import * as api from '@/lib/api';

// Mock the API module
vi.mock('@/lib/api', () => ({
  exchangeRateApi: {
    get: vi.fn(),
  },
}));

describe('BillBreakdown', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.useRealTimers();
  });
  const mockBillDataFlat: BillBreakdownData = {
    consumptionKwh: 350,
    baseCharge: 70.50,
    taxes: 14.85,
    totalFiat: 85.35,
    currency: 'EUR',
    rateStructureType: 'flat',
  };

  const mockBillDataTiered: BillBreakdownData = {
    consumptionKwh: 650,
    baseCharge: 245.00,
    taxes: 61.25,
    serviceCharge: 10.00,
    totalFiat: 316.25,
    currency: 'USD',
    rateStructureType: 'tiered',
    rateDetails: {
      tiers: [
        { name: 'Tier 1 (0-400 kWh)', kwh: 400, rate: 0.32, amount: 128.00 },
        { name: 'Tier 2 (401-800 kWh)', kwh: 250, rate: 0.40, amount: 100.00 },
      ],
    },
  };

  const mockBillDataTimeOfUse: BillBreakdownData = {
    consumptionKwh: 420,
    baseCharge: 105.00,
    taxes: 22.05,
    totalFiat: 127.05,
    currency: 'EUR',
    rateStructureType: 'time_of_use',
    rateDetails: {
      periods: [
        { name: 'peak', hours: [10, 11, 12, 13, 18, 19, 20, 21], rate: 0.40, kwh: 120, amount: 48.00 },
        { name: 'standard', hours: [8, 9, 14, 15, 16, 17, 22, 23], rate: 0.25, kwh: 180, amount: 45.00 },
        { name: 'off-peak', hours: [0, 1, 2, 3, 4, 5, 6, 7], rate: 0.15, kwh: 120, amount: 18.00 },
      ],
    },
  };

  const mockBillDataBandBased: BillBreakdownData = {
    consumptionKwh: 280,
    baseCharge: 17724.00,
    taxes: 1329.30,
    serviceCharge: 1500.00,
    totalFiat: 20553.30,
    currency: 'NGN',
    rateStructureType: 'band_based',
    rateDetails: {
      band: {
        name: 'Band B',
        rate: 63.30,
        hoursMin: 16,
      },
    },
  };

  const mockBillDataWithHbar: BillBreakdownData = {
    ...mockBillDataFlat,
  };

  const mockExchangeRate = {
    currency: 'EUR',
    hbarPrice: 0.34,
    source: 'coingecko',
    fetchedAt: '2024-03-15T10:30:00Z',
  };

  const mockBillDataWithSubsidies: BillBreakdownData = {
    consumptionKwh: 200,
    baseCharge: 50.00,
    taxes: 10.50,
    subsidies: 5.00,
    totalFiat: 55.50,
    currency: 'INR',
    rateStructureType: 'tiered',
  };

  it('renders consumption summary', () => {
    render(<BillBreakdown data={mockBillDataFlat} />);
    
    expect(screen.getByText('Bill Breakdown')).toBeInTheDocument();
    expect(screen.getByText('Total Consumption')).toBeInTheDocument();
    expect(screen.getByText('350 kWh')).toBeInTheDocument();
  });

  it('displays flat rate structure badge', () => {
    render(<BillBreakdown data={mockBillDataFlat} />);
    
    expect(screen.getByText('Flat Rate')).toBeInTheDocument();
  });

  it('displays tiered rate structure with breakdown', () => {
    render(<BillBreakdown data={mockBillDataTiered} />);
    
    expect(screen.getByText('Tiered Rate')).toBeInTheDocument();
    expect(screen.getByText('Tariff Details')).toBeInTheDocument();
    expect(screen.getByText('Tier 1 (0-400 kWh)')).toBeInTheDocument();
    expect(screen.getByText('Tier 2 (401-800 kWh)')).toBeInTheDocument();
  });

  it('displays time-of-use rate structure with periods', () => {
    render(<BillBreakdown data={mockBillDataTimeOfUse} />);
    
    expect(screen.getByText('Time-of-Use')).toBeInTheDocument();
    // Check that all three periods are present
    const periods = screen.getAllByText(/peak/i);
    expect(periods.length).toBe(2); // "peak" and "off-peak"
    expect(screen.getByText(/standard/i)).toBeInTheDocument();
  });

  it('displays band-based rate structure for Nigeria', () => {
    render(<BillBreakdown data={mockBillDataBandBased} />);
    
    expect(screen.getByText('Band-Based')).toBeInTheDocument();
    expect(screen.getByText('Band Classification')).toBeInTheDocument();
    expect(screen.getByText('Band B')).toBeInTheDocument();
    expect(screen.getByText('16h/day')).toBeInTheDocument();
  });

  it('displays itemized charges correctly', () => {
    render(<BillBreakdown data={mockBillDataFlat} />);
    
    expect(screen.getByText('Charges')).toBeInTheDocument();
    expect(screen.getByText('Energy Charge')).toBeInTheDocument();
    expect(screen.getByText('Taxes & Fees')).toBeInTheDocument();
    expect(screen.getByText('€70.50')).toBeInTheDocument();
    expect(screen.getByText('€14.85')).toBeInTheDocument();
  });

  it('displays service charge when present', () => {
    render(<BillBreakdown data={mockBillDataTiered} />);
    
    expect(screen.getByText('Service Charge')).toBeInTheDocument();
    expect(screen.getByText('$10.00')).toBeInTheDocument();
  });

  it('displays subsidies when present', () => {
    render(<BillBreakdown data={mockBillDataWithSubsidies} />);
    
    expect(screen.getByText('Subsidies Applied')).toBeInTheDocument();
    expect(screen.getByText('-₹5.00')).toBeInTheDocument();
  });

  it('displays total amount with correct currency formatting', () => {
    render(<BillBreakdown data={mockBillDataFlat} />);
    
    expect(screen.getByText('Total Amount Due')).toBeInTheDocument();
    expect(screen.getByText('€85.35')).toBeInTheDocument();
  });

  it('formats different currencies correctly', () => {
    const { rerender } = render(<BillBreakdown data={mockBillDataFlat} />);
    expect(screen.getAllByText(/€/).length).toBeGreaterThan(0);

    rerender(<BillBreakdown data={mockBillDataTiered} />);
    expect(screen.getAllByText(/\$/).length).toBeGreaterThan(0);

    rerender(<BillBreakdown data={mockBillDataBandBased} />);
    expect(screen.getAllByText(/₦/).length).toBeGreaterThan(0);
  });

  it('displays HBAR conversion when showHbarConversion is true', async () => {
    vi.mocked(api.exchangeRateApi.get).mockResolvedValue(mockExchangeRate);
    
    render(<BillBreakdown data={mockBillDataWithHbar} showHbarConversion={true} />);
    
    // Wait for exchange rate to load
    await waitFor(() => {
      expect(screen.getByText('HBAR Payment')).toBeInTheDocument();
    });
    
    expect(screen.getByText('HBAR Amount')).toBeInTheDocument();
    // The HBAR amount is calculated as: 85.35 / 0.34 = 251.02941176
    expect(screen.getByText(/251\.029/)).toBeInTheDocument();
    expect(screen.getByText('Exchange Rate')).toBeInTheDocument();
    expect(screen.getByText(/1 ℏ = €0\.34/)).toBeInTheDocument();
    expect(screen.getByText('Rate Source')).toBeInTheDocument();
    expect(screen.getByText('coingecko')).toBeInTheDocument();
  });

  it('does not display HBAR conversion when showHbarConversion is false', () => {
    render(<BillBreakdown data={mockBillDataWithHbar} showHbarConversion={false} />);
    
    expect(screen.queryByText('HBAR Payment')).not.toBeInTheDocument();
  });

  it('displays exchange rate timestamp when available', async () => {
    vi.mocked(api.exchangeRateApi.get).mockResolvedValue(mockExchangeRate);
    
    render(<BillBreakdown data={mockBillDataWithHbar} showHbarConversion={true} />);
    
    await waitFor(() => {
      expect(screen.getByText('Rate Fetched')).toBeInTheDocument();
    });
  });

  it('displays rate lock warning for HBAR payments', async () => {
    vi.mocked(api.exchangeRateApi.get).mockResolvedValue(mockExchangeRate);
    
    render(<BillBreakdown data={mockBillDataWithHbar} showHbarConversion={true} />);
    
    await waitFor(() => {
      expect(screen.getByText(/Exchange rate locked for 5 minutes/)).toBeInTheDocument();
    });
  });

  it('shows loading state while fetching exchange rate', () => {
    vi.mocked(api.exchangeRateApi.get).mockImplementation(() => new Promise(() => {}));
    
    render(<BillBreakdown data={mockBillDataWithHbar} showHbarConversion={true} />);
    
    expect(screen.getByText('Fetching exchange rate...')).toBeInTheDocument();
  });

  it('displays error when exchange rate fetch fails', async () => {
    vi.mocked(api.exchangeRateApi.get).mockRejectedValue({
      response: { data: { detail: 'Currency not supported' } }
    });
    
    render(<BillBreakdown data={mockBillDataWithHbar} showHbarConversion={true} />);
    
    await waitFor(() => {
      expect(screen.getByText('Currency not supported')).toBeInTheDocument();
    });
  });

  it('applies custom className', () => {
    const { container } = render(<BillBreakdown data={mockBillDataFlat} className="custom-class" />);
    
    const card = container.querySelector('.custom-class');
    expect(card).toBeInTheDocument();
  });

  it('handles missing optional fields gracefully', () => {
    const minimalData: BillBreakdownData = {
      consumptionKwh: 100,
      baseCharge: 20.00,
      taxes: 4.00,
      totalFiat: 24.00,
      currency: 'EUR',
    };

    render(<BillBreakdown data={minimalData} />);
    
    expect(screen.getByText('100 kWh')).toBeInTheDocument();
    expect(screen.getByText('€24.00')).toBeInTheDocument();
    expect(screen.queryByText('Service Charge')).not.toBeInTheDocument();
    expect(screen.queryByText('Subsidies Applied')).not.toBeInTheDocument();
  });

  describe('Exchange Rate Expiry', () => {
    it('displays countdown timer starting at 5:00', async () => {
      vi.mocked(api.exchangeRateApi.get).mockResolvedValue(mockExchangeRate);
      
      render(<BillBreakdown data={mockBillDataWithHbar} showHbarConversion={true} />);
      
      await waitFor(() => {
        expect(screen.getByText('Rate Expires In')).toBeInTheDocument();
      });
      
      expect(screen.getByText('5:00')).toBeInTheDocument();
    });

    it('displays rate fetched timestamp', async () => {
      vi.mocked(api.exchangeRateApi.get).mockResolvedValue(mockExchangeRate);
      
      render(<BillBreakdown data={mockBillDataWithHbar} showHbarConversion={true} />);
      
      await waitFor(() => {
        expect(screen.getByText('Rate Fetched')).toBeInTheDocument();
      });
    });

    it('shows active state styling initially', async () => {
      vi.mocked(api.exchangeRateApi.get).mockResolvedValue(mockExchangeRate);
      
      const { container } = render(<BillBreakdown data={mockBillDataWithHbar} showHbarConversion={true} />);
      
      await waitFor(() => {
        expect(screen.getByText('5:00')).toBeInTheDocument();
      });

      // Active state - purple background
      const rateBox = container.querySelector('.bg-purple-50');
      expect(rateBox).toBeInTheDocument();
    });
  });
});
