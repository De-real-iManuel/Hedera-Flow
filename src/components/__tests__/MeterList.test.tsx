import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MeterList } from '../MeterList';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

// Mock the useMeters hook
vi.mock('@/hooks/useMeters', () => ({
  useMeters: vi.fn(),
}));

const { useMeters } = await import('@/hooks/useMeters');

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  });
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
};

describe('MeterList', () => {
  it('should render loading state', () => {
    vi.mocked(useMeters).mockReturnValue({
      meters: undefined,
      isLoading: true,
      error: null,
      deleteMeter: vi.fn(),
      isDeleting: false,
      createMeter: vi.fn(),
      updateMeter: vi.fn(),
      isCreating: false,
      isUpdating: false,
      createError: null,
      updateError: null,
      deleteError: null,
    });

    render(<MeterList />, { wrapper: createWrapper() });
    expect(screen.getByText('Loading meters...')).toBeInTheDocument();
  });

  it('should render empty state when no meters', () => {
    vi.mocked(useMeters).mockReturnValue({
      meters: [],
      isLoading: false,
      error: null,
      deleteMeter: vi.fn(),
      isDeleting: false,
      createMeter: vi.fn(),
      updateMeter: vi.fn(),
      isCreating: false,
      isUpdating: false,
      createError: null,
      updateError: null,
      deleteError: null,
    });

    render(<MeterList />, { wrapper: createWrapper() });
    expect(screen.getByText('No Meters Registered')).toBeInTheDocument();
    expect(screen.getByText('Register your first electricity meter to start verifying bills')).toBeInTheDocument();
  });

  it('should render meter list with meters', () => {
    const mockMeters = [
      {
        id: '1',
        user_id: 'user1',
        meter_id: 'MTR-001',
        utility_provider_id: 'provider1',
        state_province: 'Lagos',
        utility_provider: 'IKEDP',
        meter_type: 'postpaid' as const,
        band_classification: 'A',
        address: '123 Test St',
        is_primary: true,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      },
      {
        id: '2',
        user_id: 'user1',
        meter_id: 'MTR-002',
        utility_provider_id: 'provider2',
        state_province: 'Abuja',
        utility_provider: 'AEDC',
        meter_type: 'prepaid' as const,
        band_classification: undefined,
        address: undefined,
        is_primary: false,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      },
    ];

    vi.mocked(useMeters).mockReturnValue({
      meters: mockMeters,
      isLoading: false,
      error: null,
      deleteMeter: vi.fn(),
      isDeleting: false,
      createMeter: vi.fn(),
      updateMeter: vi.fn(),
      isCreating: false,
      isUpdating: false,
      createError: null,
      updateError: null,
      deleteError: null,
    });

    render(<MeterList />, { wrapper: createWrapper() });
    
    expect(screen.getByText('Your Meters')).toBeInTheDocument();
    expect(screen.getByText('2 meters registered')).toBeInTheDocument();
    expect(screen.getByText('MTR-001')).toBeInTheDocument();
    expect(screen.getByText('MTR-002')).toBeInTheDocument();
    expect(screen.getByText('IKEDP')).toBeInTheDocument();
    expect(screen.getByText('AEDC')).toBeInTheDocument();
    expect(screen.getByText('Lagos')).toBeInTheDocument();
    expect(screen.getByText('Abuja')).toBeInTheDocument();
  });

  it('should render error state', () => {
    vi.mocked(useMeters).mockReturnValue({
      meters: undefined,
      isLoading: false,
      error: new Error('Failed to load meters'),
      deleteMeter: vi.fn(),
      isDeleting: false,
      createMeter: vi.fn(),
      updateMeter: vi.fn(),
      isCreating: false,
      isUpdating: false,
      createError: null,
      updateError: null,
      deleteError: null,
    });

    render(<MeterList />, { wrapper: createWrapper() });
    expect(screen.getByText('Failed to load meters')).toBeInTheDocument();
  });

  it('should display primary badge for primary meter', () => {
    const mockMeters = [
      {
        id: '1',
        user_id: 'user1',
        meter_id: 'MTR-001',
        utility_provider_id: 'provider1',
        state_province: 'Lagos',
        utility_provider: 'IKEDP',
        meter_type: 'postpaid' as const,
        band_classification: undefined,
        address: undefined,
        is_primary: true,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      },
    ];

    vi.mocked(useMeters).mockReturnValue({
      meters: mockMeters,
      isLoading: false,
      error: null,
      deleteMeter: vi.fn(),
      isDeleting: false,
      createMeter: vi.fn(),
      updateMeter: vi.fn(),
      isCreating: false,
      isUpdating: false,
      createError: null,
      updateError: null,
      deleteError: null,
    });

    render(<MeterList />, { wrapper: createWrapper() });
    expect(screen.getByText('Primary')).toBeInTheDocument();
  });

  it('should display band classification for Nigeria meters', () => {
    const mockMeters = [
      {
        id: '1',
        user_id: 'user1',
        meter_id: 'MTR-001',
        utility_provider_id: 'provider1',
        state_province: 'Lagos',
        utility_provider: 'IKEDP',
        meter_type: 'postpaid' as const,
        band_classification: 'A',
        address: undefined,
        is_primary: false,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      },
    ];

    vi.mocked(useMeters).mockReturnValue({
      meters: mockMeters,
      isLoading: false,
      error: null,
      deleteMeter: vi.fn(),
      isDeleting: false,
      createMeter: vi.fn(),
      updateMeter: vi.fn(),
      isCreating: false,
      isUpdating: false,
      createError: null,
      updateError: null,
      deleteError: null,
    });

    render(<MeterList />, { wrapper: createWrapper() });
    expect(screen.getByText('Band A (20+ hours)')).toBeInTheDocument();
  });
});
