'use client';

import { useState, useCallback, Suspense } from 'react';
import { useQuery } from '@tanstack/react-query';
import dynamic from 'next/dynamic';
import { Layout } from '@/components/layout/Layout';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Slider } from '@/components/ui/slider';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { TrendingUp, Calendar, Info, Sparkles, Calculator, Gauge, Settings2, ChartLine } from 'lucide-react';
import { formatCurrency } from '@/lib/constants';
import api from '@/lib/api';
import { cn } from '@/lib/utils';

// Lazy load forecast charts
const PlotlyForecastChart = dynamic(
  () => import('@/components/charts/PlotlyForecast').then(mod => ({ default: mod.PlotlyForecastChart })),
  {
    loading: () => <Skeleton className="h-[500px]" />,
    ssr: false,
  }
);

const PlotlyProjectionBarChart = dynamic(
  () => import('@/components/charts/PlotlyForecast').then(mod => ({ default: mod.PlotlyProjectionBarChart })),
  {
    loading: () => <Skeleton className="h-[400px]" />,
    ssr: false,
  }
);

interface ForecastPoint {
  date: string;
  predicted: number;
  lower_bound?: number;
  upper_bound?: number;
}

interface ForecastResult {
  model_name: string;
  forecast: ForecastPoint[];
  historical: { date: string; value: number }[];
  metrics: Record<string, unknown>;
  total_projected: number;
  monthly_average: number;
  annual_projections: { year: string; projected: number }[];
}

interface CurrentMonthTracking {
  date: string;
  value: number;
  is_partial: boolean;
}

interface ForecastResponse {
  sarimax?: ForecastResult;
  holt_winters?: ForecastResult;
  prophet?: ForecastResult;
  theta?: ForecastResult;
  simple_average?: ForecastResult;
  ensemble?: ForecastResult;
  available_models: string[];
  current_month_tracking?: CurrentMonthTracking;
}

export default function ForecastPage() {
  const [months, setMonths] = useState(12);
  const [lookback, setLookback] = useState(0); // 0 = use all data
  const [chartHistory, setChartHistory] = useState(0); // 0 = show all history
  const [selectedModel, setSelectedModel] = useState('ensemble');

  const { data: forecastData, isLoading } = useQuery<ForecastResponse>({
    queryKey: ['forecast', months, lookback],
    queryFn: () => api.get(`/api/forecast/?months=${months}&lookback=${lookback}`).then(res => res.data),
  });

  const getModelData = useCallback((): ForecastResult | null => {
    if (!forecastData) return null;
    switch (selectedModel) {
      case 'sarimax': return forecastData.sarimax || null;
      case 'holt_winters': return forecastData.holt_winters || null;
      case 'prophet': return forecastData.prophet || null;
      case 'theta': return forecastData.theta || null;
      case 'simple_average': return forecastData.simple_average || null;
      case 'ensemble':
      default: return forecastData.ensemble || null;
    }
  }, [forecastData, selectedModel]);

  const modelData = getModelData();

  // Prepare chart data for ForecastChart component
  const chartData = modelData ? [
    ...modelData.historical.map(h => ({
      date: h.date,
      actual: h.value,
      forecast: undefined as number | undefined,
      lower: undefined as number | undefined,
      upper: undefined as number | undefined,
      tracking: undefined as number | undefined,
    })),
    // Add current month tracking point if available
    ...(forecastData?.current_month_tracking ? [{
      date: forecastData.current_month_tracking.date,
      actual: undefined as number | undefined,
      forecast: undefined as number | undefined,
      lower: undefined as number | undefined,
      upper: undefined as number | undefined,
      tracking: forecastData.current_month_tracking.value,
    }] : []),
    ...modelData.forecast.map(f => ({
      date: f.date,
      actual: undefined as number | undefined,
      forecast: f.predicted,
      lower: f.lower_bound,
      upper: f.upper_bound,
      tracking: undefined as number | undefined,
    })),
  ] : [];

  // Show configurable amount of history + forecast (0 = all data)
  const trimmedChartData = chartHistory === 0
    ? chartData
    : chartData.slice(-chartHistory - months);

  return (
    <Layout>
      <div className="space-y-6">
        {/* Page Header */}
        <div className="animate-enter">
          <div className="flex items-center gap-2 text-xs text-muted-foreground mb-2">
            <span className="w-1.5 h-1.5 rounded-full bg-purple-500" />
            <span>Predictions</span>
          </div>
          <h1 className="text-4xl lg:text-5xl font-serif tracking-tight mb-2">
            Dividend Forecast
          </h1>
          <p className="text-lg text-muted-foreground max-w-2xl">
            Predict future dividend income using multiple forecasting models
          </p>
        </div>

        {/* Settings */}
        <div className="grid gap-4 md:grid-cols-2 animate-enter" style={{ animationDelay: '75ms' }}>
          <Card className="overflow-hidden">
            <CardHeader>
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center">
                  <Settings2 className="h-5 w-5 text-primary" />
                </div>
                <CardTitle className="text-lg">Forecast Settings</CardTitle>
              </div>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="space-y-2">
                <Label>Forecast Horizon: {months} months</Label>
                <Slider
                  value={[months]}
                  onValueChange={(v) => setMonths(v[0])}
                  min={3}
                  max={36}
                  step={1}
                  className="w-full"
                />
                <p className="text-xs text-muted-foreground">
                  How far ahead to forecast
                </p>
              </div>
              <div className="space-y-2">
                <Label>Lookback Period: {lookback === 0 ? 'All Data' : `${lookback} months`}</Label>
                <Slider
                  value={[lookback]}
                  onValueChange={(v) => setLookback(v[0])}
                  min={0}
                  max={60}
                  step={6}
                  className="w-full"
                />
                <p className="text-xs text-muted-foreground">
                  {lookback === 0 ? 'Using all available historical data for training' : `Using last ${lookback} months for model training`}
                </p>
              </div>
              <div className="space-y-2">
                <Label>Chart History: {chartHistory === 0 ? 'All Data' : `${chartHistory} months`}</Label>
                <Slider
                  value={[chartHistory]}
                  onValueChange={(v) => setChartHistory(v[0])}
                  min={0}
                  max={60}
                  step={6}
                  className="w-full"
                />
                <p className="text-xs text-muted-foreground">
                  {chartHistory === 0 ? 'Showing all historical data on chart' : `Showing last ${chartHistory} months on chart`}
                </p>
              </div>
            </CardContent>
          </Card>

          {/* Model Requirements Info */}
          <Card className="border-dashed">
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2">
                <Info className="h-4 w-4" />
                Model Requirements
              </CardTitle>
            </CardHeader>
            <CardContent className="text-sm text-muted-foreground space-y-2">
              <div className="flex justify-between">
                <span><strong>SARIMAX:</strong></span>
                <Badge variant={forecastData?.sarimax ? "default" : "secondary"}>12+ months</Badge>
              </div>
              <div className="flex justify-between">
                <span><strong>Holt-Winters:</strong></span>
                <Badge variant={forecastData?.holt_winters ? "default" : "secondary"}>24+ months</Badge>
              </div>
              <div className="flex justify-between">
                <span><strong>Prophet:</strong></span>
                <Badge variant={forecastData?.prophet ? "default" : "secondary"}>12+ months</Badge>
              </div>
              <div className="flex justify-between">
                <span><strong>Theta:</strong></span>
                <Badge variant={forecastData?.theta ? "default" : "secondary"}>6+ months</Badge>
              </div>
              <div className="flex justify-between">
                <span><strong>Simple Avg:</strong></span>
                <Badge variant="default">Always available</Badge>
              </div>
              <p className="text-xs pt-2 border-t">
                Models may require additional Python packages (prophet, sktime) to be installed.
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Model Tabs */}
        <Tabs value={selectedModel} onValueChange={setSelectedModel}>
          <TabsList className="grid w-full grid-cols-6 max-w-4xl">
            <TabsTrigger value="ensemble">Ensemble</TabsTrigger>
            <TabsTrigger value="sarimax" disabled={!forecastData?.sarimax}>SARIMAX</TabsTrigger>
            <TabsTrigger value="holt_winters" disabled={!forecastData?.holt_winters}>Holt-Winters</TabsTrigger>
            <TabsTrigger value="prophet" disabled={!forecastData?.prophet}>Prophet</TabsTrigger>
            <TabsTrigger value="theta" disabled={!forecastData?.theta}>Theta</TabsTrigger>
            <TabsTrigger value="simple_average">Simple Avg</TabsTrigger>
          </TabsList>

          <TabsContent value={selectedModel} className="space-y-6 mt-6">
            {isLoading ? (
              <div className="space-y-4">
                <Skeleton className="h-[400px] w-full" />
                <div className="grid grid-cols-3 gap-4">
                  <Skeleton className="h-24" />
                  <Skeleton className="h-24" />
                  <Skeleton className="h-24" />
                </div>
              </div>
            ) : modelData ? (
              <>
                {/* Summary Cards */}
                <div className="grid gap-4 md:grid-cols-3">
                  <Card className="border-l-4 border-l-purple-500 bg-purple-500/5 hover:scale-[1.02] transition-transform">
                    <CardHeader className="pb-2">
                      <div className="flex items-center gap-2 mb-1">
                        <Sparkles className="h-4 w-4 text-purple-400" />
                        <CardDescription>Total Projected ({months}mo)</CardDescription>
                      </div>
                      <CardTitle className="text-3xl number-display value-positive">
                        {formatCurrency(modelData.total_projected)}
                      </CardTitle>
                    </CardHeader>
                  </Card>
                  <Card className="border-l-4 border-l-blue-500 bg-blue-500/5 hover:scale-[1.02] transition-transform">
                    <CardHeader className="pb-2">
                      <div className="flex items-center gap-2 mb-1">
                        <Calculator className="h-4 w-4 text-blue-400" />
                        <CardDescription>Monthly Average</CardDescription>
                      </div>
                      <CardTitle className="text-3xl number-display">
                        {formatCurrency(modelData.monthly_average)}
                      </CardTitle>
                    </CardHeader>
                  </Card>
                  <Card className="border-l-4 border-l-emerald-500 bg-emerald-500/5 hover:scale-[1.02] transition-transform">
                    <CardHeader className="pb-2">
                      <div className="flex items-center gap-2 mb-1">
                        <Gauge className="h-4 w-4 text-emerald-400" />
                        <CardDescription>Active Model</CardDescription>
                      </div>
                      <CardTitle className="text-2xl flex items-center gap-2">
                        {modelData.model_name}
                        <Badge className="bg-emerald-500/20 text-emerald-400 border-emerald-500/30">Active</Badge>
                      </CardTitle>
                    </CardHeader>
                  </Card>
                </div>

                {/* Forecast Chart */}
                <Card className="overflow-hidden">
                  <CardHeader>
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-xl bg-purple-500/10 flex items-center justify-center">
                        <ChartLine className="h-5 w-5 text-purple-400" />
                      </div>
                      <div>
                        <CardTitle className="text-lg">{modelData.model_name} Forecast</CardTitle>
                        <CardDescription>
                          Historical data with {months}-month forecast
                          {modelData.forecast[0]?.lower_bound !== null && ' and 95% confidence interval'}
                        </CardDescription>
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="chart-reveal">
                      <PlotlyForecastChart
                        data={trimmedChartData}
                        height={400}
                        currency="£"
                      />
                    </div>
                  </CardContent>
                </Card>

                {/* Annual Projections */}
                {modelData.annual_projections.length > 0 && (
                  <Card>
                    <CardHeader>
                      <CardTitle className="flex items-center gap-2">
                        <Calendar className="h-5 w-5" />
                        Annual Projections
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <PlotlyProjectionBarChart
                        data={modelData.annual_projections}
                        height={250}
                        currency="£"
                      />
                    </CardContent>
                  </Card>
                )}
              </>
            ) : (
              <Card>
                <CardContent className="py-8 text-center text-muted-foreground">
                  No forecast data available for this model
                </CardContent>
              </Card>
            )}
          </TabsContent>
        </Tabs>
      </div>
    </Layout>
  );
}
