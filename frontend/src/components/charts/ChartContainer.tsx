'use client';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { ReactNode } from 'react';

interface ChartContainerProps {
  title?: string;
  description?: string;
  children: ReactNode;
  isLoading?: boolean;
  error?: Error | null;
  className?: string;
  height?: number;
  action?: ReactNode;
}

export function ChartContainer({
  title,
  description,
  children,
  isLoading = false,
  error = null,
  className = '',
  height = 350,
  action,
}: ChartContainerProps) {
  // If no title, render without Card wrapper for inline usage
  if (!title) {
    return (
      <div style={{ height }}>
        {isLoading ? (
          <div className="flex items-center justify-center h-full">
            <Skeleton className="h-full w-full" />
          </div>
        ) : error ? (
          <div className="flex items-center justify-center text-destructive h-full">
            <p>Failed to load chart data</p>
          </div>
        ) : (
          children
        )}
      </div>
    );
  }

  return (
    <Card className={className}>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <div>
          <CardTitle className="text-base font-semibold">{title}</CardTitle>
          {description && (
            <CardDescription className="text-sm">{description}</CardDescription>
          )}
        </div>
        {action && <div>{action}</div>}
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="flex items-center justify-center" style={{ height }}>
            <div className="space-y-3 w-full">
              <Skeleton className="h-4 w-3/4" />
              <Skeleton className="h-[200px] w-full" />
              <Skeleton className="h-4 w-1/2" />
            </div>
          </div>
        ) : error ? (
          <div
            className="flex items-center justify-center text-destructive"
            style={{ height }}
          >
            <p>Failed to load chart data</p>
          </div>
        ) : (
          <div style={{ height }}>{children}</div>
        )}
      </CardContent>
    </Card>
  );
}
