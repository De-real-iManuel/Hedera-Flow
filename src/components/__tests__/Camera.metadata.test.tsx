import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { Camera, ImageMetadata } from '../Camera';

describe('Camera - Image Metadata Extraction', () => {
  let mockOnCapture: ReturnType<typeof vi.fn>;
  let mockGeolocation: {
    getCurrentPosition: ReturnType<typeof vi.fn>;
  };

  beforeEach(() => {
    vi.clearAllMocks();
    mockOnCapture = vi.fn();

    // Mock geolocation API
    mockGeolocation = {
      getCurrentPosition: vi.fn()
    };

    Object.defineProperty(global.navigator, 'geolocation', {
      value: mockGeolocation,
      writable: true,
      configurable: true
    });

    // Mock getUserMedia
    const mockGetUserMedia = vi.fn().mockResolvedValue({
      getTracks: () => [{ stop: vi.fn() }]
    });

    Object.defineProperty(global.navigator, 'mediaDevices', {
      value: {
        getUserMedia: mockGetUserMedia
      },
      writable: true,
      configurable: true
    });

    // Mock navigator properties
    Object.defineProperty(global.navigator, 'userAgent', {
      value: 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)',
      writable: true,
      configurable: true
    });

    Object.defineProperty(global.navigator, 'platform', {
      value: 'iPhone',
      writable: true,
      configurable: true
    });

    // Mock screen resolution
    Object.defineProperty(global.window, 'screen', {
      value: {
        width: 390,
        height: 844
      },
      writable: true,
      configurable: true
    });
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('should extract timestamp metadata when capturing photo', async () => {
    // Mock GPS to return immediately (no GPS data)
    mockGeolocation.getCurrentPosition.mockImplementation((success, error) => {
      error({ code: 1, message: 'User denied geolocation' });
    });

    render(<Camera onCapture={mockOnCapture} />);

    // Start camera
    fireEvent.click(screen.getByText('Start Camera'));

    await waitFor(() => {
      expect(screen.getByText('Capture Reading')).toBeInTheDocument();
    });

    // Setup canvas mocking
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
      const beforeCapture = new Date().toISOString();
      fireEvent.click(screen.getByText('Capture Reading'));

      await waitFor(() => {
        expect(mockOnCapture).toHaveBeenCalledTimes(1);
        const [file, metadata] = mockOnCapture.mock.calls[0];
        
        // Verify metadata exists
        expect(metadata).toBeDefined();
        expect(metadata.timestamp).toBeDefined();
        
        // Verify timestamp is valid ISO string
        expect(() => new Date(metadata.timestamp)).not.toThrow();
        
        // Verify timestamp is recent (within 1 second of capture)
        const captureTime = new Date(metadata.timestamp).getTime();
        const beforeTime = new Date(beforeCapture).getTime();
        expect(captureTime).toBeGreaterThanOrEqual(beforeTime);
        expect(captureTime - beforeTime).toBeLessThan(1000);
      });
    }
  });

  it('should extract device metadata (userAgent, platform, screen resolution)', async () => {
    mockGeolocation.getCurrentPosition.mockImplementation((success, error) => {
      error({ code: 1, message: 'User denied geolocation' });
    });

    render(<Camera onCapture={mockOnCapture} />);

    fireEvent.click(screen.getByText('Start Camera'));

    await waitFor(() => {
      expect(screen.getByText('Capture Reading')).toBeInTheDocument();
    });

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

      fireEvent.click(screen.getByText('Capture Reading'));

      await waitFor(() => {
        expect(mockOnCapture).toHaveBeenCalledTimes(1);
        const [file, metadata] = mockOnCapture.mock.calls[0];
        
        // Verify device metadata
        expect(metadata.device).toBeDefined();
        expect(metadata.device.userAgent).toBe('Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)');
        expect(metadata.device.platform).toBe('iPhone');
        expect(metadata.device.screenResolution).toBe('390x844');
      });
    }
  });

  it('should extract GPS metadata when geolocation is available', async () => {
    // Mock successful GPS response
    const mockPosition: GeolocationPosition = {
      coords: {
        latitude: 40.4168,
        longitude: -3.7038,
        accuracy: 10,
        altitude: null,
        altitudeAccuracy: null,
        heading: null,
        speed: null
      },
      timestamp: Date.now()
    };

    mockGeolocation.getCurrentPosition.mockImplementation((success) => {
      success(mockPosition);
    });

    render(<Camera onCapture={mockOnCapture} />);

    // Wait for GPS to be acquired
    await waitFor(() => {
      expect(mockGeolocation.getCurrentPosition).toHaveBeenCalled();
    });

    fireEvent.click(screen.getByText('Start Camera'));

    await waitFor(() => {
      expect(screen.getByText('Capture Reading')).toBeInTheDocument();
    });

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

      fireEvent.click(screen.getByText('Capture Reading'));

      await waitFor(() => {
        expect(mockOnCapture).toHaveBeenCalledTimes(1);
        const [file, metadata] = mockOnCapture.mock.calls[0];
        
        // Verify GPS metadata
        expect(metadata.gps).toBeDefined();
        expect(metadata.gps?.latitude).toBe(40.4168);
        expect(metadata.gps?.longitude).toBe(-3.7038);
        expect(metadata.gps?.accuracy).toBe(10);
      });
    }
  });

  it('should handle GPS unavailable gracefully (no GPS in metadata)', async () => {
    // Mock GPS error
    mockGeolocation.getCurrentPosition.mockImplementation((success, error) => {
      error({
        code: 1,
        message: 'User denied geolocation',
        PERMISSION_DENIED: 1,
        POSITION_UNAVAILABLE: 2,
        TIMEOUT: 3
      });
    });

    render(<Camera onCapture={mockOnCapture} />);

    fireEvent.click(screen.getByText('Start Camera'));

    await waitFor(() => {
      expect(screen.getByText('Capture Reading')).toBeInTheDocument();
    });

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

      fireEvent.click(screen.getByText('Capture Reading'));

      await waitFor(() => {
        expect(mockOnCapture).toHaveBeenCalledTimes(1);
        const [file, metadata] = mockOnCapture.mock.calls[0];
        
        // Verify GPS is undefined when unavailable
        expect(metadata.gps).toBeUndefined();
        
        // But other metadata should still be present
        expect(metadata.timestamp).toBeDefined();
        expect(metadata.device).toBeDefined();
      });
    }
  });

  it('should request GPS with high accuracy settings', async () => {
    mockGeolocation.getCurrentPosition.mockImplementation((success, error) => {
      error({ code: 1, message: 'User denied geolocation' });
    });

    render(<Camera onCapture={mockOnCapture} />);

    await waitFor(() => {
      expect(mockGeolocation.getCurrentPosition).toHaveBeenCalledWith(
        expect.any(Function),
        expect.any(Function),
        {
          enableHighAccuracy: true,
          timeout: 5000,
          maximumAge: 0
        }
      );
    });
  });

  it('should include all metadata fields in correct structure', async () => {
    const mockPosition: GeolocationPosition = {
      coords: {
        latitude: 28.6139,
        longitude: 77.2090,
        accuracy: 15,
        altitude: null,
        altitudeAccuracy: null,
        heading: null,
        speed: null
      },
      timestamp: Date.now()
    };

    mockGeolocation.getCurrentPosition.mockImplementation((success) => {
      success(mockPosition);
    });

    render(<Camera onCapture={mockOnCapture} />);

    await waitFor(() => {
      expect(mockGeolocation.getCurrentPosition).toHaveBeenCalled();
    });

    fireEvent.click(screen.getByText('Start Camera'));

    await waitFor(() => {
      expect(screen.getByText('Capture Reading')).toBeInTheDocument();
    });

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

      fireEvent.click(screen.getByText('Capture Reading'));

      await waitFor(() => {
        expect(mockOnCapture).toHaveBeenCalledTimes(1);
        const [file, metadata] = mockOnCapture.mock.calls[0];
        
        // Verify complete metadata structure
        expect(metadata).toMatchObject({
          timestamp: expect.any(String),
          gps: {
            latitude: 28.6139,
            longitude: 77.2090,
            accuracy: 15
          },
          device: {
            userAgent: expect.any(String),
            platform: expect.any(String),
            screenResolution: expect.any(String)
          }
        });
      });
    }
  });

  it('should handle browser without geolocation API', async () => {
    // Remove geolocation from navigator
    Object.defineProperty(global.navigator, 'geolocation', {
      value: undefined,
      writable: true,
      configurable: true
    });

    render(<Camera onCapture={mockOnCapture} />);

    fireEvent.click(screen.getByText('Start Camera'));

    await waitFor(() => {
      expect(screen.getByText('Capture Reading')).toBeInTheDocument();
    });

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

      fireEvent.click(screen.getByText('Capture Reading'));

      await waitFor(() => {
        expect(mockOnCapture).toHaveBeenCalledTimes(1);
        const [file, metadata] = mockOnCapture.mock.calls[0];
        
        // Should still have timestamp and device metadata
        expect(metadata.timestamp).toBeDefined();
        expect(metadata.device).toBeDefined();
        expect(metadata.gps).toBeUndefined();
      });
    }
  });
});
