import { useNavigate } from 'react-router-dom';
import { MeterRegistrationForm } from '@/components/MeterRegistrationForm';
import AppHeader from '@/components/AppHeader';
import { ArrowLeft } from 'lucide-react';
import { Button } from '@/components/ui/button';

const RegisterMeterPage = () => {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-background pb-24">
      <AppHeader />
      
      <div className="px-5 py-6 space-y-4">
        {/* Back Button */}
        <Button
          variant="ghost"
          size="sm"
          onClick={() => navigate(-1)}
          className="mb-2"
        >
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back
        </Button>
        
        {/* Form */}
        <MeterRegistrationForm
          onSuccess={() => {
            // Navigate to home or meters list after successful registration
            navigate('/');
          }}
          onCancel={() => navigate(-1)}
        />
      </div>
    </div>
  );
};

export default RegisterMeterPage;
