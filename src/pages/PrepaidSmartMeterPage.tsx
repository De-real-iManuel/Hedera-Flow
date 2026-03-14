import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { PrepaidTokenPurchase } from '@/components/PrepaidTokenPurchase';
import { SmartMeterSimulator } from '@/components/SmartMeterSimulator';
import { ConsumptionHistory } from '@/components/ConsumptionHistory';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Zap, Clock, AlertCircle, ArrowLeft, Wallet, Shield, Activity, CheckCircle, XCircle } from 'lucide-react';
import { useAuth } from '@/hooks/useAuth';
import { useMeters } from '@/hooks/useMeters';
import { usePrepaid } from '@/hooks/usePrepaid';
import type { ConsumptionLog } from '@/lib/api/smart-meter';

export default function PrepaidSmartMeterPage() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const { meters, isLoading: metersLoading } = useMeters();
  const [selectedMeterId, setSelectedMeterId] = useState<string>('');
  const [refreshTrigger, setRefreshTrigger] = useState(0);
  const { tokens, balance, isLoading } = usePrepaid(selectedMeterId || undefined);

  const prepaidMeters = meters?.filter(m => m.meter_type === 'prepaid') || [];
  const selectedMeter = meters?.find(m => m.id === selectedMeterId);

  if (metersLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin w-8 h-8 border-4 border-purple-500 border-t-transparent rounded-full" />
      </div>
    );
  }

  const handlePurchaseSuccess = (tokenId: string) => {
    console.log('Token purchased:', tokenId);
  };

  // Handle consumption logged from simulator
  const handleConsumptionLogged = (log: ConsumptionLog) => {
    // Trigger refresh of consumption history
    setRefreshTrigger(prev => prev + 1);
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'bg-green-500';
      case 'low': return 'bg-yellow-500';
      case 'depleted': return 'bg-red-500';
      default: return 'bg-gray-500';
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 via-blue-50 to-indigo-50 p-4 md:p-8">
      <div className="max-w-6xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Button variant="ghost" size="icon" onClick={() => navigate('/')}>
              <ArrowLeft className="w-5 h-5" />
            </Button>
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Prepaid & Smart Meter</h1>
              <p className="text-muted-foreground">Manage tokens and verify consumption</p>
            </div>
          </div>
          {user?.hedera_account_id && (
            <Badge variant="outline" className="gap-2">
              <Wallet className="w-4 h-4" />
              {user.hedera_account_id.slice(0, 10)}...
            </Badge>
          )}
        </div>

        {/* No Prepaid Meters */}
        {prepaidMeters.length === 0 && (
          <Card>
            <CardContent className="py-12 text-center">
              <Zap className="w-16 h-16 mx-auto mb-4 text-muted-foreground" />
              <h3 className="text-xl font-semibold mb-2">No Prepaid Meters</h3>
              <p className="text-muted-foreground mb-6">Register a prepaid meter to get started</p>
              <Button onClick={() => navigate('/meters/register')}>Register Meter</Button>
            </CardContent>
          </Card>
        )}

        {/* Main Content */}
        {prepaidMeters.length > 0 && (
          <div className="space-y-6">
            {/* Meter Selection */}
            {!selectedMeterId && (
              <Card>
                <CardHeader>
                  <CardTitle>Select Meter</CardTitle>
                  <CardDescription>Choose a prepaid meter to manage</CardDescription>
                </CardHeader>
                <CardContent className="grid gap-4">
                  {prepaidMeters.map((meter) => (
                    <Card
                      key={meter.id}
                      className="cursor-pointer hover:border-purple-500 transition-colors"
                      onClick={() => setSelectedMeterId(meter.id)}
                    >
                      <CardContent className="p-4 flex items-center justify-between">
                        <div>
                          <p className="font-semibold">{meter.meter_id}</p>
                          <p className="text-sm text-muted-foreground">
                            {meter.utility_provider} • {meter.state_province}
                          </p>
                        </div>
                        {meter.is_primary && <Badge>Primary</Badge>}
                      </CardContent>
                    </Card>
                  ))}
                </CardContent>
              </Card>
            )}

            {/* Meter Management Tabs */}
            {selectedMeterId && (
              <div className="space-y-4">
                <Button variant="ghost" onClick={() => setSelectedMeterId('')} className="mb-2">
                  <ArrowLeft className="w-4 h-4 mr-2" />
                  Change Meter
                </Button>

                {/* Balance Overview */}
                {balance && (
                  <Card className="bg-gradient-to-br from-purple-500 to-blue-600 text-white">
                    <CardContent className="p-6">
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="text-sm opacity-90">Total Balance</p>
                          <p className="text-4xl font-bold">{balance.total_units.toFixed(2)} kWh</p>
                          <p className="text-sm opacity-90 mt-1">
                            {balance.active_tokens} active token{balance.active_tokens !== 1 ? 's' : ''}
                          </p>
                        </div>
                        <Zap className="w-16 h-16 opacity-50" />
                      </div>
                      {balance.low_balance_alert && (
                        <div className="mt-4 p-3 bg-yellow-500/20 rounded-lg flex items-center gap-2">
                          <AlertCircle className="w-5 h-5" />
                          <span className="text-sm">Low balance alert - Consider topping up</span>
                        </div>
                      )}
                    </CardContent>
                  </Card>
                )}

                <Tabs defaultValue="buy" className="space-y-6">
                  <TabsList className="grid w-full grid-cols-3">
                    <TabsTrigger value="buy">Buy Tokens</TabsTrigger>
                    <TabsTrigger value="history">History</TabsTrigger>
                    <TabsTrigger value="smart-meter">Smart Meter</TabsTrigger>
                  </TabsList>

                  {/* Buy Tokens Tab */}
                  <TabsContent value="buy">
                    <PrepaidTokenPurchase
                      meterId={selectedMeterId}
                      onSuccess={handlePurchaseSuccess}
                      onCancel={() => setSelectedMeterId('')}
                    />
                  </TabsContent>

                  {/* Token History Tab */}
                  <TabsContent value="history">
                    <Card>
                      <CardHeader>
                        <CardTitle>Token History</CardTitle>
                        <CardDescription>View all purchased tokens</CardDescription>
                      </CardHeader>
                      <CardContent>
                        {isLoading ? (
                          <div className="text-center py-12">
                            <Clock className="w-16 h-16 mx-auto mb-4 text-muted-foreground animate-spin" />
                            <p className="text-muted-foreground">Loading tokens...</p>
                          </div>
                        ) : !tokens || tokens.length === 0 ? (
                          <div className="text-center py-12">
                            <Clock className="w-16 h-16 mx-auto mb-4 text-muted-foreground" />
                            <p className="text-muted-foreground">No tokens purchased yet</p>
                          </div>
                        ) : (
                          <div className="space-y-3">
                            {tokens.map((token) => (
                              <Card key={token.id} className="hover:shadow-md transition-shadow">
                                <CardContent className="p-4">
                                  <div className="flex items-center justify-between">
                                    <div className="flex-1">
                                      <div className="flex items-center gap-2 mb-1">
                                        <p className="font-mono font-semibold">{token.token_id}</p>
                                        <Badge className={getStatusColor(token.status)}>
                                          {token.status}
                                        </Badge>
                                      </div>
                                      <p className="text-sm text-muted-foreground">
                                        {token.units_remaining.toFixed(2)} / {token.units_purchased.toFixed(2)} kWh
                                      </p>
                                      <p className="text-xs text-muted-foreground mt-1">
                                        {new Date(token.created_at).toLocaleDateString()}
                                      </p>
                                    </div>
                                    <div className="text-right">
                                      <p className="font-semibold">{token.amount_hbar.toFixed(2)} ℏ</p>
                                      <p className="text-sm text-muted-foreground">
                                        {token.amount_fiat} {token.currency}
                                      </p>
                                    </div>
                                  </div>
                                </CardContent>
                              </Card>
                            ))}
                          </div>
                        )}
                      </CardContent>
                    </Card>
                  </TabsContent>

                  {/* Smart Meter Tab */}
                  <TabsContent value="smart-meter">
                    <div className="space-y-6">
                      {/* Smart Meter Simulator */}
                      <SmartMeterSimulator
                        meterId={selectedMeterId}
                        meterNumber={selectedMeter.meter_id}
                        onConsumptionLogged={handleConsumptionLogged}
                        autoStart={false}
                      />

                      {/* Consumption History */}
                      <ConsumptionHistory
                        meterId={selectedMeterId}
                        refreshTrigger={refreshTrigger}
                      />
                    </div>
                  </TabsContent>
                </Tabs>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
