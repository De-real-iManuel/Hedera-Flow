import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { Camera } from '../Camera';

describe('Camera Component', () => {
  const mockOnCapture = vi.fn();
  const mockOnClose = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should render with start camera button', () => {
    render(<Camera onCapture={mockOnCapture} />);
    
    const startButton = screen.getByText('Start Camera');
    expect(startButton).toBeInTheDocument();
  });

  it('should show instructions when camera is not active', () => {
    render(<Camera onCapture={mockOnCapture} />);
    
    const instructions = screen.getByText(/Hold steady over the digital display/i);
    expect(instructions).toBeInTheDocument();
  });

  it('should request camera access when start button is clicked', async () => {
    const mockGetUserMedia = vi.fn().mockResolvedValue({
      getTracks: () => [{ stop: vi.fn() }]
    });
    
    Object.defineProperty(global.navigator, 'mediaDevices', {
      value: {
        getUserMedia: mockGetUserMedia
      },
      writable: true
    });
    
    render(<Camera onCapture={mockOnCapture} />);
    
    const startButton = screen.getByText('Start Camera');
    fireEvent.click(startButton);
    
    await waitFor(() => {
      expect(mockGetUserMedia).toHaveBeenCalledWith({
        video: expect.objectContaining({
          facingMode: 'environment',
          width: { ideal: 1920 },
          height: { ideal: 1080 }
        })
      });
    });
  });

  it('should show error message when camera access is denied', async () => {
    const mockGetUserMedia = vi.fn().mockRejectedValue(new Error('Permission denied'));
    
    Object.defineProperty(global.navigator, 'mediaDevices', {
      value: {
        getUserMedia: mockGetUserMedia
      },
      writable: true
    });
    
    render(<Camera onCapture={mockOnCapture} />);
    
    const startButton = screen.getByText('Start Camera');
    fireEvent.click(startButton);
    
    await waitFor(() => {
      expect(screen.getByText(/Unable to access camera/i)).toBeInTheDocument();
    });
  });

  it('should show capture and cancel buttons when camera is active', async () => {
    const mockGetUserMedia = vi.fn().mockResolvedValue({
      getTracks: () => [{ stop: vi.fn() }]
    });
    
    Object.defineProperty(global.navigator, 'mediaDevices', {
      value: {
        getUserMedia: mockGetUserMedia
      },
      writable: true
    });
    
    render(<Camera onCapture={mockOnCapture} />);
    
    const startButton = screen.getByText('Start Camera');
    fireEvent.click(startButton);
    
    await waitFor(() => {
      expect(screen.getByText('Capture Reading')).toBeInTheDocument();
      expect(screen.getByText('Cancel')).toBeInTheDocument();
    });
  });

  it('should render close button when onClose prop is provided', () => {
    render(<Camera onCapture={mockOnCapture} onClose={mockOnClose} />);
    
    const closeButton = screen.getByLabelText('Close camera');
    expect(closeButton).toBeInTheDocument();
  });

  it('should call onClose when close button is clicked', () => {
    render(<Camera onCapture={mockOnCapture} onClose={mockOnClose} />);
    
    const closeButton = screen.getByLabelText('Close camera');
    fireEvent.click(closeButton);
    
    expect(mockOnClose).toHaveBeenCalledTimes(1);
  });

  it('should show alignment guide overlay when camera is active', async () => {
    const mockGetUserMedia = vi.fn().mockResolvedValue({
      getTracks: () => [{ stop: vi.fn() }]
    });
    
    Object.defineProperty(global.navigator, 'mediaDevices', {
      value: {
        getUserMedia: mockGetUserMedia
      },
      writable: true
    });
    
    render(<Camera onCapture={mockOnCapture} />);
    
    const startButton = screen.getByText('Start Camera');
    fireEvent.click(startButton);
    
    await waitFor(() => {
      expect(screen.getByText('Position meter display in frame')).toBeInTheDocument();
    });
  });

  describe('Camera Permission Error Handling', () => {
    it('should handle NotAllowedError with specific message', async () => {
      const error = new DOMException('Permission denied', 'NotAllowedError');
      const mockGetUserMedia = vi.fn().mockRejectedValue(error);
      
      Object.defineProperty(global.navigator, 'mediaDevices', {
        value: { getUserMedia: mockGetUserMedia },
        writable: true
      });
      
      render(<Camera onCapture={mockOnCapture} />);
      fireEvent.click(screen.getByText('Start Camera'));
      
      await waitFor(() => {
        expect(screen.getByText(/Camera access denied/i)).toBeInTheDocument();
        expect(screen.getByText(/How to enable camera:/i)).toBeInTheDocument();
      });
    });

    it('should handle NotFoundError when no camera is available', async () => {
      const error = new DOMException('No camera found', 'NotFoundError');
      const mockGetUserMedia = vi.fn().mockRejectedValue(error);
      
      Object.defineProperty(global.navigator, 'mediaDevices', {
        value: { getUserMedia: mockGetUserMedia },
        writable: true
      });
      
      render(<Camera onCapture={mockOnCapture} />);
      fireEvent.click(screen.getByText('Start Camera'));
      
      await waitFor(() => {
        expect(screen.getByText(/No camera found on this device/i)).toBeInTheDocument();
      });
    });

    it('should handle NotReadableError when camera is in use', async () => {
      const error = new DOMException('Camera in use', 'NotReadableError');
      const mockGetUserMedia = vi.fn().mockRejectedValue(error);
      
      Object.defineProperty(global.navigator, 'mediaDevices', {
        value: { getUserMedia: mockGetUserMedia },
        writable: true
      });
      
      render(<Camera onCapture={mockOnCapture} />);
      fireEvent.click(screen.getByText('Start Camera'));
      
      await waitFor(() => {
        expect(screen.getByText(/Camera is already in use/i)).toBeInTheDocument();
        expect(screen.getByText(/Camera is busy:/i)).toBeInTheDocument();
      });
    });

    it('should handle OverconstrainedError when camera constraints cannot be met', async () => {
      const error = new DOMException('Constraints not satisfied', 'OverconstrainedError');
      const mockGetUserMedia = vi.fn().mockRejectedValue(error);
      
      Object.defineProperty(global.navigator, 'mediaDevices', {
        value: { getUserMedia: mockGetUserMedia },
        writable: true
      });
      
      render(<Camera onCapture={mockOnCapture} />);
      fireEvent.click(screen.getByText('Start Camera'));
      
      await waitFor(() => {
        expect(screen.getByText(/Camera does not meet the required specifications/i)).toBeInTheDocument();
      });
    });

    it('should handle SecurityError with HTTPS guidance', async () => {
      const error = new DOMException('Security error', 'SecurityError');
      const mockGetUserMedia = vi.fn().mockRejectedValue(error);
      
      Object.defineProperty(global.navigator, 'mediaDevices', {
        value: { getUserMedia: mockGetUserMedia },
        writable: true
      });
      
      render(<Camera onCapture={mockOnCapture} />);
      fireEvent.click(screen.getByText('Start Camera'));
      
      await waitFor(() => {
        expect(screen.getByText(/Camera access blocked due to security settings/i)).toBeInTheDocument();
        expect(screen.getByText(/Security requirement:/i)).toBeInTheDocument();
      });
    });

    it('should handle AbortError', async () => {
      const error = new DOMException('Aborted', 'AbortError');
      const mockGetUserMedia = vi.fn().mockRejectedValue(error);
      
      Object.defineProperty(global.navigator, 'mediaDevices', {
        value: { getUserMedia: mockGetUserMedia },
        writable: true
      });
      
      render(<Camera onCapture={mockOnCapture} />);
      fireEvent.click(screen.getByText('Start Camera'));
      
      await waitFor(() => {
        expect(screen.getByText(/Camera access was interrupted/i)).toBeInTheDocument();
      });
    });

    it('should handle unsupported browser (no getUserMedia)', async () => {
      Object.defineProperty(global.navigator, 'mediaDevices', {
        value: undefined,
        writable: true
      });
      
      render(<Camera onCapture={mockOnCapture} />);
      fireEvent.click(screen.getByText('Start Camera'));
      
      await waitFor(() => {
        expect(screen.getByText(/Camera is not supported on this device or browser/i)).toBeInTheDocument();
      });
    });

    it('should show Try Again button in error state', async () => {
      const error = new DOMException('Permission denied', 'NotAllowedError');
      const mockGetUserMedia = vi.fn().mockRejectedValue(error);
      
      Object.defineProperty(global.navigator, 'mediaDevices', {
        value: { getUserMedia: mockGetUserMedia },
        writable: true
      });
      
      render(<Camera onCapture={mockOnCapture} />);
      fireEvent.click(screen.getByText('Start Camera'));
      
      await waitFor(() => {
        expect(screen.getByText('Try Again')).toBeInTheDocument();
      });
    });

    it('should allow retry after error', async () => {
      const error = new DOMException('Permission denied', 'NotAllowedError');
      const mockGetUserMedia = vi.fn()
        .mockRejectedValueOnce(error)
        .mockResolvedValueOnce({
          getTracks: () => [{ stop: vi.fn() }]
        });
      
      Object.defineProperty(global.navigator, 'mediaDevices', {
        value: { getUserMedia: mockGetUserMedia },
        writable: true
      });
      
      render(<Camera onCapture={mockOnCapture} />);
      fireEvent.click(screen.getByText('Start Camera'));
      
      await waitFor(() => {
        expect(screen.getByText(/Camera access denied/i)).toBeInTheDocument();
      });
      
      fireEvent.click(screen.getByText('Try Again'));
      
      await waitFor(() => {
        expect(screen.getByText('Capture Reading')).toBeInTheDocument();
      });
    });

    it('should show Cancel button in error state when onClose is provided', async () => {
      const error = new DOMException('Permission denied', 'NotAllowedError');
      const mockGetUserMedia = vi.fn().mockRejectedValue(error);
      
      Object.defineProperty(global.navigator, 'mediaDevices', {
        value: { getUserMedia: mockGetUserMedia },
        writable: true
      });
      
      render(<Camera onCapture={mockOnCapture} onClose={mockOnClose} />);
      fireEvent.click(screen.getByText('Start Camera'));
      
      await waitFor(() => {
        const cancelButtons = screen.getAllByText('Cancel');
        expect(cancelButtons.length).toBeGreaterThan(0);
      });
    });
  });
});
