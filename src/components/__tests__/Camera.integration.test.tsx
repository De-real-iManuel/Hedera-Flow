import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { Camera } from '../Camera';

describe('Camera - Integration Test: Complete Capture Flow', () => {
  const mockOnCapture = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should complete full photo capture workflow: start → capture → file creation', async () => {
    // Setup: Mock getUserMedia
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

    // Render component
    render(<Camera onCapture={mockOnCapture} />);

    // Step 1: Verify initial state
    expect(screen.getByText('Start Camera')).toBeInTheDocument();
    expect(screen.getByText(/Hold steady over the digital display/i)).toBeInTheDocument();

    // Step 2: Start camera
    const startButton = screen.getByText('Start Camera');
    fireEvent.click(startButton);

    // Step 3: Wait for camera to activate
    await waitFor(() => {
      expect(mockGetUserMedia).toHaveBeenCalledWith({
        video: {
          facingMode: 'environment',
          width: { ideal: 1920 },
          height: { ideal: 1080 }
        }
      });
      expect(screen.getByText('Capture Reading')).toBeInTheDocument();
      expect(screen.getByText('Cancel')).toBeInTheDocument();
    });

    // Step 4: Verify alignment guide is shown
    expect(screen.getByText('Position meter display in frame')).toBeInTheDocument();

    // Step 5: Setup canvas mocking for capture
    const component = screen.getByText('Capture Reading').closest('div')?.parentElement;
    const videoRef = component?.querySelector('video');
    const canvasRef = component?.querySelector('canvas');

    if (videoRef && canvasRef) {
      // Mock video dimensions
      Object.defineProperty(videoRef, 'videoWidth', { value: 1920 });
      Object.defineProperty(videoRef, 'videoHeight', { value: 1080 });

      // Mock canvas context
      const mockContext = {
        drawImage: vi.fn(),
      } as unknown as CanvasRenderingContext2D;

      canvasRef.getContext = vi.fn().mockReturnValue(mockContext);
      canvasRef.toBlob = vi.fn((callback) => {
        const blob = new Blob(['fake-meter-image-data'], { type: 'image/jpeg' });
        callback(blob);
      });

      // Step 6: Capture photo
      const captureButton = screen.getByText('Capture Reading');
      fireEvent.click(captureButton);

      // Step 7: Verify capture workflow
      await waitFor(() => {
        // Canvas dimensions set correctly
        expect(canvasRef.width).toBe(1920);
        expect(canvasRef.height).toBe(1080);

        // Video frame drawn to canvas
        expect(mockContext.drawImage).toHaveBeenCalledWith(videoRef, 0, 0);

        // File created and callback invoked
        expect(mockOnCapture).toHaveBeenCalledTimes(1);
        const capturedFile = mockOnCapture.mock.calls[0][0];
        
        // Verify File object properties
        expect(capturedFile).toBeInstanceOf(File);
        expect(capturedFile.type).toBe('image/jpeg');
        expect(capturedFile.name).toMatch(/^meter-\d+\.jpg$/);
        expect(capturedFile.size).toBeGreaterThan(0);

        // Camera stopped after capture
        expect(mockTrack.stop).toHaveBeenCalled();
      });

      // Step 8: Verify UI returns to initial state
      await waitFor(() => {
        expect(screen.getByText('Start Camera')).toBeInTheDocument();
      });
    }
  });

  it('should handle capture with different video dimensions', async () => {
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

    // Start camera
    fireEvent.click(screen.getByText('Start Camera'));

    await waitFor(() => {
      expect(screen.getByText('Capture Reading')).toBeInTheDocument();
    });

    // Test with different dimensions (e.g., mobile portrait)
    const component = screen.getByText('Capture Reading').closest('div')?.parentElement;
    const videoRef = component?.querySelector('video');
    const canvasRef = component?.querySelector('canvas');

    if (videoRef && canvasRef) {
      Object.defineProperty(videoRef, 'videoWidth', { value: 720 });
      Object.defineProperty(videoRef, 'videoHeight', { value: 1280 });

      const mockContext = {
        drawImage: vi.fn(),
      } as unknown as CanvasRenderingContext2D;

      canvasRef.getContext = vi.fn().mockReturnValue(mockContext);
      canvasRef.toBlob = vi.fn((callback) => {
        const blob = new Blob(['mobile-image-data'], { type: 'image/jpeg' });
        callback(blob);
      });

      fireEvent.click(screen.getByText('Capture Reading'));

      await waitFor(() => {
        // Canvas should match mobile dimensions
        expect(canvasRef.width).toBe(720);
        expect(canvasRef.height).toBe(1280);
        expect(mockOnCapture).toHaveBeenCalled();
      });
    }
  });

  it('should generate unique filenames for multiple captures', async () => {
    const mockGetUserMedia = vi.fn().mockResolvedValue({
      getTracks: () => [{ stop: vi.fn() }]
    });

    Object.defineProperty(global.navigator, 'mediaDevices', {
      value: {
        getUserMedia: mockGetUserMedia
      },
      writable: true
    });

    const capturedFiles: File[] = [];

    // First capture
    const { rerender } = render(<Camera onCapture={(file) => capturedFiles.push(file)} />);
    
    fireEvent.click(screen.getByText('Start Camera'));
    await waitFor(() => expect(screen.getByText('Capture Reading')).toBeInTheDocument());

    const component1 = screen.getByText('Capture Reading').closest('div')?.parentElement;
    const videoRef1 = component1?.querySelector('video');
    const canvasRef1 = component1?.querySelector('canvas');

    if (videoRef1 && canvasRef1) {
      Object.defineProperty(videoRef1, 'videoWidth', { value: 1920 });
      Object.defineProperty(videoRef1, 'videoHeight', { value: 1080 });

      const mockContext1 = { drawImage: vi.fn() } as unknown as CanvasRenderingContext2D;
      canvasRef1.getContext = vi.fn().mockReturnValue(mockContext1);
      canvasRef1.toBlob = vi.fn((callback) => {
        callback(new Blob(['data1'], { type: 'image/jpeg' }));
      });

      fireEvent.click(screen.getByText('Capture Reading'));
      await waitFor(() => expect(capturedFiles.length).toBe(1));
    }

    // Small delay to ensure different timestamp
    await new Promise(resolve => setTimeout(resolve, 10));

    // Second capture
    rerender(<Camera onCapture={(file) => capturedFiles.push(file)} />);
    
    fireEvent.click(screen.getByText('Start Camera'));
    await waitFor(() => expect(screen.getByText('Capture Reading')).toBeInTheDocument());

    const component2 = screen.getByText('Capture Reading').closest('div')?.parentElement;
    const videoRef2 = component2?.querySelector('video');
    const canvasRef2 = component2?.querySelector('canvas');

    if (videoRef2 && canvasRef2) {
      Object.defineProperty(videoRef2, 'videoWidth', { value: 1920 });
      Object.defineProperty(videoRef2, 'videoHeight', { value: 1080 });

      const mockContext2 = { drawImage: vi.fn() } as unknown as CanvasRenderingContext2D;
      canvasRef2.getContext = vi.fn().mockReturnValue(mockContext2);
      canvasRef2.toBlob = vi.fn((callback) => {
        callback(new Blob(['data2'], { type: 'image/jpeg' }));
      });

      fireEvent.click(screen.getByText('Capture Reading'));
      await waitFor(() => expect(capturedFiles.length).toBe(2));

      // Verify filenames are unique
      expect(capturedFiles[0].name).not.toBe(capturedFiles[1].name);
      expect(capturedFiles[0].name).toMatch(/^meter-\d+\.jpg$/);
      expect(capturedFiles[1].name).toMatch(/^meter-\d+\.jpg$/);
    }
  });
});
