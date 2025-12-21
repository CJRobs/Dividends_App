'use client';

/**
 * Sidebar navigation component - Wealth Observatory Design
 * Elegant, dark sidebar with refined navigation and visual polish
 */

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  BarChart3,
  Calendar,
  Building2,
  Search,
  TrendingUp,
  FileText,
  Menu,
  X,
  Sparkles,
  ChevronRight
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { usePortfolioStore } from '@/store/portfolioStore';

const navigation = [
  { name: 'Overview', href: '/', icon: BarChart3, description: 'Portfolio summary' },
  { name: 'Monthly', href: '/monthly', icon: Calendar, description: 'Monthly breakdown' },
  { name: 'Stocks', href: '/stocks', icon: Building2, description: 'Stock analysis' },
  { name: 'Screener', href: '/screener', icon: Search, description: 'Research stocks' },
  { name: 'Forecast', href: '/forecast', icon: TrendingUp, description: 'Future projections' },
  { name: 'Reports', href: '/reports', icon: FileText, description: 'Generate PDFs' },
];

export function Sidebar() {
  const pathname = usePathname();
  const { sidebarOpen, toggleSidebar } = usePortfolioStore();

  return (
    <>
      {/* Mobile menu button */}
      <div className="lg:hidden fixed top-4 left-4 z-50">
        <Button
          variant="outline"
          size="icon"
          onClick={toggleSidebar}
          className="bg-card/80 backdrop-blur-md border-border/50 shadow-lg"
        >
          {sidebarOpen ? (
            <X className="h-4 w-4" />
          ) : (
            <Menu className="h-4 w-4" />
          )}
        </Button>
      </div>

      {/* Sidebar */}
      <aside
        className={cn(
          'fixed inset-y-0 left-0 z-40 w-72 transition-all duration-500 ease-out lg:translate-x-0',
          'bg-gradient-to-b from-sidebar via-sidebar to-sidebar/95',
          'border-r border-sidebar-border/50',
          sidebarOpen ? 'translate-x-0' : '-translate-x-full'
        )}
      >
        {/* Decorative gradient orb */}
        <div className="absolute top-0 right-0 w-32 h-32 bg-sidebar-primary/10 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute bottom-20 left-0 w-24 h-24 bg-sidebar-primary/5 rounded-full blur-2xl pointer-events-none" />

        <div className="relative flex flex-col h-full">
          {/* Logo/Brand Header */}
          <div className="flex items-center gap-3 h-20 px-6 border-b border-sidebar-border/30">
            <div className="relative">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-sidebar-primary to-emerald-400 flex items-center justify-center shadow-lg shadow-sidebar-primary/25">
                <Sparkles className="h-5 w-5 text-sidebar-primary-foreground" />
              </div>
              {/* Pulse ring */}
              <div className="absolute inset-0 rounded-xl bg-sidebar-primary/20 animate-ping" style={{ animationDuration: '3s' }} />
            </div>
            <div>
              <h1 className="text-lg font-semibold text-sidebar-foreground tracking-tight">
                Dividend
              </h1>
              <p className="text-xs text-sidebar-foreground/50 -mt-0.5">
                Portfolio Tracker
              </p>
            </div>
          </div>

          {/* Navigation */}
          <nav className="flex-1 px-4 py-6 space-y-1.5 overflow-y-auto">
            <div className="text-[10px] font-medium text-sidebar-foreground/40 uppercase tracking-wider px-3 mb-3">
              Navigation
            </div>

            {navigation.map((item, index) => {
              const isActive = pathname === item.href;
              const Icon = item.icon;

              return (
                <Link
                  key={item.name}
                  href={item.href}
                  className={cn(
                    'group relative flex items-center gap-3 px-3 py-2.5 rounded-xl transition-all duration-300',
                    'hover:bg-sidebar-accent/50',
                    isActive && 'bg-sidebar-accent'
                  )}
                  onClick={() => {
                    if (window.innerWidth < 1024) {
                      toggleSidebar();
                    }
                  }}
                  style={{ animationDelay: `${index * 50}ms` }}
                >
                  {/* Active indicator */}
                  <div
                    className={cn(
                      'absolute left-0 top-1/2 -translate-y-1/2 w-1 rounded-full transition-all duration-300',
                      isActive ? 'h-8 bg-sidebar-primary' : 'h-0 bg-transparent group-hover:h-4 group-hover:bg-sidebar-primary/50'
                    )}
                  />

                  {/* Icon container */}
                  <div
                    className={cn(
                      'w-9 h-9 rounded-lg flex items-center justify-center transition-all duration-300',
                      isActive
                        ? 'bg-sidebar-primary text-sidebar-primary-foreground shadow-lg shadow-sidebar-primary/30'
                        : 'bg-sidebar-accent/30 text-sidebar-foreground/60 group-hover:bg-sidebar-accent group-hover:text-sidebar-foreground group-hover:scale-110'
                    )}
                  >
                    <Icon className={cn(
                      'h-4 w-4 transition-transform duration-300',
                      'group-hover:scale-110'
                    )} />
                  </div>

                  {/* Label */}
                  <div className="flex-1 min-w-0">
                    <span
                      className={cn(
                        'block text-sm font-medium transition-colors duration-300',
                        isActive ? 'text-sidebar-foreground' : 'text-sidebar-foreground/70 group-hover:text-sidebar-foreground'
                      )}
                    >
                      {item.name}
                    </span>
                    <span
                      className={cn(
                        'block text-[10px] transition-colors duration-300 truncate',
                        isActive ? 'text-sidebar-foreground/50' : 'text-sidebar-foreground/30 group-hover:text-sidebar-foreground/50'
                      )}
                    >
                      {item.description}
                    </span>
                  </div>

                  {/* Arrow indicator */}
                  <ChevronRight
                    className={cn(
                      'h-4 w-4 transition-all duration-300',
                      isActive
                        ? 'text-sidebar-primary opacity-100 translate-x-0'
                        : 'text-sidebar-foreground/30 opacity-0 -translate-x-2 group-hover:opacity-100 group-hover:translate-x-0'
                    )}
                  />
                </Link>
              );
            })}
          </nav>
        </div>
      </aside>

      {/* Overlay for mobile */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black/60 backdrop-blur-sm z-30 lg:hidden transition-opacity duration-300"
          onClick={toggleSidebar}
        />
      )}
    </>
  );
}
