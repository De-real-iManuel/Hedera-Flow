import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Zap, Shield, ArrowLeft, ArrowRight, TrendingUp, Lock } from 'lucide-react';
import { useAuth } from '@/hooks/useAuth';
import { useMeters } from '@/hooks/useMeters';

export default function MeterHubPage() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const { meters, isLoading: metersLoading } = useMeters();

  const prepaidCount = meters?.filter(m => m.meter_type === 'prepaid').length || 0;

  if (metersLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin w-8 h-8 border-4 border-purple-500 border-t-transparent rounded-full" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 via-blue-50 to-indigo-50 pb-20">
      {/* Header */}
      <div className="bg-white border-b">
        <div className="max-w-4xl mx-auto px-4 py-4">
          <div className="flex items-center gap-4">
            <Button variant="ghost" size="icon" onClick={() => navigate('/home')}>
              <ArrowLeft className="w-5 h-5" />
            </Button>
            <div className="flex-1">
              <h1 className="text-2xl font-bold">Meter Management</h1>
              <p className="text-sm text-muted-foreground">Prepaid tokens & smart verification</p>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-4xl mx-auto px-4 py-8 space-y-6">
        {/* Welcome Card */}
        <Card className="bg-gradient-to-br from-purple-600 to-blue-600 text-white">
          <CardContent className="p-6">
            <h2 className="text-2xl font-bold mb-2">Welcome back!</h2>
            <p className="text-sm opacity-90 mb-4">
              Manage your prepaid electricity and verify consumption with blockchain security
            </p>
            <div className="flex items-center gap-4">
              <div className="p-3 bg-white/10 rounded-lg">
                <p className="text-2xl font-bold">{prepaidCount}</p>
                <p className="text-xs opacity-75">Active Meters</p>
              </div>
              {user?.hedera_account_id && (
                <div className="p-3 bg-white/10 rounded-lg flex-1">
                  <p className="text-xs opacity-75 mb-1">Wallet Connected</p>
                  <p className="text-sm font-mono">{user.hedera_account_id.slice(0, 15)}...</p>
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Main Features */}
        <div className="grid gap-6">
          {/* Prepaid Meters */}
          <Card className="hover:shadow-xl transition-all cursor-pointer group" onClick={() => navigate('/prepaid-meter')}>
            <CardContent className="p-6">
              <div className="flex items-start justify-between mb-4">
                <div className="p-3 bg-purple-100 rounded-xl group-hover:bg-purple-200 transition-colors">
                  <Zap className="w-8 h-8 text-purple-600" />
                </div>
                <ArrowRight className="w-5 h-5 text-muted-foreground group-hover:text-purple-600 transition-colors" />
              </div>
              <h3 className="text-xl font-bold mb-2">Prepaid Meters</h3>
              <p className="text-sm text-muted-foreground mb-4">
                Buy electricity tokens with HBAR and manage your prepaid balance
              </p>
              <div className="flex gap-2">
                <Badge variant="outline" className="gap-1">
                  <TrendingUp className="w-3 h-3" />
                  Buy Tokens
                </Badge>
                <Badge variant="outline">View Balance</Badge>
                <Badge variant="outline">History</Badge>
              </div>
            </CardContent>
          </Card>

          {/* Smart Meters */}
          <Card className="hover:shadow-xl transition-all cursor-pointer group" onClick={() => navigate('/smart-meter')}>
            <CardContent className="p-6">
              <div className="flex items-start justify-between mb-4">
                <div className="p-3 bg-blue-100 rounded-xl group-hover:bg-blue-200 transition-colors">
                  <Shield className="w-8 h-8 text-blue-600" />
                </div>
                <ArrowRight className="w-5 h-5 text-muted-foreground group-hover:text-blue-600 transition-colors" />
              </div>
              <h3 className="text-xl font-bold mb-2">Smart Meters</h3>
              <p className="text-sm text-muted-foreground mb-4">
                Verify consumption with cryptographic signatures and blockchain logging
              </p>
              <div className="flex gap-2">
                <Badge variant="outline" className="gap-1">
                  <Lock className="w-3 h-3" />
                  ED25519
                </Badge>
                <Badge variant="outline">Verify</Badge>
                <Badge variant="outline">HCS Logs</Badge>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Quick Stats */}
        {prepaidCount > 0 && (
          <Card>
            <CardHeader>
              <CardTitle>Quick Overview</CardTitle>
              <CardDescription>Your meter statistics</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-3 gap-4">
                <div className="text-center p-4 bg-purple-50 rounded-lg">
                  <p className="text-2xl font-bold text-purple-600">{prepaidCount}</p>
                  <p className="text-xs text-muted-foreground mt-1">Prepaid Meters</p>
                </div>
                <div className="text-center p-4 bg-blue-50 rounded-lg">
                  <p className="text-2xl font-bold text-blue-600">0</p>
                  <p className="text-xs text-muted-foreground mt-1">Active Tokens</p>
                </div>
                <div className="text-center p-4 bg-green-50 rounded-lg">
                  <p className="text-2xl font-bold text-green-600">0</p>
                  <p className="text-xs text-muted-foreground mt-1">Verified Logs</p>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* No Meters CTA */}
        {prepaidCount === 0 && (
          <Card>
            <CardContent className="py-12 text-center">
              <div className="w-16 h-16 bg-purple-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <Zap className="w-8 h-8 text-purple-600" />
              </div>
              <h3 className="text-lg font-semibold mb-2">Get Started</h3>
              <p className="text-sm text-muted-foreground mb-6">
                Register your first meter to start using prepaid and smart features
              </p>
              <Button onClick={() => navigate('/register-meter')} size="lg">
                Register Meter
              </Button>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}
