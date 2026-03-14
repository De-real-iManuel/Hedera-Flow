'use client';

/**
 * Prepaid Token Purchase Page
 * 
 * Allows users to purchase prepaid electricity tokens with HBAR.
 * Features:
 * - Meter selection for users with multiple meters
 * - Integration with PrepaidTokenPurchase component
 * - Success handling and navigation
 * 
 * Requirements: US-13, Task 1.6
 */

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { PrepaidTokenPurchase } from '@/components/PrepaidTokenPurchase';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { ArrowLeft, Zap, AlertCircle, Loader2 } from 'lucide-react';
import { useAuth } from '@/hooks/useAuth';
import { useMeters } from '@/hooks/useMeters';

export default function PrepaidBuyPage() {
  const router = useRouter();
  const { user, isLoading: authLoading } = useAuth();
  const { meters, isLoading: metersLoading } = useMeters();
  const [selectedMeterId, setSelectedMeterId] = useState<string>('');

  // Filter for prepaid meters only
  const prepaidMeters = meters?.filter(m => m.meter_type === 'prepaid') || [];
  const selectedMeter = meters?.find(m => m.id === selectedMeterId);

  const handlePurchaseSuccess = (tokenId: string) => {
    // Navigate to prepaid balance page or dashboard after successful purchase
    router.push('/prepaid/balance');
  };

  const handleCancel = () => {
    if (selectedMeterId) {
      // If a meter is selected, go back to meter selection
      setSelectedMeterId('');
    } else {
      // Otherwise, go back to previous page
      router.back();
    }
  };

  // Loading state
  if (authLoading || metersLoading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="flex items-center justify-center min-h-[400px]">
          <Loader2 className="w-8 h-8 animate-spin text-purple-600" />
          <span className="ml-3 text-muted-foreground">Loading...</span>
        </div>
      </div>
    );
  }

  // Not authenticated
  if (!user) {
    return (
      <div className="container mx-auto px-4 py-8">
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            Please log in to purchase prepaid tokens.
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  // No prepaid meters
  if (prepaidMeters.length === 0) {
    return (
      <div className="container mx-auto px-4 py-8 max-w-2xl">
        <Card>
          <CardHeader>
            <div className="flex items-center gap-3">
              <div className="p-2 bg-purple-100 rounded-lg">
                <Zap className="w-6 h-6 text-purple-600" />
              </div>
              <div>
                <CardTitle>No Prepaid Meters</CardTitle>
                <CardDescription>
                  You don't have any prepaid meters registered yet.
                </CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <Alert className="bg-blue-50 border-blue-200">
              <AlertCircle className="h-4 w-4 text-blue-600" />
              <AlertDescription className="text-blue-800">
                To purchase prepaid tokens, you need to register a prepaid meter first.
              </AlertDescription>
            </Alert>
            <div className="flex gap-3">
              <Button
                variant="outline"
                onClick={() => router.back()}
                className="flex-1"
              >
                <ArrowLeft className="w-4 h-4 mr-2" />
                Go Back
              </Button>
              <Button
                onClick={() => router.push('/meters/register')}
                className="flex-1 bg-purple-600 hover:bg-purple-700"
              >
                Register Meter
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="max-w-2xl mx-auto space-y-6">
        {/* Page Header */}
        <div className="flex items-center gap-4">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => router.back()}
          >
            <ArrowLeft className="w-5 h-5" />
          </Button>
          <div>
            <h1 className="text-3xl font-bold">Buy Prepaid Tokens</h1>
            <p className="text-muted-foreground">
              Purchase electricity tokens with HBAR
            </p>
          </div>
        </div>

        {/* Meter Selection */}
        {!selectedMeterId && prepaidMeters.length > 1 && (
          <Card>
            <CardHeader>
              <CardTitle>Select a Meter</CardTitle>
              <CardDescription>
                Choose which meter you want to purchase tokens for
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              {prepaidMeters.map((meter) => (
                <Card
                  key={meter.id}
                  className="cursor-pointer hover:shadow-lg hover:border-purple-400 transition-all"
                  onClick={() => setSelectedMeterId(meter.id)}
                >
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="flex items-center gap-2 mb-1">
                          <h3 className="font-semibold text-lg">{meter.meter_id}</h3>
                          {meter.is_primary && (
                            <Badge className="bg-purple-600 text-white">Primary</Badge>
                          )}
                        </div>
                        <p className="text-sm text-muted-foreground">
                          {meter.utility_provider} • {meter.state_province}
                        </p>
                      </div>
                      <Zap className="w-6 h-6 text-purple-600" />
                    </div>
                  </CardContent>
                </Card>
              ))}
            </CardContent>
          </Card>
        )}

        {/* Auto-select if only one meter */}
        {!selectedMeterId && prepaidMeters.length === 1 && (
          <>
            {setSelectedMeterId(prepaidMeters[0].id)}
            {null}
          </>
        )}

        {/* Purchase Component */}
        {selectedMeterId && (
          <div className="space-y-4">
            {/* Show selected meter info if multiple meters */}
            {prepaidMeters.length > 1 && (
              <Card className="bg-purple-50 border-purple-200">
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-purple-700 font-medium">
                        Purchasing for:
                      </p>
                      <p className="font-semibold text-purple-900">
                        {selectedMeter?.meter_id}
                      </p>
                    </div>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => setSelectedMeterId('')}
                      className="text-purple-700 hover:text-purple-900"
                    >
                      Change Meter
                    </Button>
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Prepaid Token Purchase Component */}
            <PrepaidTokenPurchase
              meterId={selectedMeterId}
              onSuccess={handlePurchaseSuccess}
              onCancel={handleCancel}
            />
          </div>
        )}
      </div>
    </div>
  );
}
