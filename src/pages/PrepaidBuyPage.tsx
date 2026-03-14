/**
 * Prepaid Token Buy Page
 * 
 * Dedicated page for purchasing prepaid electricity tokens with HBAR.
 * Features:
 * - Meter selection for users with multiple meters
 * - Integration with PrepaidTokenPurchase component
 * - Success handling and navigation
 * 
 * Requirements: US-13, Task 1.6
 * Route: /prepaid/buy
 */

import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { PrepaidTokenPurchase } from '@/components/PrepaidTokenPurchase';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
impor