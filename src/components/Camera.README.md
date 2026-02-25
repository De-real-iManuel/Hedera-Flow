# Camera Component

A React component that provides video stream access for capturing meter readings with alignment guides and error handling.

## Features

- ✅ Real-time video stream from device camera
- ✅ Automatic back camera selection on mobile devices (environment facing mode)
- ✅ Visual alignment guides for meter positioning
- ✅ High-quality image capture (1920x1080 ideal resolution)
- ✅ Error handling for camera permission denials
- ✅ Cleanup on component unmount
- ✅ Optional close button
- ✅ Responsive design with Tailwind CSS

## Usage

### Basic Usage

```tsx
import { Camera } from '@/components/Camera';

function MyPage() {
  const handleCapture = (file: File) => {
    console.log('Captured image:', file);
    // Process the captured image
  };

  return <Camera onCapture={handleCapture} />;
}
```

### With Close Button

```tsx
import { Camera } from '@/components/Camera';

function MyPage() {
  const [showCamera, setShowCamera] = useState(false);

  const handleCapture = (file: File) => {
    console.log('Captured image:', file);
    setShowCamera(false);
  };

  const handleClose = () => {
    setShowCamera(false);
  };

  return (
    <>
      {showCamera ? (
        <Camera onCapture={handleCapture} onClose={handleClose} />
      ) : (
        <button onClick={() => setShowCamera(true)}>Open Camera</button>
      )}
    </>
  );
}
```

## Props

| Prop | Type | Required | Description |
|------|------|----------|-------------|
| `onCapture` | `(file: File) => void` | Yes | Callback function called when an image is captured. Receives a File object with JPEG format. |
| `onClose` | `() => void` | No | Optional callback for closing the camera. When provided, displays a close button in the top-right corner. |

## Camera Specifications

- **Video Resolution**: 1920x1080 (ideal)
- **Camera Mode**: Environment (back camera on mobile)
- **Image Format**: JPEG
- **Image Quality**: 95%
- **Aspect Ratio**: 4:3

## Browser Compatibility

The component uses the MediaDevices API which is supported in:
- Chrome 53+
- Firefox 36+
- Safari 11+
- Edge 12+

**Note**: HTTPS is required for camera access in production environments.

## Error Handling

The component handles the following error scenarios:

1. **Camera Permission Denied**: Shows an error message with a "Try Again" button
2. **No Camera Available**: Displays appropriate error message
3. **Stream Interruption**: Automatically cleans up resources

## Component States

1. **Inactive**: Shows "Start Camera" button
2. **Active**: Shows video stream with alignment guides and "Capture Reading" + "Cancel" buttons
3. **Error**: Shows error message with retry option

## Alignment Guides

The component displays visual guides to help users position the meter correctly:
- Dashed border frame
- Corner markers (L-shaped borders)
- Centered instruction text

## Cleanup

The component automatically stops the camera stream when:
- Component unmounts
- User clicks "Cancel"
- User clicks "Close" (if onClose prop provided)
- Image is successfully captured

## Testing

The component includes comprehensive unit tests covering:
- Rendering states
- Camera access requests
- Error handling
- User interactions
- Cleanup behavior

Run tests with:
```bash
npm test -- Camera.test.tsx
```

## Example Integration

See `src/pages/ScanPage.tsx` for a complete example of integrating the Camera component with OCR processing and result display.

## Styling

The component uses Tailwind CSS classes and expects the following custom classes to be defined:
- `gradient-accent`: Gradient background for primary button
- `tap-scale`: Scale animation on tap/click
- `accent`: Accent color for borders and highlights
- `success`: Success color for capture button

## Future Enhancements

Potential improvements for future versions:
- Flash/torch control
- Zoom controls
- Multiple camera selection
- Photo preview before confirmation
- Image filters/preprocessing
- Burst mode for multiple captures
