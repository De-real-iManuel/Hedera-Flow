import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { authApi } from '@/lib/api';
import type { LoginRequest, RegisterRequest, User } from '@/types/api';
import { useNavigate } from 'react-router-dom';

export const useAuth = () => {
  const queryClient = useQueryClient();
  const navigate = useNavigate();

  // Get current user
  const { data: user, isLoading, error } = useQuery({
    queryKey: ['user'],
    queryFn: authApi.getCurrentUser,
    enabled: !!localStorage.getItem('auth_token'),
    retry: false,
  });

  // Login mutation
  const loginMutation = useMutation({
    mutationFn: authApi.login,
    onSuccess: (data) => {
      localStorage.setItem('auth_token', data.token);
      localStorage.setItem('user', JSON.stringify(data.user));
      queryClient.setQueryData(['user'], data.user);
      // Clear splash screen flag so it shows again after login
      sessionStorage.removeItem('hasSeenSplash');
      navigate('/home');
    },
  });

  // Register mutation
  const registerMutation = useMutation({
    mutationFn: authApi.register,
    onSuccess: (data) => {
      localStorage.setItem('auth_token', data.token);
      localStorage.setItem('user', JSON.stringify(data.user));
      queryClient.setQueryData(['user'], data.user);
      // Clear splash screen flag so it shows after registration
      sessionStorage.removeItem('hasSeenSplash');
      navigate('/home');
    },
  });

  // Logout
  const logout = () => {
    authApi.logout();
    queryClient.clear();
    navigate('/login');
  };

  return {
    user,
    isLoading,
    error,
    login: loginMutation.mutate,
    register: registerMutation.mutate,
    logout,
    isLoginLoading: loginMutation.isPending,
    isRegisterLoading: registerMutation.isPending,
    loginError: loginMutation.error,
    registerError: registerMutation.error,
  };
};
