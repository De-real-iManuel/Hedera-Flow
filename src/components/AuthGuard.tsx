import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

interface AuthGuardProps {
  children: React.ReactNode;
}

const AuthGuard = ({ children }: AuthGuardProps) => {
  const navigate = useNavigate();

  useEffect(() => {
    const token = localStorage.getItem('auth_token');
    if (!token) {
      navigate('/auth');
    }
  }, [navigate]);

  // Check if user is authenticated
  const token = localStorage.getItem('auth_token');
  if (!token) {
    return null; // Don't render anything while redirecting
  }

  return <>{children}</>;
};

export default AuthGuard;