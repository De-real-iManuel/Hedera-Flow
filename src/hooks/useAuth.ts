import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { authApi } from '@/lib/api';
import { setMemoryToken } from '@/lib/api-client';
import type { LoginRequest, RegisterRequest, User } from '@/types/api';
import { useNavigate } from 'react-router-dom';

export const useAuth = () => {
  const queryClient = useQueryClient();
  const navigate = useNavigate();

  const { data: user, isLoading, error } = useQuery({
    queryKey: ['user'],
    queryFn: authApi.getCurrentUser,
    staleTime: 5 * 60 * 1000,
    retry: (failureCount, error: any) => {
      if (error?.response?.status === 401) return false;
      return failureCount < 2;
    },
  });

  const loginMutation = useMutation({
    mutationFn: authApi.login,
    onSuccess: (data) => {
      // Store token in memory as fallback if cookies are blocked cross-origin
      if (data.access_token) setMemoryToken(data.access_token);
      queryClient.setQueryData(['user'], data);
      sessionStorage.removeItem('hasSeenSplash');
      navigate('/home');
    },
  });

  const registerMutation = useMutation({
    mutationFn: authApi.register,
    onSuccess: (data) => {
      if (data.access_token) setMemoryToken(data.access_token);
      queryClient.setQueryData(['user'], data);
      sessionStorage.removeItem('hasSeenSplash');
      navigate('/home');
    },
  });

  const logout = async () => {
    try {
      await authApi.logout();
    } catch (error) {
      console.warn('Logout request failed, but clearing client state:', error);
    } finally {
      setMemoryToken(null);
      queryClient.clear();
      navigate('/auth');
    }
  };

  const refreshToken = async () => {
    try {
      const userData = await authApi.refreshToken();
      queryClient.setQueryData(['user'], userData);
      return userData;
    } catch (error) {
      setMemoryToken(null);
      queryClient.setQueryData(['user'], null);
      navigate('/auth');
      throw error;
    }
  };

  return {
    user,
    isLoading,
    error,
    login: loginMutation.mutate,
    register: registerMutation.mutate,
    logout,
    refreshToken,
    isLoginLoading: loginMutation.isPending,
    isRegisterLoading: registerMutation.isPending,
    loginError: loginMutation.error,
    registerError: registerMutation.error,
  };
};
