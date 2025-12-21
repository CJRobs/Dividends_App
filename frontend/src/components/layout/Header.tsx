'use client';

/**
 * Header component - Wealth Observatory Design
 * Refined top bar with currency selector, theme toggle, and elegant styling
 */

import { useState, useEffect } from 'react';
import { Bell, Settings, Moon, Sun, ChevronDown, Wallet } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { usePortfolioStore } from '@/store/portfolioStore';
import { cn } from '@/lib/utils';

const currencies = [
  { code: 'GBP', symbol: '£', name: 'British Pound' },
  { code: 'USD', symbol: '$', name: 'US Dollar' },
  { code: 'EUR', symbol: '€', name: 'Euro' },
] as const;

export function Header() {
  const { currency, setCurrency } = usePortfolioStore();
  const [isDark, setIsDark] = useState(true);
  const [mounted, setMounted] = useState(false);

  // Handle theme toggle
  useEffect(() => {
    setMounted(true);
    // Check initial theme
    const isDarkMode = document.documentElement.classList.contains('dark');
    setIsDark(isDarkMode);
  }, []);

  const toggleTheme = () => {
    const newIsDark = !isDark;
    setIsDark(newIsDark);
    document.documentElement.classList.toggle('dark', newIsDark);
    localStorage.setItem('theme', newIsDark ? 'dark' : 'light');
  };

  // Initialize theme from localStorage
  useEffect(() => {
    const savedTheme = localStorage.getItem('theme');
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    const shouldBeDark = savedTheme === 'dark' || (!savedTheme && prefersDark);

    setIsDark(shouldBeDark);
    document.documentElement.classList.toggle('dark', shouldBeDark);
  }, []);

  const currentCurrency = currencies.find(c => c.code === currency) || currencies[0];

  return (
    <header className="sticky top-0 z-10 h-16 bg-background/80 backdrop-blur-xl border-b border-border/50">
      {/* Subtle gradient line at top */}
      <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-primary/20 to-transparent" />
      {/* Bottom gradient accent */}
      <div className="absolute bottom-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-primary/10 to-transparent" />

      <div className="flex items-center justify-end h-full px-6">

        {/* Right side - Actions */}
        <div className="flex items-center gap-2">
          {/* Currency Selector */}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button
                variant="ghost"
                size="sm"
                className="h-9 px-3 gap-2 bg-muted/30 hover:bg-muted/50 border border-transparent hover:border-border/50 transition-all duration-200"
              >
                <Wallet className="h-3.5 w-3.5 text-muted-foreground" />
                <span className="font-medium">{currentCurrency.symbol}</span>
                <span className="text-muted-foreground text-xs hidden sm:inline">{currency}</span>
                <ChevronDown className="h-3 w-3 text-muted-foreground" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-48">
              <DropdownMenuLabel className="text-xs text-muted-foreground font-normal">
                Select Currency
              </DropdownMenuLabel>
              <DropdownMenuSeparator />
              {currencies.map((curr) => (
                <DropdownMenuItem
                  key={curr.code}
                  onClick={() => setCurrency(curr.code)}
                  className={cn(
                    'flex items-center gap-3 cursor-pointer',
                    currency === curr.code && 'bg-muted'
                  )}
                >
                  <div className="w-8 h-8 rounded-lg bg-muted flex items-center justify-center text-sm font-semibold">
                    {curr.symbol}
                  </div>
                  <div className="flex-1">
                    <p className="text-sm font-medium">{curr.code}</p>
                    <p className="text-xs text-muted-foreground">{curr.name}</p>
                  </div>
                  {currency === curr.code && (
                    <div className="w-1.5 h-1.5 rounded-full bg-primary" />
                  )}
                </DropdownMenuItem>
              ))}
            </DropdownMenuContent>
          </DropdownMenu>

          {/* Divider */}
          <div className="hidden sm:block w-px h-6 bg-border/50" />

          {/* Theme Toggle */}
          {mounted && (
            <Button
              variant="ghost"
              size="icon"
              onClick={toggleTheme}
              className="h-9 w-9 hover:bg-muted/50 transition-all duration-200"
            >
              <div className="relative w-4 h-4">
                <Sun
                  className={cn(
                    "h-4 w-4 absolute inset-0 transition-all duration-300",
                    isDark ? "rotate-90 scale-0 opacity-0" : "rotate-0 scale-100 opacity-100"
                  )}
                />
                <Moon
                  className={cn(
                    "h-4 w-4 absolute inset-0 transition-all duration-300",
                    isDark ? "rotate-0 scale-100 opacity-100" : "-rotate-90 scale-0 opacity-0"
                  )}
                />
              </div>
              <span className="sr-only">Toggle theme</span>
            </Button>
          )}

          {/* Notifications */}
          <Button
            variant="ghost"
            size="icon"
            className="h-9 w-9 hover:bg-muted/50 transition-all duration-200 relative group"
          >
            <Bell className="h-4 w-4 transition-transform duration-200 group-hover:scale-110" />
            {/* Notification dot */}
            <span className="absolute top-2 right-2 w-1.5 h-1.5 rounded-full bg-amber-500 animate-pulse" />
            <span className="sr-only">Notifications</span>
          </Button>

          {/* Settings */}
          <Button
            variant="ghost"
            size="icon"
            className="h-9 w-9 hover:bg-muted/50 transition-all duration-200 group"
          >
            <Settings className="h-4 w-4 transition-transform duration-300 group-hover:rotate-90" />
            <span className="sr-only">Settings</span>
          </Button>
        </div>
      </div>
    </header>
  );
}
