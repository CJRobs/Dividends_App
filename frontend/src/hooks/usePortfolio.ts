/**
 * Custom hooks for portfolio data fetching.
 */

import { useQuery } from '@tanstack/react-query';
import { getPortfolioSummary, getCompleteOverview } from '@/lib/api';

// Complete overview with all data
export function useOverview() {
  return useQuery({
    queryKey: ['portfolio-overview'],
    queryFn: getCompleteOverview,
  });
}

export function usePortfolioSummary() {
  return useQuery({
    queryKey: ['portfolio-summary'],
    queryFn: getPortfolioSummary,
  });
}
