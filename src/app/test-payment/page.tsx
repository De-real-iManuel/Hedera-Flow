'use client';

/**
 * Test Payment Page
 * 
 * Demonstrates the complete payment flow including:
 * - Balance checking
 * - Insufficient balance handling
 * - Top-up modal
 * - Payment confirmation
 * 
 * This page is for testing and demonstration purposes.
 */

import { useState } from 'react';
import { BillBreakdown, type BillBreakdownData } from '@/components/BillBreakdown';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Info, Zap, DollarSign