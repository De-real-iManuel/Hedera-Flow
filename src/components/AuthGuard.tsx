import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/hooks/useAuth';

interface AuthGuardProps {
  children: React.ReactNode;
}

const AuthGuard = ({ children }: AuthGuardProps) => {
  const navigate = useNavigate();
  const { user, isLoading, error } = useAuth();

  useEffect(() => {
    if (!isLoading) {
      // 401 means not authenticated — redirect to auth
      // Other errors (network, 500) — don't redirect, let the page handle it
      const is401 = (error as any)?.response?.status === 401;
      if (!user && (is401 || !error)) {
        navigate('/auth');
      }
    }
  }, [isLoading, user, error, navigate]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
      </div>
    );
  }

  if (!user) return null;

  return <>{children}</>;
};

export default AuthGuard;
