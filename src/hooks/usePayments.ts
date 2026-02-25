import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { paymentsApi } from '@/lib/api';

export const usePayments = () => {
  return useQuery({
    queryKey: ['payments'],
    queryFn: paymentsApi.list,
  });
};

export const usePayment = (paymentId: string) => {
  return useQuery({
    queryKey: ['payment', paymentId],
    queryFn: () => paymentsApi.get(paymentId),
    enabled: !!paymentId,
  });
};

export const usePaymentReceipt = (paymentId: string) => {
  return useQuery({
    queryKey: ['payment-receipt', paymentId],
    queryFn: () => paymentsApi.getReceipt(paymentId),
    enabled: !!paymentId,
  });
};

export const usePreparePayment = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: paymentsApi.prepare,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['payments'] });
    },
  });
};

export const useConfirmPayment = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ paymentId, transactionId }: { paymentId: string; transactionId: string }) =>
      paymentsApi.confirm(paymentId, transactionId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['payments'] });
      queryClient.invalidateQueries({ queryKey: ['bills'] });
    },
  });
};
