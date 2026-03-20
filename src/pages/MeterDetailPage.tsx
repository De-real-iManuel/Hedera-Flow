import { useParams, useNavigate } from 'react-router-dom';
import { useMeters } from '@/hooks/useMeters';
import AppHeader from '@/components/AppHeader';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ArrowLeft, Zap, MapPin, Building2, Plus } from 'lucide-react';

const MeterDetailPage = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { meters, isLoading } = useMeters();

  const meter = meters?.find((m: any) => m.id === id);

  if (isLoading) {
    return (
      <div className="min-h-screen bg-background pb-24">
        <AppHeader title="Meter Details" />
        <div className="flex items-center justify-center py-20">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-600" />
        </div>
      </div>
    );
  }

  if (!meter) {
    return (
      <div className="min-h-screen bg-background pb-24">
        <AppHeader title="Meter Details" />
        <div className="px-5 py-6 space-y-4">
          <Button variant="ghost" size="sm" onClick={() => navigate('/meters')}>
            <ArrowLeft className="w-4 h-4 mr-2" /> Back to Meters
          </Button>
          <Card>
            <CardContent className="pt-6 text-center py-12">
              <p className="text-muted-foreground">Meter not found.</p>
              <Button className="mt-4" onClick={() => navigate('/meters')}>
                View All Meters
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background pb-24">
      <AppHeader title="Meter Details" />
      <div className="px-5 py-6 space-y-4">
        <Button variant="ghost" size="sm" onClick={() => navigate('/meters')}>
          <ArrowLeft className="w-4 h-4 mr-2" /> Back to Meters
        </Button>

        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="flex items-center gap-2">
                <Zap className="w-5 h-5 text-purple-600" />
                {meter.meter_id}
              </CardTitle>
              <Badge variant={meter.meter_type === 'prepaid' ? 'default' : 'secondary'}>
                {meter.meter_type}
              </Badge>
            </div>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Building2 className="w-4 h-4" />
              <span>{meter.utility_provider}</span>
            </div>
            {meter.state_province && (
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <MapPin className="w-4 h-4" />
                <span>{meter.state_province}</span>
              </div>
            )}
            {meter.band_classification && (
              <div className="text-sm">
                <span className="text-muted-foreground">Band: </span>
                <span className="font-medium">Band {meter.band_classification}</span>
              </div>
            )}
            {meter.address && (
              <div className="text-sm text-muted-foreground">{meter.address}</div>
            )}
          </CardContent>
        </Card>

        {meter.meter_type === 'prepaid' && (
          <Button
            className="w-full bg-purple-600 hover:bg-purple-700"
            onClick={() => navigate(`/prepaid?meter=${meter.id}`)}
          >
            <Plus className="w-4 h-4 mr-2" />
            Buy Prepaid Tokens
          </Button>
        )}

        <Button variant="outline" className="w-full" onClick={() => navigate('/scan')}>
          Scan Bill / Meter Reading
        </Button>
      </div>
    </div>
  );
};

export default MeterDetailPage;
