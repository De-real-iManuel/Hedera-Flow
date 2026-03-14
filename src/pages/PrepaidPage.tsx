import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { PrepaidTokenPurchase } from '@/components/PrepaidTokenPurchase';
import { TransactionHistory } from '@/components/TransactionHistory';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Zap, Clock, AlertCircle, ArrowLeft, Wallet } from 'lucide-react';
import { useAuth } from '@/hooks/useAuth';
import { useMeters } from '@/hooks/useMeters';
import { usePrepaid } from '@/hooks/usePrepaid';
import { toast } from 'sonner';

export default function PrepaidPage() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const { meters, isLoading: metersLoading } = useMeters();
  const [selectedMeterId, setSelectedMeterId] = useState<string>('');
  const { tokens, isLoading } = usePrepaid(selectedMeterId || undefined);

  const prepaidMeters = meters?.filter(m => m.meter_type === 'prepaid') || [];

  if (metersLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin w-8 h-8 border-4 border-purple-500 border-t-transparent rounded-full" />
      </div>
    );
  }

  const handlePurchaseSuccess = (tokenId: string) => {
    toast.success('Token purchased successfully!');
    navigate(`/prepaid/token/${tokenId}`);
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
            <Button
              variant="ghost"
              size="icon"
              onClick={() => navigate('/')}
            >
              <ArrowLeft className="w-5 h-5" />
            </Button>
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Prepaid Tokens</h1>
              <p className="text-muted-foreground">Buy electricity tokens with HBAR</p>
            </div>
          </div>
          {user?.hedera_account_id && (
            <Badge variant="outline" className="gap-2">
              <Wallet className="w-4 h-4" />
              {user.hedera_account_id}
            </Badge>
          )}
        </div>

        {/* No Prepaid Meters */}
        {prepaidMeters.length === 0 && (
          <Card>
            <CardContent className="py-12 text-center">
              <Zap className="w-16 h-16 mx-auto mb-4 text-muted-foreground" />
              <h3 className="text-xl font-semibold mb-2">No Prepaid Meters</h3>
              <p className="text-muted-foreground mb-6">
                Register a prepaid meter to start buying tokens
              </p>
              <Button onClick={() => navigate('/meters/register')}>
                Register Meter
              </Button>
            </CardContent>
          </Card>
        )}

        {/* Meter Selection & Purchase */}
        {prepaidMeters.length > 0 && (
          <Tabs defaultValue="buy" className="space-y-6">
            <TabsList className="grid w-full max-w-md grid-cols-2">
              <TabsTrigger value="buy">Buy Tokens</TabsTrigger>
              <TabsTrigger value="history">Token History</TabsTrigger>
            </TabsList>

            {/* Buy Tab */}
            <TabsContent value="buy" className="space-y-6">
              {/* Meter Selection */}
              {!selectedMeterId && (
                <Card>
                  <CardHeader>
                    <CardTitle>Select Meter</CardTitle>
                    <CardDescription>Choose which meter to buy tokens for</CardDescription>
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
                          {meter.is_primary && (
                            <Badge>Primary</Badge>
                          )}
                        </CardContent>
                      </Card>
                    ))}
                  </CardContent>
                </Card>
              )}

              {/* Purchase Form */}
              {selectedMeterId && (
                <div className="space-y-4">
                  <Button
                    variant="ghost"
                    onClick={() => setSelectedMeterId('')}
                    className="mb-2"
                  >
                    <ArrowLeft className="w-4 h-4 mr-2" />
                    Change Meter
                  </Button>
                  <PrepaidTokenPurchase
                    meterId={selectedMeterId}
                    onSuccess={handlePurchaseSuccess}
                    onCancel={() => setSelectedMeterId('')}
                  />
                </div>
              )}
            </TabsContent>

            {/* History Tab */}
            <TabsContent value="history" className="space-y-4">
              <TransactionHistory 
                meterId={selectedMeterId || undefined}
                showFilters={true}
                pageSize={20}
              />
            </TabsContent>
          </Tabs>
        )}
      </div>
    </div>
  );
}
