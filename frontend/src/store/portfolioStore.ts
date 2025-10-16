/**
 * Zustand store for portfolio state management.
 */

import { create } from 'zustand';

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

export const usePortfolioStore = create<PortfolioStore>((set) => ({
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
}));
