import { useState, useEffect } from 'react';
import { useAuth } from '@/hooks/useAuth';
import { useUtilityProviders } from '@/hooks/useUtilityProviders';
import { useMeters } from '@/hooks/useMeters';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Loader2, CheckCircle2, AlertCircle } from 'lucide-react';
import { utilityProvidersApi } from '@/lib/api';

interface MeterRegistrationFormProps {
  onSuccess?: () => void;
  onCancel?: () => void;
}

export function MeterRegistrationForm({ onSuccess, onCancel }: MeterRegistrationFormProps) {
  const { user } = useAuth();
  const { createMeter, isCreating, createError } = useMeters();
  
  // Form state
  const [meterId, setMeterId] = useState('');
  const [stateProvince, setStateProvince] = useState('');
  const [utilityProviderId, setUtilityProviderId] = useState('');
  const [meterType, setMeterType] = useState<'prepaid' | 'postpaid'>('postpaid');
  const [bandClassification, setBandClassification] = useState('');
  const [address, setAddress] = useState('');
  const [isPrimary, setIsPrimary] = useState(false);
  
  // Dropdown data
  const [states, setStates] = useState<string[]>([]);
  const [loadingStates, setLoadingStates] = useState(false);
  
  // Utility providers for selected state
  const { data: providers, isLoading: loadingProviders } = useUtilityProviders(
    user?.country_code,
    stateProvince
  );
  
  // Success state
  const [showSuccess, setShowSuccess] = useState(false);
  
  // Load states when component mounts
  useEffect(() => {
    if (user?.country_code) {
      loadStates(user.country_code);
    }
  }, [user?.country_code]);
  
  // Reset utility provider when state changes
  useEffect(() => {
    setUtilityProviderId('');
  }, [stateProvince]);
  
  const loadStates = async (countryCode: string) => {
    setLoadingStates(true);
    try {
      const response = await utilityProvidersApi.list(countryCode);
      // Extract unique states
      const uniqueStates = Array.from(
        new Set(response.map(p => p.state_province))
      ).sort();
      setStates(uniqueStates);
    } catch (error) {
      console.error('Failed to load states:', error);
    } finally {
      setLoadingStates(false);
    }
  };
  
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!utilityProviderId) {
      return;
    }
    
    // Find selected provider to get the name
    const selectedProvider = providers?.find(p => p.id === utilityProviderId);
    if (!selectedProvider) {
      return;
    }
    
    createMeter(
      {
        meter_id: meterId,
        utility_provider_id: utilityProviderId,
        state_province: stateProvince,
        utility_provider: selectedProvider.provider_name,
        meter_type: meterType,
        band_classification: bandClassification || undefined,
        address: address || undefined,
        is_primary: isPrimary,
      },
      {
        onSuccess: () => {
          setShowSuccess(true);
          setTimeout(() => {
            setShowSuccess(false);
            if (onSuccess) {
              onSuccess();
            }
          }, 2000);
        },
      }
    );
  };
  
  const isNigeria = user?.country_code === 'NG';
  const nigerianBands = ['A', 'B', 'C', 'D', 'E'];
  
  if (showSuccess) {
    return (
      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-col items-center justify-center py-8 text-center">
            <CheckCircle2 className="w-16 h-16 text-green-500 mb-4" />
            <h3 className="text-xl font-semibold mb-2">Meter Registered Successfully!</h3>
            <p className="text-muted-foreground">
              Your meter has been added to your account.
            </p>
          </div>
        </CardContent>
      </Card>
    );
  }
  
  return (
    <Card>
      <CardHeader>
        <CardTitle>Register Electricity Meter</CardTitle>
        <CardDescription>
          Add your electricity meter to start verifying bills
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Meter ID */}
          <div className="space-y-2">
            <Label htmlFor="meterId">Meter ID *</Label>
            <Input
              id="meterId"
              value={meterId}
              onChange={(e) => setMeterId(e.target.value)}
              placeholder="Enter your meter number"
              required
            />
            <p className="text-xs text-muted-foreground">
              Find this on your electricity meter or bill
            </p>
          </div>
          
          {/* State/Province Dropdown */}
          <div className="space-y-2">
            <Label htmlFor="state">State/Province *</Label>
            <Select
              value={stateProvince}
              onValueChange={setStateProvince}
              disabled={loadingStates}
            >
              <SelectTrigger id="state">
                <SelectValue placeholder={loadingStates ? "Loading..." : "Select your state"} />
              </SelectTrigger>
              <SelectContent>
                {states.map((state) => (
                  <SelectItem key={state} value={state}>
                    {state}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          
          {/* Utility Provider Dropdown */}
          <div className="space-y-2">
            <Label htmlFor="provider">Utility Provider *</Label>
            <Select
              value={utilityProviderId}
              onValueChange={setUtilityProviderId}
              disabled={!stateProvince || loadingProviders}
            >
              <SelectTrigger id="provider">
                <SelectValue 
                  placeholder={
                    !stateProvince 
                      ? "Select state first" 
                      : loadingProviders 
                      ? "Loading..." 
                      : "Select your utility provider"
                  } 
                />
              </SelectTrigger>
              <SelectContent>
                {providers?.map((provider) => (
                  <SelectItem key={provider.id} value={provider.id}>
                    {provider.provider_name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            {providers && providers.length === 0 && stateProvince && (
              <p className="text-xs text-amber-600">
                No providers found for this state
              </p>
            )}
          </div>
          
          {/* Meter Type */}
          <div className="space-y-2">
            <Label htmlFor="meterType">Meter Type *</Label>
            <Select
              value={meterType}
              onValueChange={(value) => setMeterType(value as 'prepaid' | 'postpaid')}
            >
              <SelectTrigger id="meterType">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="postpaid">Postpaid (Monthly Bill)</SelectItem>
                <SelectItem value="prepaid">Prepaid (Pay-as-you-go)</SelectItem>
              </SelectContent>
            </Select>
          </div>
          
          {/* Band Classification (Nigeria only) */}
          {isNigeria && (
            <div className="space-y-2">
              <Label htmlFor="band">Band Classification *</Label>
              <Select
                value={bandClassification}
                onValueChange={setBandClassification}
                required={isNigeria}
              >
                <SelectTrigger id="band">
                  <SelectValue placeholder="Select your band" />
                </SelectTrigger>
                <SelectContent>
                  {nigerianBands.map((band) => (
                    <SelectItem key={band} value={band}>
                      Band {band}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <p className="text-xs text-muted-foreground">
                Band determines your electricity tariff rate
              </p>
            </div>
          )}
          
          {/* Address (Optional) */}
          <div className="space-y-2">
            <Label htmlFor="address">Address (Optional)</Label>
            <Input
              id="address"
              value={address}
              onChange={(e) => setAddress(e.target.value)}
              placeholder="Enter meter installation address"
            />
          </div>
          
          {/* Error Display */}
          {createError && (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>
                {createError instanceof Error ? createError.message : 'Failed to register meter'}
              </AlertDescription>
            </Alert>
          )}
          
          {/* Action Buttons */}
          <div className="flex gap-3 pt-4">
            {onCancel && (
              <Button
                type="button"
                variant="outline"
                onClick={onCancel}
                className="flex-1"
              >
                Cancel
              </Button>
            )}
            <Button
              type="submit"
              disabled={isCreating || !utilityProviderId}
              className="flex-1"
            >
              {isCreating ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Registering...
                </>
              ) : (
                'Register Meter'
              )}
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  );
}
