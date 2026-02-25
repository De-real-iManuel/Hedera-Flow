'use client';

import { useRef, useState, useEffect } from 'react';
import { Camera as CameraIcon, X } from 'lucide-react';

export interface ImageMetadata {
  timestamp: string;
  gps?: {
    latitude: number;
    longitude: number;
    accuracy?: number;
  };
  device: {
    userAgent: string;
    platform: string;
    screenResolution: string;
  };
}

interface CameraProps {
  onCapture: (file: File, metadata?: ImageMetadata) => void;
  onClose?: () => void;
}

export function Camera({ onCapture, onClose }: CameraProps) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [stream, setStream] = useState<MediaStream | null>(null);
  const [isActive, setIsActive] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [gpsPosition, setGpsPosition] = useState<GeolocationPosition | null>(null);
  const [permissionState, setPermissionState] = useState<PermissionState | 'unknown'>('unknown');

  // Request GPS permission when component mounts
  useEffect(() => {
    if ('geolocation' in navigator && navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          setGpsPosition(position);
        },
        (error) => {
          console.warn('GPS access denied or unavailable:', error);
          // GPS is optional, so we don't show an error to the user
        },
        {
          enableHighAccuracy: true,
          timeout: 5000,
          maximumAge: 0
        }
      );
    }
  }, []);

  // Check camera permission status on mount
  useEffect(() => {
    const checkCameraPermission = async () => {
      try {
        // Check if Permissions API is supported
        if ('permissions' in navigator) {
          const result = await navigator.permissions.query({ name: 'camera' as PermissionName });
          setPermissionState(result.state);
          
          // Listen for permission changes
          result.addEventListener('change', () => {
            setPermissionState(result.state);
          });
        }
      } catch (err) {
        // Permissions API not supported or query failed
        console.warn('Unable to check camera permission:', err);
        setPermissionState('unknown');
      }
    };

    checkCameraPermission();
  }, []);

  const extractMetadata = (): ImageMetadata => {
    const metadata: ImageMetadata = {
      timestamp: new Date().toISOString(),
      device: {
        userAgent: navigator.userAgent,
        platform: navigator.platform,
        screenResolution: `${window.screen.width}x${window.screen.height}`
      }
    };

    // Add GPS data if available
    if (gpsPosition) {
      metadata.gps = {
        latitude: gpsPosition.coords.latitude,
        longitude: gpsPosition.coords.longitude,
        accuracy: gpsPosition.coords.accuracy
      };
    }

    return metadata;
  };

  const startCamera = async () => {
    try {
      setError(null);
      
      // Check if getUserMedia is supported
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        setError('Camera is not supported on this device or browser. Please use a modern browser like Chrome or Safari.');
        return;
      }

      const mediaStream = await navigator.mediaDevices.getUserMedia({
        video: { 
          facingMode: 'environment', // Use back camera on mobile
          width: { ideal: 1920 },
          height: { ideal: 1080 }
        }
      });
      
      if (videoRef.current) {
        videoRef.current.srcObject = mediaStream;
        setStream(mediaStream);
        setIsActive(true);
      }
    } catch (err) {
      console.error('Camera access error:', err);
      handleCameraError(err);
    }
  };

  const handleCameraError = (err: unknown) => {
    // Check if it's a DOMException with a name property
    const error = err as { name?: string; message?: string };
    
    if (!error || !error.name) {
      setError('An unexpected error occurred while accessing the camera. Please try again.');
      return;
    }
    
    switch (error.name) {
      case 'NotAllowedError':
      case 'PermissionDeniedError':
        setError('Camera access denied. Please allow camera access in your browser settings and try again.');
        break;
      
      case 'NotFoundError':
      case 'DevicesNotFoundError':
        setError('No camera found on this device. Please ensure your device has a working camera.');
        break;
      
      case 'NotReadableError':
      case 'TrackStartError':
        setError('Camera is already in use by another application. Please close other apps using the camera and try again.');
        break;
      
      case 'OverconstrainedError':
      case 'ConstraintNotSatisfiedError':
        setError('Camera does not meet the required specifications. Try using a different device or camera.');
        break;
      
      case 'TypeError':
        setError('Camera access is not supported on this device or browser. Please use a modern browser like Chrome or Safari.');
        break;
      
      case 'AbortError':
        setError('Camera access was interrupted. Please try again.');
        break;
      
      case 'SecurityError':
        setError('Camera access blocked due to security settings. Please ensure you are using HTTPS or localhost.');
        break;
      
      default:
        setError('Unable to access camera. Please check your browser permissions and try again.');
    }
  };

  const stopCamera = () => {
    if (stream) {
      stream.getTracks().forEach(track => track.stop());
      setStream(null);
      setIsActive(false);
    }
  };

  const capture = () => {
    if (videoRef.current && canvasRef.current) {
      const context = canvasRef.current.getContext('2d');
      if (!context) return;

      // Set canvas dimensions to match video
      canvasRef.current.width = videoRef.current.videoWidth;
      canvasRef.current.height = videoRef.current.videoHeight;
      
      // Draw current video frame to canvas
      context.drawImage(videoRef.current, 0, 0);
      
      // Extract metadata
      const metadata = extractMetadata();
      
      // Convert canvas to blob and create file
      canvasRef.current.toBlob((blob) => {
        if (blob) {
          const file = new File([blob], `meter-${Date.now()}.jpg`, { type: 'image/jpeg' });
          onCapture(file, metadata);
          stopCamera();
        }
      }, 'image/jpeg', 0.95);
    }
  };

  const handleClose = () => {
    stopCamera();
    onClose?.();
  };

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      stopCamera();
    };
  }, []);

  return (
    <div className="relative w-full">
      {/* Video Stream */}
      <div className="relative aspect-[4/3] rounded-3xl overflow-hidden bg-black">
        <video 
          ref={videoRef} 
          autoPlay 
          playsInline
          muted
          className="w-full h-full object-cover"
        />
        
        {/* Hidden canvas for capture */}
        <canvas ref={canvasRef} className="hidden" />
        
        {/* Alignment Guide Overlay */}
        {isActive && (
          <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
            <div className="absolute inset-6 border-2 border-dashed border-accent/50 rounded-2xl" />
            <div className="absolute top-6 left-6 w-6 h-6 border-t-2 border-l-2 border-accent rounded-tl-lg" />
            <div className="absolute top-6 right-6 w-6 h-6 border-t-2 border-r-2 border-accent rounded-tr-lg" />
            <div className="absolute bottom-6 left-6 w-6 h-6 border-b-2 border-l-2 border-accent rounded-bl-lg" />
            <div className="absolute bottom-6 right-6 w-6 h-6 border-b-2 border-r-2 border-accent rounded-br-lg" />
            
            <div className="text-center z-10 bg-black/50 px-4 py-2 rounded-lg">
              <p className="text-sm text-white">Position meter display in frame</p>
            </div>
          </div>
        )}

        {/* Error Message */}
        {error && (
          <div className="absolute inset-0 flex items-center justify-center bg-black/90 p-6">
            <div className="text-center max-w-sm">
              {/* Error Icon */}
              <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-red-500/20 flex items-center justify-center">
                <svg 
                  className="w-8 h-8 text-red-500" 
                  fill="none" 
                  stroke="currentColor" 
                  viewBox="0 0 24 24"
                >
                  <path 
                    strokeLinecap="round" 
                    strokeLinejoin="round" 
                    strokeWidth={2} 
                    d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" 
                  />
                </svg>
              </div>
              
              {/* Error Message */}
              <p className="text-white text-sm mb-6 leading-relaxed">{error}</p>
              
              {/* Help Text */}
              {error.includes('denied') && (
                <div className="mb-6 p-3 bg-white/10 rounded-lg text-left">
                  <p className="text-white text-xs font-semibold mb-2">How to enable camera:</p>
                  <ul className="text-white/80 text-xs space-y-1 list-disc list-inside">
                    <li>Tap the lock icon in your browser's address bar</li>
                    <li>Find "Camera" in the permissions list</li>
                    <li>Change setting to "Allow"</li>
                    <li>Refresh the page and try again</li>
                  </ul>
                </div>
              )}
              
              {error.includes('in use') && (
                <div className="mb-6 p-3 bg-white/10 rounded-lg text-left">
                  <p className="text-white text-xs font-semibold mb-2">Camera is busy:</p>
                  <ul className="text-white/80 text-xs space-y-1 list-disc list-inside">
                    <li>Close other apps using the camera</li>
                    <li>Close other browser tabs with camera access</li>
                    <li>Restart your browser if the issue persists</li>
                  </ul>
                </div>
              )}
              
              {error.includes('HTTPS') && (
                <div className="mb-6 p-3 bg-white/10 rounded-lg text-left">
                  <p className="text-white text-xs font-semibold mb-2">Security requirement:</p>
                  <p className="text-white/80 text-xs">
                    Camera access requires a secure connection (HTTPS). Please access the app via HTTPS or localhost.
                  </p>
                </div>
              )}
              
              {/* Action Buttons */}
              <div className="flex gap-2">
                <button
                  onClick={startCamera}
                  className="flex-1 px-4 py-3 bg-accent hover:bg-accent/90 text-white rounded-lg text-sm font-medium transition-colors"
                >
                  Try Again
                </button>
                {onClose && (
                  <button
                    onClick={handleClose}
                    className="px-4 py-3 bg-white/10 hover:bg-white/20 text-white rounded-lg text-sm font-medium transition-colors"
                  >
                    Cancel
                  </button>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Close Button */}
        {onClose && (
          <button
            onClick={handleClose}
            className="absolute top-4 right-4 w-10 h-10 bg-black/50 hover:bg-black/70 rounded-full flex items-center justify-center transition-colors z-20"
            aria-label="Close camera"
          >
            <X className="w-5 h-5 text-white" />
          </button>
        )}
      </div>

      {/* Camera Instructions */}
      {!isActive && !error && (
        <>
          {permissionState === 'denied' && (
            <div className="mb-3 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
              <div className="flex items-start gap-2">
                <svg 
                  className="w-5 h-5 text-yellow-600 flex-shrink-0 mt-0.5" 
                  fill="none" 
                  stroke="currentColor" 
                  viewBox="0 0 24 24"
                >
                  <path 
                    strokeLinecap="round" 
                    strokeLinejoin="round" 
                    strokeWidth={2} 
                    d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" 
                  />
                </svg>
                <div className="flex-1">
                  <p className="text-sm font-medium text-yellow-800 mb-1">Camera access is blocked</p>
                  <p className="text-xs text-yellow-700">
                    Please enable camera access in your browser settings to capture meter readings.
                  </p>
                </div>
              </div>
            </div>
          )}
          
          <p className="text-center text-xs text-muted-foreground mt-3">
            Hold steady over the digital display for best results
          </p>
        </>
      )}
      
      {/* Control Buttons */}
      <div className="flex gap-3 mt-4">
        {!isActive ? (
          <button 
            onClick={startCamera}
            className={`flex-1 py-4 rounded-2xl font-semibold text-base flex items-center justify-center gap-2 tap-scale transition-colors ${
              permissionState === 'denied' 
                ? 'bg-yellow-500 hover:bg-yellow-600 text-white' 
                : 'gradient-accent text-accent-foreground'
            }`}
          >
            <CameraIcon className="w-5 h-5" />
            {permissionState === 'denied' ? 'Enable Camera Access' : 'Start Camera'}
          </button>
        ) : (
          <>
            <button 
              onClick={capture}
              className="flex-1 py-4 rounded-2xl bg-success hover:bg-success/90 text-white font-semibold text-base transition-colors tap-scale"
            >
              Capture Reading
            </button>
            <button 
              onClick={stopCamera}
              className="px-6 py-4 rounded-2xl border border-border text-foreground font-medium text-base hover:bg-muted transition-colors tap-scale"
            >
              Cancel
            </button>
          </>
        )}
      </div>
    </div>
  );
}
