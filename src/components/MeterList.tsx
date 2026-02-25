import { useMeters } from '@/hooks/useMeters';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Loader2, Zap, MapPin, Building2, Calendar, Star, Trash2, AlertCircle } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import type { Meter } from '@/types/api';

interface MeterListProps {
  onMeterSelect?: (meter: Meter) => void;
  onMeterDelete?: (meterId: string) => void;
  showActions?: boolean;
}

export function MeterList({ onMeterSelect, onMeterDelete, showActions = false }: MeterListProps) {
  const { meters, isLoading, error, deleteMeter, isDeleting } = useMeters();

  const handleDelete = (meterId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (window.confirm('Are you sure you want to delete this meter?')) {
      deleteMeter(meterId);
      if (onMeterDelete) {
        onMeterDelete(meterId);
      }
    }
  };

  const getMeterTypeLabel = (type: string) => {
    return type === 'prepaid' ? 'Prepaid' : 'Postpaid';
  };

  const getMeterTypeColor = (type: string) => {
    return type === 'prepaid' ? 'bg-blue-100 text-blue-800 border-blue-200' : 'bg-purple-100 text-purple-800 border-purple-200';
  };

  const getBandLabel = (band?: string) => {
    if (!band) return null;
    const bandInfo: Record<string, string> = {
      'A': '20+ hours',
      'B': '16-20 hours',
      'C': '12-16 hours',
      'D': '8-12 hours',
      'E': '<8 hours',
    };
    return `Band ${band} (${bandInfo[band] || 'Unknown'})`;
  };

  if (isLoading) {
    return (
      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-col items-center justify-center py-8">
            <Loader2 className="w-8 h-8 animate-spin text-muted-foreground mb-3" />
            <p className="text-sm text-muted-foreground">Loading meters...</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Alert variant="destructive">
        <AlertCircle className="h-4 w-4" />
        <AlertDescription>
          {error instanceof Error ? error.message : 'Failed to load meters'}
        </AlertDescription>
      </Alert>
    );
  }

  if (!meters || meters.length === 0) {
    return (
      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-col items-center justify-center py-8 text-center">
            <div className="w-16 h-16 rounded-full bg-muted flex items-center justify-center mb-4">
              <Zap className="w-8 h-8 text-muted-foreground" />
            </div>
            <h3 className="text-lg font-semibold mb-2">No Meters Registered</h3>
            <p className="text-sm text-muted-foreground mb-4">
              Register your first electricity meter to start verifying bills
            </p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold">Your Meters</h3>
          <p className="text-sm text-muted-foreground">
            {meters.length} {meters.length === 1 ? 'meter' : 'meters'} registered
          </p>
        </div>
      </div>

      <div className="space-y-3">
        {meters.map((meter) => (
          <Card
            key={meter.id}
            className={`transition-all hover:shadow-md ${
              onMeterSelect ? 'cursor-pointer' : ''
            } ${meter.is_primary ? 'border-accent' : ''}`}
            onClick={() => onMeterSelect && onMeterSelect(meter)}
          >
            <CardContent className="p-4">
              <div className="space-y-3">
                {/* Header Row */}
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <h4 className="font-semibold text-base">{meter.meter_id}</h4>
                      {meter.is_primary && (
                        <Badge className="bg-accent text-accent-foreground border-accent">
                          <Star className="w-3 h-3 mr-1" />
                          Primary
                        </Badge>
                      )}
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge className={getMeterTypeColor(meter.meter_type)}>
                        {getMeterTypeLabel(meter.meter_type)}
                      </Badge>
                      {meter.band_classification && (
                        <Badge variant="outline" className="text-xs">
                          {getBandLabel(meter.band_classification)}
                        </Badge>
                      )}
                    </div>
                  </div>
                  {showActions && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={(e) => handleDelete(meter.id, e)}
                      disabled={isDeleting}
                      className="text-destructive hover:text-destructive hover:bg-destructive/10"
                    >
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  )}
                </div>

                {/* Details */}
                <div className="space-y-2 text-sm">
                  <div className="flex items-center gap-2 text-muted-foreground">
                    <Building2 className="w-4 h-4" />
                    <span>{meter.utility_provider}</span>
                  </div>
                  <div className="flex items-center gap-2 text-muted-foreground">
                    <MapPin className="w-4 h-4" />
                    <span>{meter.state_province}</span>
                  </div>
                  {meter.address && (
                    <div className="flex items-start gap-2 text-muted-foreground">
                      <MapPin className="w-4 h-4 mt-0.5" />
                      <span className="text-xs">{meter.address}</span>
                    </div>
                  )}
                  <div className="flex items-center gap-2 text-muted-foreground text-xs">
                    <Calendar className="w-3.5 h-3.5" />
                    <span>
                      Registered {formatDistanceToNow(new Date(meter.created_at), { addSuffix: true })}
                    </span>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
