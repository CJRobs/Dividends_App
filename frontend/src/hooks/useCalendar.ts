/**
 * Custom hooks for calendar data fetching.
 */

import { useQuery } from '@tanstack/react-query';
import { getCalendarView, getUpcomingDividends } from '@/lib/api';

export function useCalendar(year?: number, months: number = 12) {
  return useQuery({
    queryKey: ['calendar', year, months],
    queryFn: () => getCalendarView(year, months),
  });
}

export function useUpcomingDividends(days: number = 30) {
  return useQuery({
    queryKey: ['upcoming-dividends', days],
    queryFn: () => getUpcomingDividends(days),
  });
}
