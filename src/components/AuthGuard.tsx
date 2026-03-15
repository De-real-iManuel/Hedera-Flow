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
    // If there's an authentication error (401), redirect to auth page
    if (error?.response?.status === 401) {
      navigate('/auth');
    }
  }, [error, navigate]);

  // Show loading state while checking authentication
  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  // If no user and not loading, redirect to auth
  if (!user && !isLoading) {
    navigate('/auth');
    return null;
  }

  // User is authenticated, render children
  return <>{children}</>;
};

export default AuthGuard;