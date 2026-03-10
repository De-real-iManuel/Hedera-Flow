import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { PrepaidTokenPurchase } from '@/components/PrepaidTokenPurchase';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Zap, ArrowLeft, Wallet, Plus, History, TrendingUp, AlertTriangle } from 'lucide-react';
import { useAuth } from '@/hooks/useAuth';
import { useMeters } from '@/hooks/useMeters';
import { usePrepaid } from '@/hooks/usePrepaid';

export default function PrepaidMeterPage() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const { meters, isLoading: metersLoading } = useMeters();
  const [selectedMeterId, setSelectedMeterId] = useState<string>('');
  const [showPurchase, setShowPurchase] = useState(false);
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

  const handlePurchaseSuccess = () => {
    setShowPurchase(false);
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'bg-green-500';
      case 'low': return 'bg-yellow-500';
      case 'depleted': return 'bg-red-500';
      default: return 'bg-gray-500';
    }
  };

  const getBalancePercentage = () => {
    if (!balance || !tokens || tokens.length === 0) return 0;
    const totalPurchased = tokens.reduce((sum, t) => sum + t.units_purchased, 0);
    return totalPurchased > 0 ? (balance.total_units / totalPurchased) * 100 : 0;
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 via-blue-50 to-indigo-50 pb-20">
      {/* Header */}
      <div className="bg-white border-b sticky top-0 z-10">
        <div className="max-w-4xl mx-auto px-4 py-4">
          <div className="flex items-center gap-4">
            <Button variant="ghost" size="icon" onClick={() => navigate('/home')}>
              <ArrowLeft className="w-5 h-5" />
            </Button>
            <div className="flex-1">
              <h1 className="text-2xl font-bold">Prepaid Meters</h1>
              <p className="text-sm text-muted-foreground">Manage your prepaid electricity</p>
            </div>
            {user?.hedera_account_id && (
              <Badge variant="outline" className="hidden md:flex gap-2">
                <Wallet className="w-3 h-3" />
                Connected
              </Badge>
            )}
          </div>
        </div>
      </div>

      <div className="max-w-4xl mx-auto px-4 py-6 space-y-6">
        {/* No Meters */}
        {prepaidMeters.length === 0 && (
          <Card>
            <CardContent className="py-16 text-center">
              <Zap className="w-20 h-20 mx-auto mb-4 text-purple-300" />
              <h3 className="text-xl font-semibold mb-2">No Prepaid Meters</h3>
              <p className="text-muted-foreground mb-6">
                Register your first prepaid meter to start buying tokens
              </p>
              <Button onClick={() => navigate('/register-meter')} size="lg">
                <Plus className="w-4 h-4 mr-2" />
                Register Meter
              </Button>
            </CardContent>
          </Card>
        )}

        {/* Meter Selection Grid */}
        {prepaidMeters.length > 0 && !selectedMeterId && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold">Select a Meter</h2>
              <Button variant="outline" size="sm" onClick={() => navigate('/register-meter')}>
                <Plus className="w-4 h-4 mr-2" />
                Add Meter
              </Button>
            </div>
            <div className="grid gap-4">
              {prepaidMeters.map((meter) => (
                <Card
                  key={meter.id}
                  className="cursor-pointer hover:shadow-lg hover:border-purple-400 transition-all"
                  onClick={() => setSelectedMeterId(meter.id)}
                >
                  <CardContent className="p-6">
                    <div className="flex items-start justify-between mb-4">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <h3 className="font-bold text-lg">{meter.meter_id}</h3>
                          {meter.is_primary && (
                            <Badge className="bg-purple-500">Primary</Badge>
                          )}
                        </div>
                        <p className="text-sm text-muted-foreground">
                          {meter.utility_provider}
                        </p>
                        <p className="text-xs text-muted-foreground">
                          {meter.state_province} • {meter.band_classification || 'Standard'}
                        </p>
                      </div>
                      <Zap className="w-8 h-8 text-purple-500" />
                    </div>
                    <Button className="w-full" variant="outline">
                      Manage Meter
                    </Button>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        )}

        {/* Selected Meter View */}
        {selectedMeterId && selectedMeter && (
          <div className="space-y-6">
            {/* Back Button */}
            <Button variant="ghost" onClick={() => { setSelectedMeterId(''); setShowPurchase(false); }}>
              <ArrowLeft className="w-4 h-4 mr-2" />
              All Meters
            </Button>

            {/* Meter Header */}
            <Card className="bg-gradient-to-br from-purple-600 to-blue-600 text-white">
              <CardContent className="p-6">
                <div className="flex items-start justify-between mb-4">
                  <div>
                    <h2 className="text-2xl font-bold mb-1">{selectedMeter.meter_id}</h2>
                    <p className="text-sm opacity-90">{selectedMeter.utility_provider}</p>
                  </div>
                  <Zap className="w-10 h-10 opacity-50" />
                </div>
                {balance && (
                  <div className="space-y-3">
                    <div>
                      <div className="flex items-baseline gap-2">
                        <span className="text-4xl font-bold">{balance.total_units.toFixed(1)}</span>
                        <span className="text-lg opacity-90">kWh</span>
                      </div>
                      <p className="text-sm opacity-75">Available Balance</p>
                    </div>
                    <Progress value={getBalancePercentage()} className="h-2 bg-white/20" />
                    {balance.low_balance_alert && (
                      <div className="flex items-center gap-2 p-3 bg-yellow-500/20 rounded-lg">
                        <AlertTriangle className="w-4 h-4" />
                        <span className="text-sm">Low balance - Top up soon</span>
                      </div>
                    )}
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Quick Actions */}
            <div className="grid grid-cols-2 gap-4">
              <Button
                size="lg"
                className="h-24 flex-col gap-2 bg-purple-600 hover:bg-purple-700"
                onClick={() => setShowPurchase(true)}
              >
                <Plus className="w-6 h-6" />
                <span>Buy Tokens</span>
              </Button>
              <Button
                size="lg"
                variant="outline"
                className="h-24 flex-col gap-2"
                onClick={() => setShowPurchase(false)}
              >
                <History className="w-6 h-6" />
                <span>View History</span>
              </Button>
            </div>

            {/* Purchase Form */}
            {showPurchase && (
              <PrepaidTokenPurchase
                meterId={selectedMeterId}
                onSuccess={handlePurchaseSuccess}
                onCancel={() => setShowPurchase(false)}
              />
            )}

            {/* Token History */}
            {!showPurchase && (
              <Card>
                <CardHeader>
                  <CardTitle>Token History</CardTitle>
                  <CardDescription>
                    {balance?.active_tokens || 0} active token{balance?.active_tokens !== 1 ? 's' : ''}
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  {isLoading ? (
                    <div className="text-center py-8">
                      <div className="animate-spin w-8 h-8 border-4 border-purple-500 border-t-transparent rounded-full mx-auto" />
                      <p className="text-sm text-muted-foreground mt-4">Loading...</p>
                    </div>
                  ) : !tokens || tokens.length === 0 ? (
                    <div className="text-center py-12">
                      <TrendingUp className="w-16 h-16 mx-auto mb-4 text-muted-foreground" />
                      <p className="text-muted-foreground mb-2">No tokens yet</p>
                      <p className="text-sm text-muted-foreground">
                        Purchase your first token to get started
                      </p>
                    </div>
                  ) : (
                    <div className="space-y-3">
                      {tokens.map((token) => (
                        <Card key={token.id} className="hover:shadow-md transition-shadow">
                          <CardContent className="p-4">
                            <div className="flex items-center justify-between mb-3">
                              <div className="flex items-center gap-2">
                                <Badge className={getStatusColor(token.status)}>
                                  {token.status}
                                </Badge>
                                <span className="text-xs text-muted-foreground">
                                  {new Date(token.created_at).toLocaleDateString()}
                                </span>
                              </div>
                              <div className="text-right">
                                <p className="font-bold">{token.amount_hbar.toFixed(2)} ℏ</p>
                                <p className="text-xs text-muted-foreground">
                                  {token.amount_fiat} {token.currency}
                                </p>
                              </div>
                            </div>
                            <div className="space-y-2">
                              <div className="flex justify-between text-sm">
                                <span className="text-muted-foreground">Token ID</span>
                                <span className="font-mono font-semibold">{token.token_id}</span>
                              </div>
                              <div className="flex justify-between text-sm">
                                <span className="text-muted-foreground">Remaining</span>
                                <span className="font-semibold">
                                  {token.units_remaining.toFixed(2)} / {token.units_purchased.toFixed(2)} kWh
                                </span>
                              </div>
                              <Progress
                                value={(token.units_remaining / token.units_purchased) * 100}
                                className="h-1"
                              />
                            </div>
                          </CardContent>
                        </Card>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
