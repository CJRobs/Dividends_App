'use client';

import { useState, useCallback } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Layout } from '@/components/layout/Layout';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Slider } from '@/components/ui/slider';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { TrendingUp, Calendar, Info } from 'lucide-react';
import { PlotlyForecastChart, PlotlyProjectionBarChart } from '@/components/charts/PlotlyForecast';
import { formatCurrency } from '@/lib/constants';
import api from '@/lib/api';

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
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Dividend Forecast</h1>
          <p className="text-muted-foreground">
            Predict future dividend income using multiple forecasting models
          </p>
        </div>

        {/* Settings */}
        <div className="grid gap-4 md:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Forecast Settings</CardTitle>
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
                  <Card>
                    <CardHeader className="pb-2">
                      <CardDescription>Total Projected ({months}mo)</CardDescription>
                      <CardTitle className="text-2xl">
                        {formatCurrency(modelData.total_projected)}
                      </CardTitle>
                    </CardHeader>
                  </Card>
                  <Card>
                    <CardHeader className="pb-2">
                      <CardDescription>Monthly Average</CardDescription>
                      <CardTitle className="text-2xl">
                        {formatCurrency(modelData.monthly_average)}
                      </CardTitle>
                    </CardHeader>
                  </Card>
                  <Card>
                    <CardHeader className="pb-2">
                      <CardDescription>Model</CardDescription>
                      <CardTitle className="text-2xl flex items-center gap-2">
                        {modelData.model_name}
                        <Badge variant="secondary">Active</Badge>
                      </CardTitle>
                    </CardHeader>
                  </Card>
                </div>

                {/* Forecast Chart */}
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <TrendingUp className="h-5 w-5" />
                      {modelData.model_name} Forecast
                    </CardTitle>
                    <CardDescription>
                      Historical data with {months}-month forecast
                      {modelData.forecast[0]?.lower_bound !== null && ' and 95% confidence interval'}
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <PlotlyForecastChart
                      data={trimmedChartData}
                      height={400}
                      currency="£"
                    />
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
