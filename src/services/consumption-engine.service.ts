/**
 * Consumption Engine Service
 * 
 * Generates realistic electricity consumption patterns based on:
 * - Time of day variations
 * - Seasonal patterns
 * - Regional differences
 * - Appliance usage patterns
 * - Weather conditions (simulated)
 */

export interface ConsumptionPattern {
  baseRate: number; // kWh per hour
  peakMultiplier: number;
  offPeakMultiplier: number;
  seasonalAdjustment: number;
  weatherAdjustment: number;
  randomVariation: number;
}

export interface MeterProfile {
  region: string;
  utilityProvider: string;
  meterType: 'residential' | 'commercial' | 'industrial';
  baselineConsumption: number;
  peakHours: { start: number; end: number }[];
  seasonalProfile: SeasonalProfile;
}

export interface SeasonalProfile {
  winter: { multiplier: number; peakShift: number };
  spring: { multiplier: number; peakShift: number };
  summer: { multiplier: number; peakShift: number };
  fall: { multiplier: number; peakShift: number };
}

export interface WeatherConditions {
  temperature: number; // Celsius
  humidity: number; // Percentage
  season: 'winter' | 'spring' | 'summer' | 'fall';
  isWeekend: boolean;
  isHoliday: boolean;
}

export class ConsumptionEngine {
  private meterProfiles: Map<string, MeterProfile> = new Map();
  private consumptionHistory: Map<string, number[]> = new Map();
  
  // Regional consumption patterns (kWh per hour baseline)
  private readonly REGIONAL_PATTERNS = {
    'US': { base: 1.2, peak: 2.5, offPeak: 0.4 },
    'EU': { base: 0.8, peak: 1.8, offPeak: 0.3 },
    'NG': { base: 0.6, peak: 1.5, offPeak: 0.2 }, // Nigeria
    'IN': { base: 0.7, peak: 1.6, offPeak: 0.25 }, // India
    'BR': { base: 0.9, peak: 2.0, offPeak: 0.35 }, // Brazil
  };

  // Appliance usage patterns throughout the day
  private readonly APPLIANCE_PATTERNS = {
    hvac: { peak: [14, 15, 16, 17, 18, 19, 20], consumption: 3.5 },
    lighting: { peak: [18, 19, 20, 21, 22, 23], consumption: 0.5 },
    cooking: { peak: [7, 8, 12, 13, 18, 19, 20], consumption: 2.0 },
    waterHeater: { peak: [6, 7, 8, 18, 19, 20, 21], consumption: 1.5 },
    electronics: { peak: [19, 20, 21, 22, 23], consumption: 0.8 },
    laundry: { peak: [10, 11, 14, 15, 16], consumption: 1.2 },
  };

  /**
   * Initialize a meter with consumption profile
   */
  async initializeMeter(meterId: string, config: {
    region: string;
    utilityProvider: string;
    baselineReading: number;
    meterType?: 'residential' | 'commercial' | 'industrial';
  }): Promise<void> {
    const profile: MeterProfile = {
      region: config.region,
      utilityProvider: config.utilityProvider,
      meterType: config.meterType || 'residential',
      baselineConsumption: this.getRegionalBaseline(config.region),
      peakHours: this.getPeakHours(config.meterType || 'residential'),
      seasonalProfile: this.getSeasonalProfile(config.region),
    };

    this.meterProfiles.set(meterId, profile);
    this.consumptionHistory.set(meterId, []);
    
    console.log(`✅ Initialized consumption engine for meter ${meterId} in ${config.region}`);
  }

  /**
   * Get realistic consumption rate for current time
   */
  getRealisticConsumptionRate(meterId: string): number {
    const profile = this.meterProfiles.get(meterId);
    if (!profile) {
      console.warn(`No profile found for meter ${meterId}, using default rate`);
      return 0.5;
    }

    const now = new Date();
    const hour = now.getHours();
    const dayOfWeek = now.getDay();
    const month = now.getMonth();

    // Get weather conditions (simulated)
    const weather = this.simulateWeatherConditions(profile.region, month);
    
    // Calculate base consumption pattern
    const pattern = this.calculateConsumptionPattern(profile, hour, dayOfWeek, weather);
    
    // Apply appliance usage patterns
    const applianceConsumption = this.calculateApplianceConsumption(hour, dayOfWeek, weather);
    
    // Combine patterns
    let totalRate = pattern.baseRate + applianceConsumption;
    
    // Apply time-of-day multipliers
    if (this.isPeakHour(hour, profile.peakHours)) {
      totalRate *= pattern.peakMultiplier;
    } else {
      totalRate *= pattern.offPeakMultiplier;
    }
    
    // Apply seasonal adjustment
    totalRate *= pattern.seasonalAdjustment;
    
    // Apply weather adjustment (AC/heating usage)
    totalRate *= pattern.weatherAdjustment;
    
    // Add random variation (±15%)
    const randomFactor = 0.85 + (Math.random() * 0.3);
    totalRate *= randomFactor;
    
    // Store in history for trend analysis
    this.updateConsumptionHistory(meterId, totalRate);
    
    return Math.max(totalRate, 0.05); // Minimum consumption
  }

  /**
   * Calculate consumption pattern based on profile and conditions
   */
  private calculateConsumptionPattern(
    profile: MeterProfile, 
    hour: number, 
    dayOfWeek: number, 
    weather: WeatherConditions
  ): ConsumptionPattern {
    const regional = this.REGIONAL_PATTERNS[profile.region as keyof typeof this.REGIONAL_PATTERNS] 
      || this.REGIONAL_PATTERNS['US'];

    // Base rate varies by meter type
    let baseRate = regional.base;
    switch (profile.meterType) {
      case 'commercial':
        baseRate *= 3.5;
        break;
      case 'industrial':
        baseRate *= 8.0;
        break;
      default: // residential
        baseRate *= 1.0;
    }

    // Weekend patterns (residential uses more, commercial uses less)
    if (weather.isWeekend) {
      baseRate *= profile.meterType === 'residential' ? 1.2 : 0.6;
    }

    // Holiday patterns
    if (weather.isHoliday) {
      baseRate *= profile.meterType === 'residential' ? 1.4 : 0.3;
    }

    return {
      baseRate,
      peakMultiplier: regional.peak / regional.base,
      offPeakMultiplier: regional.offPeak / regional.base,
      seasonalAdjustment: this.getSeasonalAdjustment(profile.seasonalProfile, weather.season),
      weatherAdjustment: this.getWeatherAdjustment(weather),
      randomVariation: 0.15,
    };
  }

  /**
   * Calculate appliance-specific consumption
   */
  private calculateApplianceConsumption(hour: number, dayOfWeek: number, weather: WeatherConditions): number {
    let totalAppliance = 0;

    Object.entries(this.APPLIANCE_PATTERNS).forEach(([appliance, pattern]) => {
      if (pattern.peak.includes(hour)) {
        let consumption = pattern.consumption;
        
        // Weather adjustments for specific appliances
        if (appliance === 'hvac') {
          if (weather.temperature > 25 || weather.temperature < 5) {
            consumption *= 1.8; // High AC/heating usage
          }
        }
        
        // Weekend adjustments
        if (weather.isWeekend) {
          if (['cooking', 'laundry', 'electronics'].includes(appliance)) {
            consumption *= 1.3;
          }
        }
        
        totalAppliance += consumption;
      }
    });

    return totalAppliance;
  }

  /**
   * Simulate weather conditions for realistic consumption
   */
  private simulateWeatherConditions(region: string, month: number): WeatherConditions {
    const now = new Date();
    const season = this.getSeason(month);
    
    // Simulate temperature based on region and season
    let baseTemp = 20; // Default 20°C
    switch (region) {
      case 'NG': // Nigeria - tropical
        baseTemp = season === 'winter' ? 25 : 32;
        break;
      case 'US': // US - temperate
        baseTemp = season === 'winter' ? 5 : season === 'summer' ? 28 : 18;
        break;
      case 'EU': // Europe - temperate
        baseTemp = season === 'winter' ? 3 : season === 'summer' ? 25 : 15;
        break;
      case 'IN': // India - tropical/subtropical
        baseTemp = season === 'winter' ? 20 : 35;
        break;
      case 'BR': // Brazil - tropical
        baseTemp = season === 'winter' ? 22 : 30;
        break;
    }
    
    // Add daily variation
    const dailyVariation = Math.sin((now.getHours() - 6) * Math.PI / 12) * 8;
    const temperature = baseTemp + dailyVariation + (Math.random() - 0.5) * 4;
    
    return {
      temperature,
      humidity: 40 + Math.random() * 40, // 40-80%
      season,
      isWeekend: now.getDay() === 0 || now.getDay() === 6,
      isHoliday: false, // Simplified
    };
  }

  /**
   * Get seasonal adjustment multiplier
   */
  private getSeasonalAdjustment(profile: SeasonalProfile, season: WeatherConditions['season']): number {
    return profile[season].multiplier;
  }

  /**
   * Get weather-based consumption adjustment
   */
  private getWeatherAdjustment(weather: WeatherConditions): number {
    // Extreme temperatures increase consumption (AC/heating)
    if (weather.temperature > 30 || weather.temperature < 0) {
      return 1.6;
    } else if (weather.temperature > 25 || weather.temperature < 10) {
      return 1.3;
    }
    return 1.0;
  }

  /**
   * Check if current hour is peak hour
   */
  private isPeakHour(hour: number, peakHours: { start: number; end: number }[]): boolean {
    return peakHours.some(period => hour >= period.start && hour <= period.end);
  }

  /**
   * Get regional baseline consumption
   */
  private getRegionalBaseline(region: string): number {
    const pattern = this.REGIONAL_PATTERNS[region as keyof typeof this.REGIONAL_PATTERNS];
    return pattern ? pattern.base : this.REGIONAL_PATTERNS['US'].base;
  }

  /**
   * Get peak hours for meter type
   */
  private getPeakHours(meterType: 'residential' | 'commercial' | 'industrial'): { start: number; end: number }[] {
    switch (meterType) {
      case 'residential':
        return [
          { start: 7, end: 9 },   // Morning peak
          { start: 18, end: 22 }, // Evening peak
        ];
      case 'commercial':
        return [
          { start: 9, end: 17 },  // Business hours
        ];
      case 'industrial':
        return [
          { start: 6, end: 22 },  // Extended operations
        ];
      default:
        return [{ start: 18, end: 22 }];
    }
  }

  /**
   * Get seasonal profile for region
   */
  private getSeasonalProfile(region: string): SeasonalProfile {
    // Simplified seasonal profiles by region
    switch (region) {
      case 'NG': // Nigeria - minimal seasonal variation
        return {
          winter: { multiplier: 0.9, peakShift: 0 },
          spring: { multiplier: 1.0, peakShift: 0 },
          summer: { multiplier: 1.3, peakShift: 2 }, // More AC usage
          fall: { multiplier: 1.0, peakShift: 0 },
        };
      case 'US': // US - significant seasonal variation
        return {
          winter: { multiplier: 1.4, peakShift: -2 }, // Heating
          spring: { multiplier: 1.0, peakShift: 0 },
          summer: { multiplier: 1.6, peakShift: 2 }, // AC
          fall: { multiplier: 1.1, peakShift: 0 },
        };
      default:
        return {
          winter: { multiplier: 1.2, peakShift: 0 },
          spring: { multiplier: 1.0, peakShift: 0 },
          summer: { multiplier: 1.3, peakShift: 1 },
          fall: { multiplier: 1.0, peakShift: 0 },
        };
    }
  }

  /**
   * Get season from month
   */
  private getSeason(month: number): WeatherConditions['season'] {
    if (month >= 2 && month <= 4) return 'spring';
    if (month >= 5 && month <= 7) return 'summer';
    if (month >= 8 && month <= 10) return 'fall';
    return 'winter';
  }

  /**
   * Update consumption history for trend analysis
   */
  private updateConsumptionHistory(meterId: string, rate: number): void {
    const history = this.consumptionHistory.get(meterId) || [];
    history.push(rate);
    
    // Keep only last 100 readings for performance
    if (history.length > 100) {
      history.shift();
    }
    
    this.consumptionHistory.set(meterId, history);
  }

  /**
   * Get consumption trends for a meter
   */
  getConsumptionTrends(meterId: string): {
    average: number;
    trend: 'increasing' | 'decreasing' | 'stable';
    volatility: number;
  } {
    const history = this.consumptionHistory.get(meterId) || [];
    if (history.length < 10) {
      return { average: 0, trend: 'stable', volatility: 0 };
    }

    const average = history.reduce((sum, rate) => sum + rate, 0) / history.length;
    
    // Calculate trend (simple linear regression slope)
    const n = history.length;
    const sumX = (n * (n - 1)) / 2;
    const sumY = history.reduce((sum, rate) => sum + rate, 0);
    const sumXY = history.reduce((sum, rate, index) => sum + (rate * index), 0);
    const sumX2 = (n * (n - 1) * (2 * n - 1)) / 6;
    
    const slope = (n * sumXY - sumX * sumY) / (n * sumX2 - sumX * sumX);
    
    let trend: 'increasing' | 'decreasing' | 'stable' = 'stable';
    if (slope > 0.01) trend = 'increasing';
    else if (slope < -0.01) trend = 'decreasing';
    
    // Calculate volatility (standard deviation)
    const variance = history.reduce((sum, rate) => sum + Math.pow(rate - average, 2), 0) / n;
    const volatility = Math.sqrt(variance);
    
    return { average, trend, volatility };
  }

  /**
   * Predict next consumption reading
   */
  predictNextReading(meterId: string, currentReading: number, minutesAhead: number): number {
    const currentRate = this.getRealisticConsumptionRate(meterId);
    const hoursAhead = minutesAhead / 60;
    return currentReading + (currentRate * hoursAhead);
  }

  /**
   * Clean up meter data
   */
  cleanup(meterId?: string): void {
    if (meterId) {
      this.meterProfiles.delete(meterId);
      this.consumptionHistory.delete(meterId);
    } else {
      this.meterProfiles.clear();
      this.consumptionHistory.clear();
    }
  }
}