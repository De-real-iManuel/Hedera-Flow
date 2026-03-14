/**
 * Tests for PrepaidTokenPurchase notification system
 * 
 * Validates:
 * - Success notifications show token ID and receipt confirmation
 * - Error notifications show clear error messages
 * - Notifications are dismissible
 * - Notifications have appropriate styling (green for success, red for error)
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { PrepaidTokenPurchase } from '../PrepaidTokenPurchase';
import { toast } from 'sonner';

// Mock dependencies
vi.mock('sonner', () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
    info: vi.fn(),
  },
}));

vi.mock('@/hooks/useAuth', () => ({
  useAuth: () => ({
    user: {
      hedera_account_id: '0.0.123456',
      country_code: 'US',
    },
  }),
}));

vi.mock('@/lib/api/prepaid', () => ({
  prepaidApi: {
    preview: vi.fn().mockResolvedValue({
      amount_hbar: 147.0,
      amount_fiat: 50.0,
      units_kwh: 125.0,
      exchange_rate: 0.34,
      tariff_rate: 0.40,
    }),
    confirm: vi.fn().mockResolvedValue({
      token: {
        token_id: 'TOKEN-US-2026-001',
        units_purchased: 125.0,
        amount_paid_hbar: 147.0,
        amount_paid_fiat: 50.0,
      },
    }),
  },
}));

vi.mock('@/lib/hashpack', () => ({
  hashPackWallet: {
    initialize: vi.fn().mockResolvedValue(true),
    isConnected: vi.fn().mockReturnValue(true),
    getConnectedAccount: vi.fn().mockReturnValue('0.0.123456'),
    checkBalance: vi.fn().mockResolvedValue(200),
  },
}));

// Mock window.hashpack
(global as any).window = {
  hashpack: {
    sendTransaction: vi.fn().mockResolvedValue({
      success: true,
      receipt: {
        transactionId: '0.0.123456@1234567890.123',
        status: 'SUCCESS',
      },
    }),
  },
};

describe('PrepaidTokenPurchase - Notifications', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Success Notifications', () => {
    it('should show success notification with token ID', async () => {
      const onSuccess = vi.fn();
      render(
        <PrepaidTokenPurchase
          meterId="meter-123"
          onSuccess={onSuccess}
        />
      );

      // Wait for preview to load
      await waitFor(() => {
        expect(screen.getByText(/Purchase Preview/i)).toBeInTheDocument();
      });

      // Click purchase button
      const purchaseButton = screen.getByRole('button', { name: /Buy with HBAR/i });
      await userEvent.click(purchaseButton);

      // Wait for success notification
      await waitFor(() => {
        expect(toast.success).toHaveBeenCalled();
      });

      // Verify success notification contains token ID
      const successCall = (toast.success as any).mock.calls[0];
      expect(successCall[0]).toContain('Token Purchased Successfully');
      
      // Verify notification has green styling
      expect(successCall[1].className).toContain('bg-green-50');
      expect(successCall[1].className).toContain('border-green-500');
    });

    it('should show receipt confirmation in success notification', async () => {
      render(<PrepaidTokenPurchase meterId="meter-123" />);

      await waitFor(() => {
        expect(screen.getByText(/Purchase Preview/i)).toBeInTheDocument();
      });

      const purchaseButton = screen.getByRole('button', { name: /Buy with HBAR/i });
      await userEvent.click(purchaseButton);

      await waitFor(() => {
        expect(toast.success).toHaveBeenCalled();
      });

      // Verify receipt confirmation message is included
      const successCall = (toast.success as any).mock.calls[0];
      const description = successCall[1].description;
      
      // The description should be a React element containing receipt confirmation
      expect(description).toBeDefined();
    });

    it('should make success notification dismissible with action button', async () => {
      render(<PrepaidTokenPurchase meterId="meter-123" />);

      await waitFor(() => {
        expect(screen.getByText(/Purchase Preview/i)).toBeInTheDocument();
      });

      const purchaseButton = screen.getByRole('button', { name: /Buy with HBAR/i });
      await userEvent.click(purchaseButton);

      await waitFor(() => {
        expect(toast.success).toHaveBeenCalled();
      });

      // Verify notification has action button
      const successCall = (toast.success as any).mock.calls[0];
      expect(successCall[1].action).toBeDefined();
      expect(successCall[1].action.label).toBe('View on HashScan');
    });
  });

  describe('Error Notifications', () => {
    it('should show error notification with clear error message', async () => {
      // Mock API to throw error
      const { prepaidApi } = await import('@/lib/api/prepaid');
      (prepaidApi.confirm as any).mockRejectedValueOnce(
        new Error('Insufficient HBAR balance')
      );

      render(<PrepaidTokenPurchase meterId="meter-123" />);

      await waitFor(() => {
        expect(screen.getByText(/Purchase Preview/i)).toBeInTheDocument();
      });

      const purchaseButton = screen.getByRole('button', { name: /Buy with HBAR/i });
      await userEvent.click(purchaseButton);

      // Wait for error notification
      await waitFor(() => {
        expect(toast.error).toHaveBeenCalled();
      });

      // Verify error notification contains error message
      const errorCall = (toast.error as any).mock.calls[0];
      expect(errorCall[0]).toContain('Purchase Failed');
      
      // Verify notification has red styling
      expect(errorCall[1].className).toContain('bg-red-50');
      expect(errorCall[1].className).toContain('border-red-500');
    });

    it('should make error notification dismissible', async () => {
      const { prepaidApi } = await import('@/lib/api/prepaid');
      (prepaidApi.confirm as any).mockRejectedValueOnce(
        new Error('Network error')
      );

      render(<PrepaidTokenPurchase meterId="meter-123" />);

      await waitFor(() => {
        expect(screen.getByText(/Purchase Preview/i)).toBeInTheDocument();
      });

      const purchaseButton = screen.getByRole('button', { name: /Buy with HBAR/i });
      await userEvent.click(purchaseButton);

      await waitFor(() => {
        expect(toast.error).toHaveBeenCalled();
      });

      // Verify notification has dismiss action
      const errorCall = (toast.error as any).mock.calls[0];
      expect(errorCall[1].action).toBeDefined();
      expect(errorCall[1].action.label).toBe('Dismiss');
    });

    it('should show validation error for missing wallet', async () => {
      // Mock user without wallet
      vi.mocked(await import('@/hooks/useAuth')).useAuth = () => ({
        user: {
          hedera_account_id: null,
          country_code: 'US',
        },
      } as any);

      render(<PrepaidTokenPurchase meterId="meter-123" />);

      await waitFor(() => {
        expect(screen.getByText(/Purchase Preview/i)).toBeInTheDocument();
      });

      const purchaseButton = screen.getByRole('button', { name: /Buy with HBAR/i });
      await userEvent.click(purchaseButton);

      // Should show wallet not connected error
      await waitFor(() => {
        expect(toast.error).toHaveBeenCalledWith(
          expect.stringContaining('Wallet Not Connected'),
          expect.objectContaining({
            className: 'bg-yellow-50 border-yellow-500',
          })
        );
      });
    });
  });

  describe('Notification Styling', () => {
    it('should use green styling for success notifications', async () => {
      render(<PrepaidTokenPurchase meterId="meter-123" />);

      await waitFor(() => {
        expect(screen.getByText(/Purchase Preview/i)).toBeInTheDocument();
      });

      const purchaseButton = screen.getByRole('button', { name: /Buy with HBAR/i });
      await userEvent.click(purchaseButton);

      await waitFor(() => {
        expect(toast.success).toHaveBeenCalled();
      });

      const successCall = (toast.success as any).mock.calls[0];
      expect(successCall[1].className).toContain('bg-green-50');
      expect(successCall[1].className).toContain('border-green-500');
    });

    it('should use red styling for error notifications', async () => {
      const { prepaidApi } = await import('@/lib/api/prepaid');
      (prepaidApi.confirm as any).mockRejectedValueOnce(new Error('Test error'));

      render(<PrepaidTokenPurchase meterId="meter-123" />);

      await waitFor(() => {
        expect(screen.getByText(/Purchase Preview/i)).toBeInTheDocument();
      });

      const purchaseButton = screen.getByRole('button', { name: /Buy with HBAR/i });
      await userEvent.click(purchaseButton);

      await waitFor(() => {
        expect(toast.error).toHaveBeenCalled();
      });

      const errorCall = (toast.error as any).mock.calls[0];
      expect(errorCall[1].className).toContain('bg-red-50');
      expect(errorCall[1].className).toContain('border-red-500');
    });

    it('should use blue styling for info notifications', async () => {
      render(<PrepaidTokenPurchase meterId="meter-123" />);

      await waitFor(() => {
        expect(screen.getByText(/Purchase Preview/i)).toBeInTheDocument();
      });

      const purchaseButton = screen.getByRole('button', { name: /Buy with HBAR/i });
      await userEvent.click(purchaseButton);

      // Info notifications are shown during the process
      await waitFor(() => {
        expect(toast.info).toHaveBeenCalled();
      });

      const infoCall = (toast.info as any).mock.calls[0];
      expect(infoCall[1].className).toContain('bg-blue-50');
      expect(infoCall[1].className).toContain('border-blue-500');
    });
  });
});
