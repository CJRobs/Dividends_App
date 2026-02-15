'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { cn } from '@/lib/utils';

interface MetricCardProps {
  label: string;
  value: string;
  icon: React.ReactNode;
  status?: 'good' | 'warning' | 'danger' | 'neutral';
  delay?: number;
}

const statusColors = {
  good: 'border-l-green-500 bg-green-500/5',
  warning: 'border-l-yellow-500 bg-yellow-500/5',
  danger: 'border-l-red-500 bg-red-500/5',
  neutral: 'border-l-primary/50 bg-primary/5',
};

const valueColors = {
  good: 'text-green-400',
  warning: 'text-yellow-400',
  danger: 'text-red-400',
  neutral: 'text-foreground',
};

export function MetricCard({ label, value, icon, status = 'neutral', delay = 0 }: MetricCardProps) {
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    const timer = setTimeout(() => setIsVisible(true), delay);
    return () => clearTimeout(timer);
  }, [delay]);

  return (
    <Card className={cn(
      'border-l-4 transition-all duration-500 hover:scale-[1.02] hover:shadow-lg',
      statusColors[status],
      isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'
    )}>
      <CardContent className="pt-4 pb-4">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <p className="text-sm text-muted-foreground flex items-center gap-1.5">
              {icon}
              {label}
            </p>
            <p className={cn('text-2xl font-bold mt-1 number-display', valueColors[status])}>
              {value}
            </p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
