/**
 * Cryptographic Service
 * 
 * Handles all cryptographic operations for smart meters:
 * - ED25519 keypair generation and management
 * - Consumption data signing and verification
 * - Secure key storage and retrieval
 * - Fraud detection through signature validation
 */

import { smartMeterApi } from '@/lib/api/smart-meter';

export interface KeyPair {
  publicKey: string;
  privateKey: string; // Never exposed to frontend in production
  algorithm: 'ED25519';
  created: string;
}

export interface ConsumptionSignatureData {
  meterId: string;
  consumption: number;
  timestamp: string;
  readingBefore: number;
  readingAfter: number;
}

export interface SignatureVerificationResult {
  valid: boolean;
  algorithm: string;
  publicKey: string;
  signature: string;
  data: ConsumptionSignatureData;
  error?: string;
}

export class CryptographicService {
  private keyCache: Map<string, KeyPair> = new Map();
  
  /**
   * Ensure a keypair exists for a meter (generate if needed)
   */
  async ensureKeypair(meterId: string): Promise<KeyPair> {
    // Check cache first
    const cached = this.keyCache.get(meterId);
    if (cached) {
      return cached;
    }

    try {
      // Try to get existing public key from backend
      const existingPublicKey = await smartMeterApi.getPublicKey(meterId);
      
      // Create keypair object (private key is managed by backend)
      const keypair: KeyPair = {
        publicKey: existingPublicKey,
        privateKey: '[MANAGED_BY_BACKEND]', // Never expose actual private key
        algorithm: 'ED25519',
        created: new Date().toISOString(),
      };
      
      this.keyCache.set(meterId, keypair);
      return keypair;
      
    } catch (error) {
      // Generate new keypair if none exists
      console.log(`Generating new keypair for meter ${meterId}`);
      return await this.generateKeypair(meterId);
    }
  }

  /**
   * Generate a new ED25519 keypair for a meter
   */
  async generateKeypair(meterId: string): Promise<KeyPair> {
    try {
      const response = await smartMeterApi.generateKeypair(meterId);
      
      const keypair: KeyPair = {
        publicKey: response.public_key,
        privateKey: '[MANAGED_BY_BACKEND]',
        algorithm: response.algorithm as 'ED25519',
        created: response.created_at,
      };
      
      // Cache the keypair
      this.keyCache.set(meterId, keypair);
      
      console.log(`✅ Generated ED25519 keypair for meter ${meterId}`);
      return keypair;
      
    } catch (error) {
      console.error(`Failed to generate keypair for meter ${meterId}:`, error);
      throw new Error(`Keypair generation failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  /**
   * Sign consumption data (mock implementation for frontend demo)
   * In production, this would be done by the smart meter's secure element
   */
  async signConsumption(data: ConsumptionSignatureData): Promise<string> {
    try {
      // Create deterministic signature data string
      const signatureData = this.createSignatureDataString(data);
      
      // Generate mock signature for demo purposes
      // In production, this would use the actual private key in a secure environment
      const mockSignature = await this.generateMockSignature(signatureData, data.meterId);
      
      console.log(`✅ Generated signature for meter ${data.meterId} consumption: ${data.consumption.toFixed(3)} kWh`);
      return mockSignature;
      
    } catch (error) {
      console.error(`Failed to sign consumption data for meter ${data.meterId}:`, error);
      throw new Error(`Signature generation failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  /**
   * Verify consumption signature
   */
  async verifySignature(
    data: ConsumptionSignatureData,
    signature: string,
    publicKey: string
  ): Promise<SignatureVerificationResult> {
    try {
      const verificationRequest = {
        meter_id: data.meterId,
        consumption_kwh: data.consumption,
        timestamp: data.timestamp,
        signature,
        public_key: publicKey,
      };
      
      const result = await smartMeterApi.verifySignature(verificationRequest);
      
      return {
        valid: result.valid,
        algorithm: result.algorithm,
        publicKey,
        signature,
        data,
        error: result.error,
      };
      
    } catch (error) {
      console.error(`Failed to verify signature for meter ${data.meterId}:`, error);
      return {
        valid: false,
        algorithm: 'ED25519',
        publicKey,
        signature,
        data,
        error: error instanceof Error ? error.message : 'Verification failed',
      };
    }
  }

  /**
   * Batch verify multiple signatures (for performance)
   */
  async batchVerifySignatures(
    verifications: Array<{
      data: ConsumptionSignatureData;
      signature: string;
      publicKey: string;
    }>
  ): Promise<SignatureVerificationResult[]> {
    // Process in parallel for better performance
    const verificationPromises = verifications.map(({ data, signature, publicKey }) =>
      this.verifySignature(data, signature, publicKey)
    );
    
    return await Promise.all(verificationPromises);
  }

  /**
   * Detect potential fraud based on signature patterns
   */
  async detectFraud(
    meterId: string,
    recentSignatures: Array<{
      data: ConsumptionSignatureData;
      signature: string;
      timestamp: string;
    }>
  ): Promise<{
    fraudDetected: boolean;
    confidence: number;
    reasons: string[];
    recommendations: string[];
  }> {
    const reasons: string[] = [];
    const recommendations: string[] = [];
    let suspiciousCount = 0;

    try {
      const keypair = await this.ensureKeypair(meterId);
      
      // Verify all recent signatures
      const verifications = await this.batchVerifySignatures(
        recentSignatures.map(sig => ({
          data: sig.data,
          signature: sig.signature,
          publicKey: keypair.publicKey,
        }))
      );
      
      // Check for invalid signatures
      const invalidSignatures = verifications.filter(v => !v.valid);
      if (invalidSignatures.length > 0) {
        suspiciousCount += invalidSignatures.length * 3; // High weight
        reasons.push(`${invalidSignatures.length} invalid signatures detected`);
        recommendations.push('Investigate meter tampering or key compromise');
      }
      
      // Check for unusual consumption patterns
      const consumptions = recentSignatures.map(sig => sig.data.consumption);
      const avgConsumption = consumptions.reduce((sum, c) => sum + c, 0) / consumptions.length;
      const maxConsumption = Math.max(...consumptions);
      
      if (maxConsumption > avgConsumption * 5) {
        suspiciousCount += 2;
        reasons.push('Unusually high consumption spike detected');
        recommendations.push('Verify meter readings and check for anomalies');
      }
      
      // Check for timestamp anomalies
      const timestamps = recentSignatures.map(sig => new Date(sig.timestamp).getTime());
      const sortedTimestamps = [...timestamps].sort();
      
      for (let i = 1; i < sortedTimestamps.length; i++) {
        const timeDiff = sortedTimestamps[i] - sortedTimestamps[i - 1];
        if (timeDiff < 1000) { // Less than 1 second apart
          suspiciousCount += 1;
          reasons.push('Suspiciously close timestamps detected');
          recommendations.push('Check for replay attacks or clock manipulation');
          break;
        }
      }
      
      // Check for signature reuse
      const uniqueSignatures = new Set(recentSignatures.map(sig => sig.signature));
      if (uniqueSignatures.size < recentSignatures.length) {
        suspiciousCount += 3;
        reasons.push('Duplicate signatures detected');
        recommendations.push('Investigate potential signature replay attack');
      }
      
      const confidence = Math.min(suspiciousCount / 10, 1.0); // Scale to 0-1
      const fraudDetected = confidence > 0.3;
      
      if (fraudDetected) {
        console.warn(`🚨 Fraud detected for meter ${meterId} (confidence: ${(confidence * 100).toFixed(1)}%)`);
      }
      
      return {
        fraudDetected,
        confidence,
        reasons,
        recommendations,
      };
      
    } catch (error) {
      console.error(`Fraud detection failed for meter ${meterId}:`, error);
      return {
        fraudDetected: false,
        confidence: 0,
        reasons: ['Fraud detection system error'],
        recommendations: ['Contact system administrator'],
      };
    }
  }

  /**
   * Create signature data string for consistent signing
   */
  private createSignatureDataString(data: ConsumptionSignatureData): string {
    // Create deterministic string for signing
    return [
      data.meterId,
      data.consumption.toFixed(6), // Fixed precision for consistency
      data.timestamp,
      data.readingBefore.toFixed(6),
      data.readingAfter.toFixed(6),
    ].join('|');
  }

  /**
   * Generate mock signature for demo purposes
   * In production, this would be done by the meter's secure element
   */
  private async generateMockSignature(dataString: string, meterId: string): Promise<string> {
    // Create a deterministic but unpredictable signature
    const encoder = new TextEncoder();
    const data = encoder.encode(dataString + meterId);
    
    // Use Web Crypto API for consistent hashing
    const hashBuffer = await crypto.subtle.digest('SHA-256', data);
    const hashArray = new Uint8Array(hashBuffer);
    
    // Convert to hex and format as ED25519 signature
    const hashHex = Array.from(hashArray)
      .map(b => b.toString(16).padStart(2, '0'))
      .join('');
    
    // Format as ED25519 signature (64 bytes = 128 hex chars)
    const signature = hashHex.slice(0, 128);
    
    return `0x${signature}`;
  }

  /**
   * Get public key for a meter
   */
  async getPublicKey(meterId: string): Promise<string> {
    const keypair = await this.ensureKeypair(meterId);
    return keypair.publicKey;
  }

  /**
   * Check if keypair exists for meter
   */
  hasKeypair(meterId: string): boolean {
    return this.keyCache.has(meterId);
  }

  /**
   * Clear cached keypairs (for security)
   */
  clearKeyCache(meterId?: string): void {
    if (meterId) {
      this.keyCache.delete(meterId);
    } else {
      this.keyCache.clear();
    }
    console.log(`🔐 Cleared key cache${meterId ? ` for meter ${meterId}` : ''}`);
  }

  /**
   * Get security metrics
   */
  getSecurityMetrics(): {
    cachedKeypairs: number;
    algorithmsSupported: string[];
    securityLevel: 'high' | 'medium' | 'low';
  } {
    return {
      cachedKeypairs: this.keyCache.size,
      algorithmsSupported: ['ED25519'],
      securityLevel: 'high', // ED25519 is considered high security
    };
  }

  /**
   * Clean up resources
   */
  cleanup(): void {
    this.clearKeyCache();
  }
}