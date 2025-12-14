/**
 * Zustand store for portfolio state management with localStorage persistence.
 */

import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';

interface PortfolioStore {
  // UI State
  sidebarOpen: boolean;
  toggleSidebar: () => void;
  setSidebarOpen: (open: boolean) => void;

  // Filter State
  selectedYear: number | null;
  setSelectedYear: (year: number | null) => void;

  currency: string;
  setCurrency: (currency: string) => void;

  // Date Range
  startDate: Date | null;
  endDate: Date | null;
  setDateRange: (start: Date | null, end: Date | null) => void;
}

export const usePortfolioStore = create<PortfolioStore>()(
  persist(
    (set) => ({
      // UI State
      sidebarOpen: true,
      toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
      setSidebarOpen: (open) => set({ sidebarOpen: open }),

      // Filter State
      selectedYear: new Date().getFullYear(),
      setSelectedYear: (year) => set({ selectedYear: year }),

      currency: 'GBP',
      setCurrency: (currency) => set({ currency }),

      // Date Range
      startDate: null,
      endDate: null,
      setDateRange: (start, end) => set({ startDate: start, endDate: end }),
    }),
    {
      name: 'portfolio-preferences',
      storage: createJSONStorage(() => localStorage),
      // Only persist user preferences, not transient UI state
      partialize: (state) => ({
        currency: state.currency,
        selectedYear: state.selectedYear,
      }),
    }
  )
);
