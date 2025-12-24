'use client';

import { ReactNode, forwardRef } from 'react';
import { LucideIcon, RefreshCw, AlertCircle } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';

// =============================================================================
// TYPES
// =============================================================================

export type ChartContainerVariant = 'default' | 'glass' | 'gradient' | 'minimal';
export type SkeletonType = 'line' | 'bar' | 'pie' | 'default';

interface PremiumChartContainerProps {
  /** Chart content */
  children: ReactNode;
  /** Chart title */
  title?: string;
  /** Chart subtitle/description */
  subtitle?: string;
  /** Icon component from lucide-react */
  icon?: LucideIcon;
  /** Height of the chart area */
  height?: number | string;
  /** Container variant styling */
  variant?: ChartContainerVariant;
  /** Loading state */
  isLoading?: boolean;
  /** Skeleton type for loading state */
  skeletonType?: SkeletonType;
  /** Error state */
  error?: Error | string | null;
  /** Callback for retry button */
  onRetry?: () => void;
  /** Show refresh button */
  showRefresh?: boolean;
  /** Callback for refresh button */
  onRefresh?: () => void;
  /** Is refreshing */
  isRefreshing?: boolean;
  /** Custom toolbar content */
  toolbar?: ReactNode;
  /** Additional class names */
  className?: string;
  /** Delay for staggered animation (1-4) */
  animationDelay?: 1 | 2 | 3 | 4;
  /** Disable entrance animation */
  noAnimation?: boolean;
}

// =============================================================================
// SKELETON COMPONENTS
// =============================================================================

function LineSkeleton({ height }: { height: number | string }) {
  return (
    <div
      className="chart-skeleton chart-skeleton-line"
      style={{ height: typeof height === 'number' ? `${height}px` : height }}
    />
  );
}

function BarSkeleton({ height }: { height: number | string }) {
  return (
    <div
      className="chart-skeleton chart-skeleton-bar"
      style={{ height: typeof height === 'number' ? `${height}px` : height }}
    >
      <div className="chart-skeleton-bar-item" />
      <div className="chart-skeleton-bar-item" />
      <div className="chart-skeleton-bar-item" />
      <div className="chart-skeleton-bar-item" />
      <div className="chart-skeleton-bar-item" />
    </div>
  );
}

function PieSkeleton({ height }: { height: number | string }) {
  return (
    <div
      className="chart-skeleton chart-skeleton-pie"
      style={{ height: typeof height === 'number' ? `${height}px` : height }}
    />
  );
}

function DefaultSkeleton({ height }: { height: number | string }) {
  return (
    <div
      className="chart-skeleton"
      style={{ height: typeof height === 'number' ? `${height}px` : height }}
    />
  );
}

function ChartSkeleton({ type, height }: { type: SkeletonType; height: number | string }) {
  switch (type) {
    case 'line':
      return <LineSkeleton height={height} />;
    case 'bar':
      return <BarSkeleton height={height} />;
    case 'pie':
      return <PieSkeleton height={height} />;
    default:
      return <DefaultSkeleton height={height} />;
  }
}

// =============================================================================
// ERROR STATE
// =============================================================================

function ChartError({
  error,
  onRetry,
  height,
}: {
  error: Error | string;
  onRetry?: () => void;
  height: number | string;
}) {
  const errorMessage = typeof error === 'string' ? error : error.message;

  return (
    <div
      className="flex flex-col items-center justify-center gap-4 text-center p-6"
      style={{ height: typeof height === 'number' ? `${height}px` : height }}
    >
      <div className="w-12 h-12 rounded-full bg-destructive/10 flex items-center justify-center">
        <AlertCircle className="w-6 h-6 text-destructive" />
      </div>
      <div className="space-y-1">
        <p className="text-sm font-medium text-foreground">Failed to load chart</p>
        <p className="text-xs text-muted-foreground max-w-[200px]">{errorMessage}</p>
      </div>
      {onRetry && (
        <Button variant="outline" size="sm" onClick={onRetry} className="mt-2">
          <RefreshCw className="w-3.5 h-3.5 mr-1.5" />
          Try again
        </Button>
      )}
    </div>
  );
}

// =============================================================================
// MAIN COMPONENT
// =============================================================================

export const PremiumChartContainer = forwardRef<HTMLDivElement, PremiumChartContainerProps>(
  (
    {
      children,
      title,
      subtitle,
      icon: Icon,
      height = 400,
      variant = 'default',
      isLoading = false,
      skeletonType = 'default',
      error = null,
      onRetry,
      showRefresh = false,
      onRefresh,
      isRefreshing = false,
      toolbar,
      className,
      animationDelay,
      noAnimation = false,
    },
    ref
  ) => {
    // Variant class mapping
    const variantClasses: Record<ChartContainerVariant, string> = {
      default: 'bg-card border border-border rounded-xl',
      glass: 'chart-glass',
      gradient: 'chart-gradient-border',
      minimal: 'chart-minimal',
    };

    // Animation classes
    const animationClasses = noAnimation
      ? ''
      : `chart-animate-in${animationDelay ? ` chart-delay-${animationDelay}` : ''}`;

    const hasHeader = title || subtitle || Icon || showRefresh || toolbar;

    return (
      <div
        ref={ref}
        className={cn(
          'relative overflow-hidden',
          variantClasses[variant],
          animationClasses,
          className
        )}
      >
        {/* Inner padding container */}
        <div className="p-5 sm:p-6">
          {/* Header */}
          {hasHeader && (
            <div className="chart-header">
              <div className="flex items-start gap-3">
                {Icon && (
                  <div className="chart-icon">
                    <Icon className="w-5 h-5" />
                  </div>
                )}
                <div className="chart-header-content">
                  {title && <h3 className="chart-title">{title}</h3>}
                  {subtitle && <p className="chart-subtitle">{subtitle}</p>}
                </div>
              </div>
              <div className="chart-actions">
                {toolbar}
                {showRefresh && onRefresh && (
                  <button
                    onClick={onRefresh}
                    disabled={isRefreshing}
                    className="chart-action-btn"
                    title="Refresh data"
                  >
                    <RefreshCw
                      className={cn('w-4 h-4', isRefreshing && 'animate-spin')}
                    />
                  </button>
                )}
              </div>
            </div>
          )}

          {/* Content area */}
          <div className="relative">
            {/* Loading state */}
            {isLoading && (
              <ChartSkeleton type={skeletonType} height={height} />
            )}

            {/* Error state */}
            {!isLoading && error && (
              <ChartError error={error} onRetry={onRetry} height={height} />
            )}

            {/* Chart content */}
            {!isLoading && !error && (
              <div className="chart-fade-in">{children}</div>
            )}
          </div>
        </div>
      </div>
    );
  }
);

PremiumChartContainer.displayName = 'PremiumChartContainer';

// =============================================================================
// SIMPLE WRAPPER (for backward compatibility)
// =============================================================================

interface SimpleChartWrapperProps {
  children: ReactNode;
  className?: string;
  variant?: ChartContainerVariant;
  animationDelay?: 1 | 2 | 3 | 4;
}

export function ChartWrapper({
  children,
  className,
  variant = 'default',
  animationDelay,
}: SimpleChartWrapperProps) {
  const variantClasses: Record<ChartContainerVariant, string> = {
    default: 'bg-card border border-border rounded-xl',
    glass: 'chart-glass',
    gradient: 'chart-gradient-border',
    minimal: 'chart-minimal',
  };

  const animationClasses = `chart-animate-in${animationDelay ? ` chart-delay-${animationDelay}` : ''}`;

  return (
    <div
      className={cn(
        'relative overflow-hidden p-5 sm:p-6',
        variantClasses[variant],
        animationClasses,
        className
      )}
    >
      {children}
    </div>
  );
}

export default PremiumChartContainer;
