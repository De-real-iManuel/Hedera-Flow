import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { authApi } from '@/lib/api';
import type { LoginRequest, RegisterRequest, User } from '@/types/api';
import { useNavigate } from 'react-router-dom';

export const useAuth = () => {
  const queryClient = useQueryClient();
  const navigate = useNavigate();

  // Get current user - no longer depends on localStorage token
  const { data: user, isLoading, error } = useQuery({
    queryKey: ['user'],
    queryFn: authApi.getCurrentUser,
    retry: (failureCount, error: any) => {
      // Don't retry on 401 errors (unauthenticated)
      if (error?.response?.status === 401) {
        return false;
      }
      return failureCount < 3;
    },
  });

  // Login mutation
  const loginMutation = useMutation({
    mutationFn: authApi.login,
    onSuccess: (data) => {
      // No need to store token - it's in httpOnly cookie
      queryClient.setQueryData(['user'], data);
      // Clear splash screen flag so it shows again after login
      sessionStorage.removeItem('hasSeenSplash');
      navigate('/home');
    },
  });

  // Register mutation
  const registerMutation = useMutation({
    mutationFn: authApi.register,
    onSuccess: (data) => {
      // No need to store token - it's in httpOnly cookie
      queryClient.setQueryData(['user'], data);
      // Clear splash screen flag so it shows after registration
      sessionStorage.removeItem('hasSeenSplash');
      navigate('/home');
    },
  });

  // Logout
  const logout = async () => {
    try {
      await authApi.logout();
    } catch (error) {
      // Even if logout fails on server, clear client state
      console.warn('Logout request failed, but clearing client state:', error);
    } finally {
      queryClient.clear();
      navigate('/auth');
    }
  };

  // Token refresh function (called automatically by interceptor)
  const refreshToken = async () => {
    try {
      const userData = await authApi.refreshToken();
      queryClient.setQueryData(['user'], userData);
      return userData;
    } catch (error) {
      // Refresh failed, clear user data and redirect
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
