/**
 * Payment Confirmation Modal Tests
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { PaymentConfirmationModal, type PaymentConfirmationData } from '../PaymentConfirmationModal';

// Mock sonner toast
vi.mock('sonner', () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
  },
}));

describe('PaymentConfirmationModal', () => {
  const mockData: PaymentConfirmationData = {
    transactionId: '0.0.123456@1708254600.123',
    consensusTimestamp: '2026-02-18T10:30:05Z',
    amountHbar: 251.17647059,
    amountFiat: 85.40,
    currency: 'EUR',
    exchangeRate: 0.34,
    exchangeRateSource: 'coingecko',
    billId: 'bill-123',
    consumptionKwh: 250.5,
    receiptUrl: '/api/payments/bill-123/receipt',
  };

  const mockOnClose = vi.fn();
  const mockOnDownloadReceipt = vi.fn();
  const mockOnViewBillDetails = vi.fn();

  it('renders modal when open', () => {
    render(
      <PaymentConfirmationModal
        isOpen={true}
        onClose={mockOnClose}
        data={mockData}
      />
    );

    expect(screen.getByText('Payment Successful!')).toBeInTheDocument();
    expect(screen.getByText(/Your bill payment has been confirmed/)).toBeInTheDocument();
  });

  it('does not render when closed', () => {
    render(
      <PaymentConfirmationModal
        isOpen={false}
        onClose={mockOnClose}
        data={mockData}
      />
    );

    expect(screen.queryByText('Payment Successful!')).not.toBeInTheDocument();
  });

  it('displays transaction ID correctly', () => {
    render(
      <PaymentConfirmationModal
        isOpen={true}
        onClose={mockOnClose}
        data={mockData}
      />
    );

    expect(screen.getByText(mockData.transactionId)).toBeInTheDocument();
  });

  it('displays HBAR amount correctly', () => {
    render(
      <PaymentConfirmationModal
        isOpen={true}
        onClose={mockOnClose}
        data={mockData}
      />
    );

    expect(screen.getByText(/251\.17647059 ℏ/)).toBeInTheDocument();
  });

  it('displays fiat amount correctly', () => {
    render(
      <PaymentConfirmationModal
        isOpen={true}
        onClose={mockOnClose}
        data={mockData}
      />
    );

    expect(screen.getByText(/€85\.40/)).toBeInTheDocument();
  });

  it('displays exchange rate correctly', () => {
    render(
      <PaymentConfirmationModal
        isOpen={true}
        onClose={mockOnClose}
        data={mockData}
      />
    );

    expect(screen.getByText(/1 ℏ = €0\.34/)).toBeInTheDocument();
  });

  it('displays consumption when provided', () => {
    render(
      <PaymentConfirmationModal
        isOpen={true}
        onClose={mockOnClose}
        data={mockData}
      />
    );

    expect(screen.getByText(/250\.5 kWh/)).toBeInTheDocument();
  });

  it('does not display consumption when not provided', () => {
    const dataWithoutConsumption = { ...mockData, consumptionKwh: undefined };
    
    render(
      <PaymentConfirmationModal
        isOpen={true}
        onClose={mockOnClose}
        data={dataWithoutConsumption}
      />
    );

    expect(screen.queryByText(/kWh/)).not.toBeInTheDocument();
  });

  it('calls onClose when Done button is clicked', () => {
    render(
      <PaymentConfirmationModal
        isOpen={true}
        onClose={mockOnClose}
        data={mockData}
      />
    );

    const doneButton = screen.getByText('Done');
    fireEvent.click(doneButton);

    expect(mockOnClose).toHaveBeenCalledTimes(1);
  });

  it('opens HashScan when View on HashScan button is clicked', () => {
    const mockOpen = vi.fn();
    window.open = mockOpen;

    render(
      <PaymentConfirmationModal
        isOpen={true}
        onClose={mockOnClose}
        data={mockData}
      />
    );

    const hashScanButton = screen.getByText('View on HashScan');
    fireEvent.click(hashScanButton);

    expect(mockOpen).toHaveBeenCalledWith(
      `https://hashscan.io/testnet/transaction/${mockData.transactionId}`,
      '_blank',
      'noopener,noreferrer'
    );
  });

  it('calls onDownloadReceipt when Download Receipt button is clicked', () => {
    render(
      <PaymentConfirmationModal
        isOpen={true}
        onClose={mockOnClose}
        data={mockData}
        onDownloadReceipt={mockOnDownloadReceipt}
      />
    );

    const downloadButton = screen.getByText('Download Receipt');
    fireEvent.click(downloadButton);

    expect(mockOnDownloadReceipt).toHaveBeenCalledTimes(1);
  });

  it('does not show Download Receipt button when callback not provided', () => {
    render(
      <PaymentConfirmationModal
        isOpen={true}
        onClose={mockOnClose}
        data={mockData}
      />
    );

    expect(screen.queryByText('Download Receipt')).not.toBeInTheDocument();
  });

  it('calls onViewBillDetails when View Bill Details button is clicked', () => {
    render(
      <PaymentConfirmationModal
        isOpen={true}
        onClose={mockOnClose}
        data={mockData}
        onViewBillDetails={mockOnViewBillDetails}
      />
    );

    const viewBillButton = screen.getByText('View Bill Details');
    fireEvent.click(viewBillButton);

    expect(mockOnViewBillDetails).toHaveBeenCalledTimes(1);
  });

  it('does not show View Bill Details button when callback not provided', () => {
    render(
      <PaymentConfirmationModal
        isOpen={true}
        onClose={mockOnClose}
        data={mockData}
      />
    );

    expect(screen.queryByText('View Bill Details')).not.toBeInTheDocument();
  });

  it('copies transaction ID to clipboard when copy button is clicked', async () => {
    const mockWriteText = vi.fn().mockResolvedValue(undefined);
    Object.assign(navigator, {
      clipboard: {
        writeText: mockWriteText,
      },
    });

    render(
      <PaymentConfirmationModal
        isOpen={true}
        onClose={mockOnClose}
        data={mockData}
      />
    );

    const copyButton = screen.getByTitle('Copy transaction ID');
    fireEvent.click(copyButton);

    await waitFor(() => {
      expect(mockWriteText).toHaveBeenCalledWith(mockData.transactionId);
    });
  });

  it('formats different currencies correctly', () => {
    const currencies = [
      { currency: 'USD', symbol: '$', amount: 120.50 },
      { currency: 'INR', symbol: '₹', amount: 450.00 },
      { currency: 'BRL', symbol: 'R$', amount: 95.00 },
      { currency: 'NGN', symbol: '₦', amount: 12500.00 },
    ];

    currencies.forEach(({ currency, symbol, amount }) => {
      const { unmount } = render(
        <PaymentConfirmationModal
          isOpen={true}
          onClose={mockOnClose}
          data={{ ...mockData, currency, amountFiat: amount }}
        />
      );

      expect(screen.getByText(new RegExp(`${symbol}${amount.toFixed(2)}`))).toBeInTheDocument();
      unmount();
    });
  });

  it('displays confirmed badge', () => {
    render(
      <PaymentConfirmationModal
        isOpen={true}
        onClose={mockOnClose}
        data={mockData}
      />
    );

    expect(screen.getByText('Confirmed')).toBeInTheDocument();
  });

  it('displays blockchain info', () => {
    render(
      <PaymentConfirmationModal
        isOpen={true}
        onClose={mockOnClose}
        data={mockData}
      />
    );

    expect(screen.getByText(/This transaction is permanently recorded/)).toBeInTheDocument();
    expect(screen.getByText(/Network: Hedera Testnet/)).toBeInTheDocument();
  });
});
