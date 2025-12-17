'use client';

/**
 * Main layout wrapper component - Wealth Observatory Design
 * Provides the app shell with sidebar and header
 */

import { ReactNode } from 'react';
import { Sidebar } from './Sidebar';
import { Header } from './Header';

interface LayoutProps {
  children: ReactNode;
}

export function Layout({ children }: LayoutProps) {
  return (
    <div className="flex h-screen overflow-hidden bg-background">
      {/* Subtle background gradient */}
      <div className="fixed inset-0 gradient-mesh pointer-events-none" />

      {/* Noise texture overlay */}
      <div className="grain-overlay" />

      <Sidebar />

      <div className="relative flex-1 flex flex-col lg:ml-72">
        <Header />

        <main className="relative flex-1 overflow-y-auto">
          {/* Main content area with padding */}
          <div className="p-6 lg:p-8 max-w-[1600px] mx-auto">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}
