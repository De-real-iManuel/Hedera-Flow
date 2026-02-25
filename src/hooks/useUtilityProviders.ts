import { useQuery } from '@tanstack/react-query';
import { utilityProvidersApi } from '@/lib/api';

export const useUtilityProviders = (countryCode?: string, stateProvince?: string) => {
  return useQuery({
    queryKey: ['utility-providers', countryCode, stateProvince],
    queryFn: () => utilityProvidersApi.list(countryCode, stateProvince),
    enabled: !!countryCode,
  });
};

export const useUtilityProvider = (providerId: string) => {
  return useQuery({
    queryKey: ['utility-provider', providerId],
    queryFn: () => utilityProvidersApi.get(providerId),
    enabled: !!providerId,
  });
};
