/**
 * Custom hooks for monthly analysis data fetching.
 */

import { useQuery } from '@tanstack/react-query';
import {
  getMonthlyAnalysis,
  getMonthlyByYear,
  getMonthlyHeatmap,
  getMonthlyByCompany,
  getMonthlyCoverage,
} from '@/lib/api';
import type {
  MonthlyAnalysisResponse,
  MonthlyByYearData,
  HeatmapData,
  MonthlyByCompanyResponse,
  CoverageData,
} from '@/types';

export function useMonthlyAnalysis() {
  return useQuery<MonthlyAnalysisResponse>({
    queryKey: ['monthly-analysis'],
    queryFn: getMonthlyAnalysis,
  });
}

export function useMonthlyByYear() {
  return useQuery<MonthlyByYearData>({
    queryKey: ['monthly-by-year'],
    queryFn: getMonthlyByYear,
  });
}

export function useMonthlyHeatmap() {
  return useQuery<HeatmapData>({
    queryKey: ['monthly-heatmap'],
    queryFn: getMonthlyHeatmap,
  });
}

export function useMonthlyByCompany(companies?: string[], month?: string) {
  return useQuery<MonthlyByCompanyResponse>({
    queryKey: ['monthly-by-company', companies, month],
    queryFn: () => getMonthlyByCompany(companies, month),
  });
}

export function useMonthlyCoverage(monthlyExpenses: number = 2000) {
  return useQuery<CoverageData>({
    queryKey: ['monthly-coverage', monthlyExpenses],
    queryFn: () => getMonthlyCoverage(monthlyExpenses),
  });
}
