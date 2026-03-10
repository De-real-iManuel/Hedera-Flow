import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { prepaidApi } from '@/lib/api/prepaid';
import type { BuyTokenRequest } from '@/lib/api/prepaid';
import { toast } from 'sonner';

export function usePrepaid(meterId?: string) {
  const queryClient = useQueryClient();

  // Get balance for a meter - disabled until backend is fixed
  const { data: balance, isLoading: balanceLoading } = useQuery({
    queryKey: ['prepaid-balance', meterId],
    queryFn: () => prepaidApi.getBalance(meterId!),
    enabled: false, // Disabled temporarily
  });

  // List all tokens - disabled until backend is fixed
  const { data: tokens, isLoading: tokensLoading } = useQuery({
    queryKey: ['prepaid-tokens', meterId],
    queryFn: () => prepaidApi.listTokens(meterId),
    enabled: false, // Disabled temporarily
  });

  // Buy token mutation
  const buyToken = useMutation({
    mutationFn: (data: BuyTokenRequest) => prepaidApi.buy(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['prepaid-balance'] });
      queryClient.invalidateQueries({ queryKey: ['prepaid-tokens'] });
      toast.success('Token purchased successfully!');
    },
    onError: (error: any) => {
      toast.error('Purchase failed', {
        description: error.response?.data?.detail || error.message,
      });
    },
  });

  // Confirm token mutation
  const confirmToken = useMutation({
    mutationFn: ({ meterId, hederaTxId }: { meterId: string; hederaTxId: string }) =>
      prepaidApi.confirm(meterId, hederaTxId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['prepaid-balance'] });
      queryClient.invalidateQueries({ queryKey: ['prepaid-tokens'] });
    },
  });

  return {
    balance,
    tokens,
    isLoading: balanceLoading || tokensLoading,
    buyToken: buyToken.mutate,
    confirmToken: confirmToken.mutate,
    isBuying: buyToken.isPending,
    isConfirming: confirmToken.isPending,
  };
}
