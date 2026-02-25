import { useNavigate } from 'react-router-dom';
import { MeterList } from '@/components/MeterList';
import AppHeader from '@/components/AppHeader';
import { Button } from '@/components/ui/button';
import { Plus } from 'lucide-react';

const MetersPage = () => {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-background pb-24">
      <AppHeader title="My Meters" />
      
      <div className="px-5 py-6 space-y-4">
        {/* Add Meter Button */}
        <Button
          onClick={() => navigate('/register-meter')}
          className="w-full"
        >
          <Plus className="w-4 h-4 mr-2" />
          Register New Meter
        </Button>
        
        {/* Meter List */}
        <MeterList
          showActions={true}
          onMeterSelect={(meter) => {
            // Navigate to meter details or verification page
            console.log('Selected meter:', meter);
          }}
        />
      </div>
    </div>
  );
};

export default MetersPage;
