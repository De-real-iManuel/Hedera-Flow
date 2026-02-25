import { useQuery } from '@tanstack/react-query';
import { billsApi } from '@/lib/api';

export const useBills = (meterId?: string) => {
  return useQuery({
    queryKey: ['bills', meterId],
    queryFn: () => billsApi.list(meterId),
  });
};

export const useBill = (billId: string) => {
  return useQuery({
    queryKey: ['bill', billId],
    queryFn: () => billsApi.get(billId),
    enabled: !!billId,
  });
};

export const useBillBreakdown = (billId: string) => {
  return useQuery({
    queryKey: ['bill-breakdown', billId],
    queryFn: () => billsApi.getBreakdown(billId),
    enabled: !!billId,
  });
};
