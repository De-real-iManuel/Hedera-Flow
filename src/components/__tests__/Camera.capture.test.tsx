import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { Camera } from '../Camera';

describe('Camera - Photo Capture to Canvas', () => {
  const mockOnCapture = vi.fn();
  let mockVideoElement: HTMLVideoElement;
  let mockCanvasElement: HTMLCanvasElement;
  let mockContext: CanvasRenderingContext2D;

  beforeEach(() => {
    vi.clearAllMocks();

    // Mock video element
    mockVideoElement = document.createElement('video');
    Object.defineProperty(mockVideoElement, 'videoWidth', { value: 1920, writable: true });
    Object.defineProperty(mockVideoElement, 'videoHeight', { value: 1080, writable: true });

    // Mock canvas and context
    mockContext = {
      drawImage: vi.fn(),
    } as unknown as CanvasRenderingContext2D;

    mockCanvasElement = document.createElement('canvas');
    mockCanvasElement.getContext = vi.fn().mockReturnValue(mockContext);
    mockCanvasElement.toBlob = vi.fn((callback) => {
      const blob = new Blob(['fake-image-data'], { type: 'image/jpeg' });
      callback(blob);
    });

    // Mock getUserMedia
    const mockGetUserMedia = vi.fn().mockResolvedValue({
      getTracks: () => [{ stop: vi.fn() }]
    });

    Object.defineProperty(global.navigator, 'mediaDevices', {
      value: {
        getUserMedia: mockGetUserMedia
      },
      writable: true
    });
  });

  it('should set canvas dimensions to match video dimensions', async () => {
    render(<Camera onCapture={mockOnCapture} />);

    // Start camera
    const startButton = screen.getByText('Start Camera');
    fireEvent.click(startButton);

    await waitFor(() => {
      expect(screen.getByText('Capture Reading')).toBeInTheDocument();
    });

    // Mock refs
    const component = screen.getByText('Capture Reading').closest('div')?.parentElement;
    const videoRef = component?.querySelector('video');
    const canvasRef = component?.querySelector('canvas');

    if (videoRef && canvasRef) {
      Object.defineProperty(videoRef, 'videoWidth', { value: 1920 });
      Object.defineProperty(videoRef, 'videoHeight', { value: 1080 });

      const mockContext = {
        drawImage: vi.fn(),
      } as unknown as CanvasRenderingContext2D;

      canvasRef.getContext = vi.fn().mockReturnValue(mockContext);
      canvasRef.toBlob = vi.fn((callback) => {
        const blob = new Blob(['fake-image-data'], { type: 'image/jpeg' });
        callback(blob);
      });

      // Capture photo
      const captureButton = screen.getByText('Capture Reading');
      fireEvent.click(captureButton);

      await waitFor(() => {
        // Verify canvas dimensions were set
        expect(canvasRef.width).toBe(1920);
        expect(canvasRef.height).toBe(1080);
      });
    }
  });

  it('should draw video frame to canvas when capturing', async () => {
    render(<Camera onCapture={mockOnCapture} />);

    // Start camera
    const startButton = screen.getByText('Start Camera');
    fireEvent.click(startButton);

    await waitFor(() => {
      expect(screen.getByText('Capture Reading')).toBeInTheDocument();
    });

    // Get elements
    const component = screen.getByText('Capture Reading').closest('div')?.parentElement;
    const videoRef = component?.querySelector('video');
    const canvasRef = component?.querySelector('canvas');

    if (videoRef && canvasRef) {
      Object.defineProperty(videoRef, 'videoWidth', { value: 1920 });
      Object.defineProperty(videoRef, 'videoHeight', { value: 1080 });

      const mockContext = {
        drawImage: vi.fn(),
      } as unknown as CanvasRenderingContext2D;

      canvasRef.getContext = vi.fn().mockReturnValue(mockContext);
      canvasRef.toBlob = vi.fn((callback) => {
        const blob = new Blob(['fake-image-data'], { type: 'image/jpeg' });
        callback(blob);
      });

      // Capture photo
      const captureButton = screen.getByText('Capture Reading');
      fireEvent.click(captureButton);

      await waitFor(() => {
        // Verify drawImage was called with video element
        expect(mockContext.drawImage).toHaveBeenCalledWith(videoRef, 0, 0);
      });
    }
  });

  it('should convert canvas to blob with correct JPEG quality', async () => {
    render(<Camera onCapture={mockOnCapture} />);

    // Start camera
    const startButton = screen.getByText('Start Camera');
    fireEvent.click(startButton);

    await waitFor(() => {
      expect(screen.getByText('Capture Reading')).toBeInTheDocument();
    });

    // Get canvas element
    const component = screen.getByText('Capture Reading').closest('div')?.parentElement;
    const videoRef = component?.querySelector('video');
    const canvasRef = component?.querySelector('canvas');

    if (videoRef && canvasRef) {
      Object.defineProperty(videoRef, 'videoWidth', { value: 1920 });
      Object.defineProperty(videoRef, 'videoHeight', { value: 1080 });

      const mockContext = {
        drawImage: vi.fn(),
      } as unknown as CanvasRenderingContext2D;

      const toBlobSpy = vi.fn((callback, type, quality) => {
        const blob = new Blob(['fake-image-data'], { type: 'image/jpeg' });
        callback(blob);
      });

      canvasRef.getContext = vi.fn().mockReturnValue(mockContext);
      canvasRef.toBlob = toBlobSpy;

      // Capture photo
      const captureButton = screen.getByText('Capture Reading');
      fireEvent.click(captureButton);

      await waitFor(() => {
        // Verify toBlob was called with correct parameters
        expect(toBlobSpy).toHaveBeenCalledWith(
          expect.any(Function),
          'image/jpeg',
          0.95
        );
      });
    }
  });

  it('should create File object from blob and call onCapture', async () => {
    render(<Camera onCapture={mockOnCapture} />);

    // Start camera
    const startButton = screen.getByText('Start Camera');
    fireEvent.click(startButton);

    await waitFor(() => {
      expect(screen.getByText('Capture Reading')).toBeInTheDocument();
    });

    // Get elements
    const component = screen.getByText('Capture Reading').closest('div')?.parentElement;
    const videoRef = component?.querySelector('video');
    const canvasRef = component?.querySelector('canvas');

    if (videoRef && canvasRef) {
      Object.defineProperty(videoRef, 'videoWidth', { value: 1920 });
      Object.defineProperty(videoRef, 'videoHeight', { value: 1080 });

      const mockContext = {
        drawImage: vi.fn(),
      } as unknown as CanvasRenderingContext2D;

      canvasRef.getContext = vi.fn().mockReturnValue(mockContext);
      canvasRef.toBlob = vi.fn((callback) => {
        const blob = new Blob(['fake-image-data'], { type: 'image/jpeg' });
        callback(blob);
      });

      // Capture photo
      const captureButton = screen.getByText('Capture Reading');
      fireEvent.click(captureButton);

      await waitFor(() => {
        // Verify onCapture was called with a File object
        expect(mockOnCapture).toHaveBeenCalledTimes(1);
        const capturedFile = mockOnCapture.mock.calls[0][0];
        expect(capturedFile).toBeInstanceOf(File);
        expect(capturedFile.type).toBe('image/jpeg');
        expect(capturedFile.name).toMatch(/^meter-\d+\.jpg$/);
      });
    }
  });

  it('should stop camera after successful capture', async () => {
    const mockTrack = { stop: vi.fn() };
    const mockGetUserMedia = vi.fn().mockResolvedValue({
      getTracks: () => [mockTrack]
    });

    Object.defineProperty(global.navigator, 'mediaDevices', {
      value: {
        getUserMedia: mockGetUserMedia
      },
      writable: true
    });

    render(<Camera onCapture={mockOnCapture} />);

    // Start camera
    const startButton = screen.getByText('Start Camera');
    fireEvent.click(startButton);

    await waitFor(() => {
      expect(screen.getByText('Capture Reading')).toBeInTheDocument();
    });

    // Get elements
    const component = screen.getByText('Capture Reading').closest('div')?.parentElement;
    const videoRef = component?.querySelector('video');
    const canvasRef = component?.querySelector('canvas');

    if (videoRef && canvasRef) {
      Object.defineProperty(videoRef, 'videoWidth', { value: 1920 });
      Object.defineProperty(videoRef, 'videoHeight', { value: 1080 });

      const mockContext = {
        drawImage: vi.fn(),
      } as unknown as CanvasRenderingContext2D;

      canvasRef.getContext = vi.fn().mockReturnValue(mockContext);
      canvasRef.toBlob = vi.fn((callback) => {
        const blob = new Blob(['fake-image-data'], { type: 'image/jpeg' });
        callback(blob);
      });

      // Capture photo
      const captureButton = screen.getByText('Capture Reading');
      fireEvent.click(captureButton);

      await waitFor(() => {
        // Verify camera stream was stopped
        expect(mockTrack.stop).toHaveBeenCalled();
      });
    }
  });

  it('should handle null context gracefully', async () => {
    render(<Camera onCapture={mockOnCapture} />);

    // Start camera
    const startButton = screen.getByText('Start Camera');
    fireEvent.click(startButton);

    await waitFor(() => {
      expect(screen.getByText('Capture Reading')).toBeInTheDocument();
    });

    // Get elements
    const component = screen.getByText('Capture Reading').closest('div')?.parentElement;
    const videoRef = component?.querySelector('video');
    const canvasRef = component?.querySelector('canvas');

    if (videoRef && canvasRef) {
      Object.defineProperty(videoRef, 'videoWidth', { value: 1920 });
      Object.defineProperty(videoRef, 'videoHeight', { value: 1080 });

      // Return null context
      canvasRef.getContext = vi.fn().mockReturnValue(null);

      // Capture photo
      const captureButton = screen.getByText('Capture Reading');
      fireEvent.click(captureButton);

      // Should not crash, onCapture should not be called
      await waitFor(() => {
        expect(mockOnCapture).not.toHaveBeenCalled();
      });
    }
  });
});
