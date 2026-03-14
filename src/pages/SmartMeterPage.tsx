import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Shield, ArrowLeft, CheckCircle, Activity, Key, Lock, AlertCircle } from 'lucide-react';
import { useAuth } from '@/hooks/useAuth';
import { useMeters } from '@/hooks/useMeters';
import { SmartMeterSimulator } from '@/components/SmartMeterSimulator';
import { ConsumptionHistory } from '@/components/ConsumptionHistory';
import type { ConsumptionLog } from '@/lib/api/smart-meter';

export default function SmartMeterPage() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const { meters, isLoading: metersLoading } = useMeters();
  const [selectedMeterId, setSelectedMeterId] = useState<string>('');
  const [refreshTrigger, setRefreshTrigger] = useState(0);

  const prepaidMeters = meters?.filter(m => m.meter_type === 'prepaid') || [];
  const selectedMeter = meters?.find(m => m.id === selectedMeterId);

  // Handle consumption logged from simulator
  const handleConsumptionLogged = (log: ConsumptionLog) => {
    // Trigger refresh of consumption history
    setRefreshTrigger(prev => prev + 1);
  };

  if (metersLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 pb-20">
      {/* Header */}
      <div className="bg-white border-b sticky top-0 z-10">
        <div className="max-w-4xl mx-auto px-4 py-4">
          <div className="flex items-center gap-4">
            <Button variant="ghost" size="icon" onClick={() => navigate('/home')}>
              <ArrowLeft className="w-5 h-5" />
            </Button>
            <div className="flex-1">
              <h1 className="text-2xl font-bold">Smart Meters</h1>
              <p className="text-sm text-muted-foreground">Cryptographically verified consumption</p>
            </div>
            <Badge variant="outline" className="gap-2">
              <Shield className="w-3 h-3" />
              Secure
            </Badge>
          </div>
        </div>
      </div>

      <div className="max-w-4xl mx-auto px-4 py-6 space-y-6">
        {/* No Meters */}
        {prepaidMeters.length === 0 && (
          <Card>
            <CardContent className="py-16 text-center">
              <Shield className="w-20 h-20 mx-auto mb-4 text-blue-300" />
              <h3 className="text-xl font-semibold mb-2">No Smart Meters</h3>
              <p className="text-muted-foreground mb-6">
                Register a prepaid meter to enable smart features
              </p>
              <Button onClick={() => navigate('/register-meter')} size="lg">
                Register Meter
              </Button>
            </CardContent>
          </Card>
        )}

        {/* Meter Selection */}
        {prepaidMeters.length > 0 && !selectedMeterId && (
          <div className="space-y-4">
            <h2 className="text-lg font-semibold">Select a Meter</h2>
            <div className="grid gap-4">
              {prepaidMeters.map((meter) => (
                <Card
                  key={meter.id}
                  className="cursor-pointer hover:shadow-lg hover:border-blue-400 transition-all"
                  onClick={() => setSelectedMeterId(meter.id)}
                >
                  <CardContent className="p-6">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <h3 className="font-bold text-lg">{meter.meter_id}</h3>
                          {meter.is_primary && <Badge>Primary</Badge>}
                        </div>
                        <p className="text-sm text-muted-foreground">{meter.utility_provider}</p>
                        <div className="flex items-center gap-2 mt-3">
                          <Badge variant="outline" className="gap-1">
                            <CheckCircle className="w-3 h-3 text-green-500" />
                            Verified
                          </Badge>
                          <Badge variant="outline" className="gap-1">
                            <Key className="w-3 h-3" />
                            ED25519
                          </Badge>
                        </div>
                      </div>
                      <Shield className="w-8 h-8 text-blue-500" />
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        )}

        {/* Selected Meter View */}
        {selectedMeterId && selectedMeter && (
          <div className="space-y-6">
            <Button variant="ghost" onClick={() => setSelectedMeterId('')}>
              <ArrowLeft className="w-4 h-4 mr-2" />
              All Meters
            </Button>

            {/* Meter Security Status */}
            <Card className="bg-gradient-to-br from-blue-600 to-indigo-600 text-white">
              <CardContent className="p-6">
                <div className="flex items-start justify-between mb-4">
                  <div>
                    <h2 className="text-2xl font-bold mb-1">{selectedMeter.meter_id}</h2>
                    <p className="text-sm opacity-90">{selectedMeter.utility_provider}</p>
                  </div>
                  <Shield className="w-10 h-10 opacity-50" />
                </div>
                <div className="grid grid-cols-2 gap-4 mt-6">
                  <div className="p-3 bg-white/10 rounded-lg">
                    <div className="flex items-center gap-2 mb-1">
                      <CheckCircle className="w-4 h-4" />
                      <span className="text-sm">Status</span>
                    </div>
                    <p className="text-lg font-bold">Active</p>
                  </div>
                  <div className="p-3 bg-white/10 rounded-lg">
                    <div className="flex items-center gap-2 mb-1">
                      <Key className="w-4 h-4" />
                      <span className="text-sm">Algorithm</span>
                    </div>
                    <p className="text-lg font-bold">ED25519</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Smart Meter Tabs */}
            <Tabs defaultValue="simulator" className="space-y-6">
              <TabsList className="grid w-full grid-cols-2">
                <TabsTrigger value="simulator">Live Simulator</TabsTrigger>
                <TabsTrigger value="history">Consumption History</TabsTrigger>
              </TabsList>

              {/* Simulator Tab */}
              <TabsContent value="simulator">
                <SmartMeterSimulator
                  meterId={selectedMeterId}
                  meterNumber={selectedMeter.meter_id}
                  onConsumptionLogged={handleConsumptionLogged}
                  autoStart={false}
                />
              </TabsContent>

              {/* History Tab */}
              <TabsContent value="history">
                <ConsumptionHistory
                  meterId={selectedMeterId}
                  refreshTrigger={refreshTrigger}
                />
              </TabsContent>
            </Tabs>

            {/* Security Info */}
            <Card>
              <CardHeader>
                <CardTitle>Security Information</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-start gap-3 p-3 bg-blue-50 rounded-lg">
                  <Shield className="w-5 h-5 text-blue-600 mt-0.5" />
                  <div>
                    <p className="font-semibold text-sm mb-1">Cryptographic Signatures</p>
                    <p className="text-xs text-muted-foreground">
                      All consumption data is signed with ED25519 to prevent tampering
                    </p>
                  </div>
                </div>
                <div className="flex items-start gap-3 p-3 bg-purple-50 rounded-lg">
                  <Lock className="w-5 h-5 text-purple-600 mt-0.5" />
                  <div>
                    <p className="font-semibold text-sm mb-1">Private Key Security</p>
                    <p className="text-xs text-muted-foreground">
                      Private keys are encrypted with AES-256 and never exposed
                    </p>
                  </div>
                </div>
                <div className="flex items-start gap-3 p-3 bg-green-50 rounded-lg">
                  <CheckCircle className="w-5 h-5 text-green-600 mt-0.5" />
                  <div>
                    <p className="font-semibold text-sm mb-1">Hedera HCS Logging</p>
                    <p className="text-xs text-muted-foreground">
                      All verifications are logged immutably to Hedera Consensus Service
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        )}
      </div>
    </div>
  );
}
