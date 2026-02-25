import { describe, it, expect } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { VerificationResult, VerificationResultData } from '../VerificationResult';

describe('VerificationResult - Fraud Score Display', () => {
  const baseData: VerificationResultData = {
    reading: 5142.7,
    previousReading: 5000.0,
    consumption: 142.7,
    confidence: 0.96,
    status: 'VERIFIED',
    fraudScore: 0.0,
    bill: {
      baseCharge: 50.0,
      taxes: 10.5,
      total: 60.5,
      currency: 'EUR',
    },
  };

  it('should NOT show fraud score when score is 0 and status is VERIFIED', () => {
    render(<VerificationResult data={baseData} />);
    
    // Fraud score section should not be present
    expect(screen.queryByText('Fraud Score')).not.toBeInTheDocument();
  });

  it('should show fraud score when score is greater than 0', () => {
    const dataWithFraudScore: VerificationResultData = {
      ...baseData,
      fraudScore: 0.25,
    };
    
    render(<VerificationResult data={dataWithFraudScore} />);
    
    // Fraud score section should be present
    expect(screen.getByText('Fraud Score')).toBeInTheDocument();
    expect(screen.getByText('0.25 (Low Risk)')).toBeInTheDocument();
  });

  it('should show fraud score when there are fraud flags', () => {
    const dataWithFlags: VerificationResultData = {
      ...baseData,
      fraudScore: 0.0,
      fraudFlags: ['MISSING_METADATA', 'OLD_IMAGE'],
    };
    
    render(<VerificationResult data={dataWithFlags} />);
    
    // Fraud score section should be present
    expect(screen.getByText('Fraud Score')).toBeInTheDocument();
    expect(screen.getByText('Detected Issues:')).toBeInTheDocument();
    expect(screen.getByText('MISSING_METADATA')).toBeInTheDocument();
    expect(screen.getByText('OLD_IMAGE')).toBeInTheDocument();
  });

  it('should show fraud score when status is WARNING', () => {
    const dataWithWarning: VerificationResultData = {
      ...baseData,
      status: 'WARNING',
      fraudScore: 0.0,
    };
    
    render(<VerificationResult data={dataWithWarning} />);
    
    // Fraud score section should be present
    expect(screen.getByText('Fraud Score')).toBeInTheDocument();
  });

  it('should show fraud score when status is DISCREPANCY', () => {
    const dataWithDiscrepancy: VerificationResultData = {
      ...baseData,
      status: 'DISCREPANCY',
      fraudScore: 0.0,
    };
    
    render(<VerificationResult data={dataWithDiscrepancy} />);
    
    // Fraud score section should be present
    expect(screen.getByText('Fraud Score')).toBeInTheDocument();
  });

  it('should show fraud score when status is FRAUD_DETECTED', () => {
    const dataWithFraud: VerificationResultData = {
      ...baseData,
      status: 'FRAUD_DETECTED',
      fraudScore: 0.85,
      fraudFlags: ['LOCALIZED_MANIPULATION', 'SUSPICIOUS_GPS'],
    };
    
    render(<VerificationResult data={dataWithFraud} />);
    
    // Fraud score section should be present
    expect(screen.getByText('Fraud Score')).toBeInTheDocument();
    expect(screen.getByText('0.85 (High Risk)')).toBeInTheDocument();
    expect(screen.getByText('LOCALIZED_MANIPULATION')).toBeInTheDocument();
    expect(screen.getByText('SUSPICIOUS_GPS')).toBeInTheDocument();
  });

  it('should display correct fraud score labels', () => {
    // Low Risk
    const lowRiskData: VerificationResultData = {
      ...baseData,
      fraudScore: 0.2,
    };
    const { rerender } = render(<VerificationResult data={lowRiskData} />);
    expect(screen.getByText(/Low Risk/)).toBeInTheDocument();

    // Medium Risk
    const mediumRiskData: VerificationResultData = {
      ...baseData,
      fraudScore: 0.5,
    };
    rerender(<VerificationResult data={mediumRiskData} />);
    expect(screen.getByText(/Medium Risk/)).toBeInTheDocument();

    // High Risk
    const highRiskData: VerificationResultData = {
      ...baseData,
      fraudScore: 0.8,
    };
    rerender(<VerificationResult data={highRiskData} />);
    expect(screen.getByText(/High Risk/)).toBeInTheDocument();
  });

  it('should show "All validation checks passed" when no fraud flags', () => {
    const dataWithScore: VerificationResultData = {
      ...baseData,
      fraudScore: 0.15,
      fraudFlags: [],
    };
    
    render(<VerificationResult data={dataWithScore} />);
    
    expect(screen.getByText('All validation checks passed. No anomalies detected.')).toBeInTheDocument();
  });
});

describe('VerificationResult - View Details Modal', () => {
  const detailedData: VerificationResultData = {
    reading: 5142.7,
    previousReading: 5000.0,
    consumption: 142.7,
    confidence: 0.96,
    status: 'VERIFIED',
    fraudScore: 0.12,
    fraudFlags: ['MINOR_INCONSISTENCY'],
    ocrEngine: 'tesseract',
    rawOcrText: '5142.7 kWh',
    imageIpfsHash: 'QmXyz123abc',
    imageMetadata: {
      gpsCoordinates: '40.4168,-3.7038',
      timestamp: '2024-02-18T10:30:00Z',
      deviceId: 'device-123',
    },
    bill: {
      baseCharge: 50.0,
      taxes: 10.5,
      total: 60.5,
      currency: 'EUR',
      breakdown: [
        { description: 'Energy Charge', amount: 40.0 },
        { description: 'Distribution Charge', amount: 10.0 },
        { description: 'VAT (21%)', amount: 10.5 },
      ],
    },
    hcsSequenceNumber: 12345,
    hcsTopicId: '0.0.TOPIC_EU',
  };

  it('should render View Details button', () => {
    render(<VerificationResult data={detailedData} />);
    
    expect(screen.getByRole('button', { name: /view details/i })).toBeInTheDocument();
  });

  it('should open modal when View Details button is clicked', async () => {
    render(<VerificationResult data={detailedData} />);
    
    const viewDetailsButton = screen.getByRole('button', { name: /view details/i });
    fireEvent.click(viewDetailsButton);
    
    await waitFor(() => {
      expect(screen.getByRole('dialog')).toBeInTheDocument();
      expect(screen.getByText('Verification Details')).toBeInTheDocument();
    });
  });

  it('should display OCR analysis details in modal', async () => {
    render(<VerificationResult data={detailedData} />);
    
    const viewDetailsButton = screen.getByRole('button', { name: /view details/i });
    fireEvent.click(viewDetailsButton);
    
    await waitFor(() => {
      const dialog = screen.getByRole('dialog');
      expect(dialog).toBeInTheDocument();
      // Look for the heading specifically
      const headings = screen.getAllByRole('heading', { level: 3 });
      const ocrHeading = headings.find(h => h.textContent === 'OCR Analysis');
      expect(ocrHeading).toBeInTheDocument();
      expect(screen.getByText('Tesseract.js (Client-side)')).toBeInTheDocument();
      expect(screen.getByText('96.0%')).toBeInTheDocument();
      expect(screen.getByText('Raw OCR Text:')).toBeInTheDocument();
      expect(screen.getByText('5142.7 kWh')).toBeInTheDocument();
    });
  });

  it('should display fraud detection details in modal', async () => {
    render(<VerificationResult data={detailedData} />);
    
    const viewDetailsButton = screen.getByRole('button', { name: /view details/i });
    fireEvent.click(viewDetailsButton);
    
    await waitFor(() => {
      const dialog = screen.getByRole('dialog');
      expect(dialog).toBeInTheDocument();
      // Look for the heading specifically
      const headings = screen.getAllByRole('heading', { level: 3 });
      const fraudHeading = headings.find(h => h.textContent === 'Fraud Detection');
      expect(fraudHeading).toBeInTheDocument();
      expect(screen.getByText('0.12')).toBeInTheDocument();
      // Use getAllByText since it appears in both the main view and modal
      const inconsistencyTexts = screen.getAllByText('MINOR_INCONSISTENCY');
      expect(inconsistencyTexts.length).toBeGreaterThan(0);
    });
  });

  it('should display image metadata in modal', async () => {
    render(<VerificationResult data={detailedData} />);
    
    const viewDetailsButton = screen.getByRole('button', { name: /view details/i });
    fireEvent.click(viewDetailsButton);
    
    await waitFor(() => {
      expect(screen.getByText(/image metadata/i)).toBeInTheDocument();
      expect(screen.getByText('40.4168,-3.7038')).toBeInTheDocument();
      expect(screen.getByText('device-123')).toBeInTheDocument();
      expect(screen.getByText('IPFS Hash:')).toBeInTheDocument();
      expect(screen.getByText('QmXyz123abc')).toBeInTheDocument();
    });
  });

  it('should display blockchain proof in modal', async () => {
    render(<VerificationResult data={detailedData} />);
    
    const viewDetailsButton = screen.getByRole('button', { name: /view details/i });
    fireEvent.click(viewDetailsButton);
    
    await waitFor(() => {
      const dialog = screen.getByRole('dialog');
      expect(dialog).toBeInTheDocument();
      // Check within the dialog for blockchain proof section
      expect(screen.getByText('0.0.TOPIC_EU')).toBeInTheDocument();
      expect(screen.getByText('#12345')).toBeInTheDocument();
      expect(screen.getByText('View on HashScan')).toBeInTheDocument();
    });
  });

  it('should display billing breakdown in modal', async () => {
    render(<VerificationResult data={detailedData} />);
    
    const viewDetailsButton = screen.getByRole('button', { name: /view details/i });
    fireEvent.click(viewDetailsButton);
    
    await waitFor(() => {
      const dialog = screen.getByRole('dialog');
      expect(dialog).toBeInTheDocument();
      // Check for all breakdown items within the dialog
      const energyCharges = screen.getAllByText('Energy Charge');
      expect(energyCharges.length).toBeGreaterThan(0);
      expect(screen.getAllByText('Distribution Charge').length).toBeGreaterThan(0);
      expect(screen.getAllByText('VAT (21%)').length).toBeGreaterThan(0);
    });
  });

  it('should handle missing optional data gracefully', async () => {
    const minimalData: VerificationResultData = {
      reading: 5142.7,
      confidence: 0.96,
      status: 'VERIFIED',
      fraudScore: 0.0,
    };
    
    render(<VerificationResult data={minimalData} />);
    
    const viewDetailsButton = screen.getByRole('button', { name: /view details/i });
    fireEvent.click(viewDetailsButton);
    
    await waitFor(() => {
      const dialog = screen.getByRole('dialog');
      expect(dialog).toBeInTheDocument();
      // Should not crash and should show available data
      // Look for the heading specifically
      const headings = screen.getAllByRole('heading', { level: 3 });
      const ocrHeading = headings.find(h => h.textContent === 'OCR Analysis');
      expect(ocrHeading).toBeInTheDocument();
    });
  });

  it('should display Google Vision API when ocrEngine is google_vision', async () => {
    const googleVisionData: VerificationResultData = {
      ...detailedData,
      ocrEngine: 'google_vision',
    };
    
    render(<VerificationResult data={googleVisionData} />);
    
    const viewDetailsButton = screen.getByRole('button', { name: /view details/i });
    fireEvent.click(viewDetailsButton);
    
    await waitFor(() => {
      expect(screen.getByText('Google Vision API (Server-side)')).toBeInTheDocument();
    });
  });

  it('should close modal when close button is clicked', async () => {
    render(<VerificationResult data={detailedData} />);
    
    const viewDetailsButton = screen.getByRole('button', { name: /view details/i });
    fireEvent.click(viewDetailsButton);
    
    await waitFor(() => {
      expect(screen.getByRole('dialog')).toBeInTheDocument();
    });
    
    // Find and click the close button (X button in dialog)
    const closeButton = screen.getByRole('button', { name: /close/i });
    fireEvent.click(closeButton);
    
    await waitFor(() => {
      expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
    });
  });

  it('should render external links correctly', async () => {
    render(<VerificationResult data={detailedData} />);
    
    const viewDetailsButton = screen.getByRole('button', { name: /view details/i });
    fireEvent.click(viewDetailsButton);
    
    await waitFor(() => {
      const hashScanLink = screen.getByText('View on HashScan').closest('a');
      expect(hashScanLink).toHaveAttribute('href', 'https://hashscan.io/testnet/topic/0.0.TOPIC_EU');
      expect(hashScanLink).toHaveAttribute('target', '_blank');
      expect(hashScanLink).toHaveAttribute('rel', 'noopener noreferrer');
    });
  });
});
