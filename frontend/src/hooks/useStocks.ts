/**
 * Custom hooks for stock analysis data fetching.
 */

import { useQuery } from '@tanstack/react-query';
import {
  getStocksOverview,
  getStocksList,
  getStocksByPeriod,
  getStocksGrowth,
  getStockDistribution,
  getConcentration,
  getStockDetails,
} from '@/lib/api';
import type {
  StockOverviewResponse,
  StockListItem,
  PeriodAnalysisResponse,
  GrowthAnalysisResponse,
  StockDistribution,
  ConcentrationData,
  StockAnalysisDetailResponse,
} from '@/types';

export function useStocksOverview() {
  return useQuery<StockOverviewResponse>({
    queryKey: ['stocks-overview'],
    queryFn: getStocksOverview,
  });
}

export function useStocksList(limit: number = 50) {
  return useQuery<StockListItem[]>({
    queryKey: ['stocks-list', limit],
    queryFn: () => getStocksList(limit),
  });
}

export function useStocksByPeriod(periodType: 'Monthly' | 'Quarterly' | 'Yearly' = 'Monthly') {
  return useQuery<PeriodAnalysisResponse>({
    queryKey: ['stocks-by-period', periodType],
    queryFn: () => getStocksByPeriod(periodType),
  });
}

export function useStocksGrowth(periodType: 'Monthly' | 'Quarterly' | 'Yearly' = 'Monthly') {
  return useQuery<GrowthAnalysisResponse>({
    queryKey: ['stocks-growth', periodType],
    queryFn: () => getStocksGrowth(periodType),
  });
}

export function useStockDistribution() {
  return useQuery<StockDistribution[]>({
    queryKey: ['stock-distribution'],
    queryFn: getStockDistribution,
  });
}

export function useConcentration() {
  return useQuery<ConcentrationData>({
    queryKey: ['concentration'],
    queryFn: getConcentration,
  });
}

export function useStockDetails(ticker: string) {
  return useQuery<StockAnalysisDetailResponse>({
    queryKey: ['stock-details', ticker],
    queryFn: () => getStockDetails(ticker),
    enabled: !!ticker,
  });
}
