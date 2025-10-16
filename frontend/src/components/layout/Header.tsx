'use client';

/**
 * Header component for the dashboard.
 */

import { Bell, Settings } from 'lucide-react';
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

export function Header() {
  const { currency, setCurrency } = usePortfolioStore();

  return (
    <header className="sticky top-0 z-10 h-16 bg-background border-b border-border">
      <div className="flex items-center justify-between h-full px-6">
        <div>
          {/* This space can be used for page titles or breadcrumbs */}
        </div>

        <div className="flex items-center gap-4">
          {/* Currency Selector */}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="outline" size="sm">
                {currency}
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuLabel>Currency</DropdownMenuLabel>
              <DropdownMenuSeparator />
              <DropdownMenuItem onClick={() => setCurrency('GBP')}>
                GBP (£)
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => setCurrency('USD')}>
                USD ($)
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => setCurrency('EUR')}>
                EUR (€)
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>

          {/* Notifications */}
          <Button variant="ghost" size="icon">
            <Bell className="h-5 w-5" />
          </Button>

          {/* Settings */}
          <Button variant="ghost" size="icon">
            <Settings className="h-5 w-5" />
          </Button>
        </div>
      </div>
    </header>
  );
}
