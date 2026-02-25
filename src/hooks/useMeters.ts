import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { metersApi } from '@/lib/api';
import type { MeterCreateRequest } from '@/types/api';

export const useMeters = () => {
  const queryClient = useQueryClient();

  // List all meters
  const { data: meters, isLoading, error } = useQuery({
    queryKey: ['meters'],
    queryFn: metersApi.list,
  });

  // Create meter mutation
  const createMeterMutation = useMutation({
    mutationFn: metersApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['meters'] });
    },
  });

  // Update meter mutation
  const updateMeterMutation = useMutation({
    mutationFn: ({ meterId, data }: { meterId: string; data: Partial<MeterCreateRequest> }) =>
      metersApi.update(meterId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['meters'] });
    },
  });

  // Delete meter mutation
  const deleteMeterMutation = useMutation({
    mutationFn: metersApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['meters'] });
    },
  });

  return {
    meters,
    isLoading,
    error,
    createMeter: createMeterMutation.mutate,
    updateMeter: updateMeterMutation.mutate,
    deleteMeter: deleteMeterMutation.mutate,
    isCreating: createMeterMutation.isPending,
    isUpdating: updateMeterMutation.isPending,
    isDeleting: deleteMeterMutation.isPending,
    createError: createMeterMutation.error,
    updateError: updateMeterMutation.error,
    deleteError: deleteMeterMutation.error,
  };
};

export const useMeter = (meterId: string) => {
  return useQuery({
    queryKey: ['meter', meterId],
    queryFn: () => metersApi.get(meterId),
    enabled: !!meterId,
  });
};
