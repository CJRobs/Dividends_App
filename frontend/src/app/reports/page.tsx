'use client';

import { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { Layout } from '@/components/layout/Layout';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  FileText,
  Download,
  Calendar,
  DollarSign,
  BarChart3,
  Loader2,
} from 'lucide-react';
import { formatCurrency } from '@/lib/constants';
import api from '@/lib/api';

interface PeriodInfo {
  label: string;
  year: number;
  month?: number;
  quarter?: number;
}

interface AvailablePeriodsResponse {
  monthly: PeriodInfo[];
  quarterly: PeriodInfo[];
  yearly: PeriodInfo[];
}

interface ReportPreview {
  period_type: string;
  period_label: string;
  total_dividends: number;
  dividend_count: number;
  unique_stocks: number;
  top_stocks: Array<{
    ticker: string;
    name: string;
    total: number;
  }>;
  monthly_breakdown?: Array<{
    month: string;
    total: number;
  }>;
}

export default function ReportsPage() {
  const [reportType, setReportType] = useState<'Monthly' | 'Quarterly' | 'Yearly'>('Monthly');
  const [selectedPeriod, setSelectedPeriod] = useState<PeriodInfo | null>(null);

  // Fetch available periods
  const { data: periods, isLoading: periodsLoading } = useQuery<AvailablePeriodsResponse>({
    queryKey: ['report-periods'],
    queryFn: () => api.get('/api/reports/periods').then(res => res.data),
  });

  // Get preview when period is selected
  const { data: preview, isLoading: previewLoading } = useQuery<ReportPreview>({
    queryKey: ['report-preview', reportType, selectedPeriod],
    queryFn: () =>
      api.post('/api/reports/preview', {
        period_type: reportType,
        year: selectedPeriod?.year,
        month: selectedPeriod?.month,
        quarter: selectedPeriod?.quarter,
      }).then(res => res.data),
    enabled: !!selectedPeriod,
  });

  // Download report mutation
  const downloadMutation = useMutation({
    mutationFn: async () => {
      if (!selectedPeriod) throw new Error('No period selected');

      const response = await api.post(
        '/api/reports/generate',
        {
          period_type: reportType,
          year: selectedPeriod.year,
          month: selectedPeriod.month,
          quarter: selectedPeriod.quarter,
        },
        {
          responseType: 'blob',
        }
      );

      // Create download link
      const blob = new Blob([response.data], { type: 'application/pdf' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;

      // Generate filename
      let filename = 'dividend_report';
      if (reportType === 'Monthly') {
        filename += `_${selectedPeriod.year}_${String(selectedPeriod.month).padStart(2, '0')}`;
      } else if (reportType === 'Quarterly') {
        filename += `_Q${selectedPeriod.quarter}_${selectedPeriod.year}`;
      } else {
        filename += `_${selectedPeriod.year}`;
      }
      filename += '.pdf';

      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    },
  });

  // Get periods for current report type
  const getCurrentPeriods = (): PeriodInfo[] => {
    if (!periods) return [];
    switch (reportType) {
      case 'Monthly':
        return periods.monthly;
      case 'Quarterly':
        return periods.quarterly;
      case 'Yearly':
        return periods.yearly;
      default:
        return [];
    }
  };

  // Reset selected period when report type changes
  const handleReportTypeChange = (type: 'Monthly' | 'Quarterly' | 'Yearly') => {
    setReportType(type);
    setSelectedPeriod(null);
  };

  return (
    <Layout>
      <div className="space-y-6">
        {/* Page Header */}
        <div>
          <h1 className="text-3xl font-bold tracking-tight">PDF Reports</h1>
          <p className="text-muted-foreground">
            Generate and download professional dividend reports
          </p>
        </div>

        {/* Report Type Selection */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <FileText className="h-5 w-5" />
              Generate Report
            </CardTitle>
            <CardDescription>
              Select a report type and period to generate your dividend report
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Report Type Tabs */}
            <Tabs value={reportType} onValueChange={(v) => handleReportTypeChange(v as typeof reportType)}>
              <TabsList className="grid w-full grid-cols-3 max-w-md">
                <TabsTrigger value="Monthly">Monthly</TabsTrigger>
                <TabsTrigger value="Quarterly">Quarterly</TabsTrigger>
                <TabsTrigger value="Yearly">Yearly</TabsTrigger>
              </TabsList>

              <TabsContent value={reportType} className="mt-4">
                <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-end">
                  {/* Period Selector */}
                  <div className="w-full sm:w-64">
                    <label className="text-sm font-medium mb-2 block">
                      Select Period
                    </label>
                    {periodsLoading ? (
                      <Skeleton className="h-10 w-full" />
                    ) : (
                      <Select
                        value={selectedPeriod?.label || ''}
                        onValueChange={(label) => {
                          const period = getCurrentPeriods().find(p => p.label === label);
                          setSelectedPeriod(period || null);
                        }}
                      >
                        <SelectTrigger>
                          <SelectValue placeholder={`Select ${reportType.toLowerCase()} period`} />
                        </SelectTrigger>
                        <SelectContent>
                          {getCurrentPeriods().map((period) => (
                            <SelectItem key={period.label} value={period.label}>
                              {period.label}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    )}
                  </div>

                  {/* Download Button */}
                  <Button
                    onClick={() => downloadMutation.mutate()}
                    disabled={!selectedPeriod || downloadMutation.isPending}
                    size="lg"
                  >
                    {downloadMutation.isPending ? (
                      <>
                        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                        Generating...
                      </>
                    ) : (
                      <>
                        <Download className="h-4 w-4 mr-2" />
                        Download PDF
                      </>
                    )}
                  </Button>
                </div>
              </TabsContent>
            </Tabs>
          </CardContent>
        </Card>

        {/* Report Preview */}
        {selectedPeriod && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <BarChart3 className="h-5 w-5" />
                Report Preview
                <Badge variant="secondary">{preview?.period_label}</Badge>
              </CardTitle>
              <CardDescription>
                Preview of what will be included in your PDF report
              </CardDescription>
            </CardHeader>
            <CardContent>
              {previewLoading ? (
                <div className="space-y-4">
                  <Skeleton className="h-24 w-full" />
                  <Skeleton className="h-48 w-full" />
                </div>
              ) : preview ? (
                <div className="space-y-6">
                  {/* Summary Stats */}
                  <div className="grid gap-4 md:grid-cols-3">
                    <div className="p-4 bg-muted rounded-lg">
                      <div className="flex items-center gap-2 text-muted-foreground mb-1">
                        <DollarSign className="h-4 w-4" />
                        <span className="text-xs">Total Dividends</span>
                      </div>
                      <p className="text-2xl font-bold">
                        {formatCurrency(preview.total_dividends)}
                      </p>
                    </div>
                    <div className="p-4 bg-muted rounded-lg">
                      <div className="flex items-center gap-2 text-muted-foreground mb-1">
                        <Calendar className="h-4 w-4" />
                        <span className="text-xs">Payments</span>
                      </div>
                      <p className="text-2xl font-bold">{preview.dividend_count}</p>
                    </div>
                    <div className="p-4 bg-muted rounded-lg">
                      <div className="flex items-center gap-2 text-muted-foreground mb-1">
                        <BarChart3 className="h-4 w-4" />
                        <span className="text-xs">Unique Stocks</span>
                      </div>
                      <p className="text-2xl font-bold">{preview.unique_stocks}</p>
                    </div>
                  </div>

                  {/* Top Stocks Table */}
                  <div>
                    <h4 className="text-sm font-medium mb-3">Top Stocks</h4>
                    <div className="border rounded-lg overflow-hidden">
                      <table className="w-full text-sm">
                        <thead className="bg-muted">
                          <tr>
                            <th className="text-left py-2 px-4">Ticker</th>
                            <th className="text-left py-2 px-4">Company</th>
                            <th className="text-right py-2 px-4">Total</th>
                          </tr>
                        </thead>
                        <tbody>
                          {preview.top_stocks.map((stock) => (
                            <tr key={stock.ticker} className="border-t border-muted">
                              <td className="py-2 px-4 font-medium">{stock.ticker}</td>
                              <td className="py-2 px-4 text-muted-foreground truncate max-w-[200px]">
                                {stock.name}
                              </td>
                              <td className="py-2 px-4 text-right font-semibold">
                                {formatCurrency(stock.total)}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>

                  {/* Monthly Breakdown for Quarterly/Yearly */}
                  {preview.monthly_breakdown && preview.monthly_breakdown.length > 0 && (
                    <div>
                      <h4 className="text-sm font-medium mb-3">Monthly Breakdown</h4>
                      <div className="grid gap-2 md:grid-cols-4">
                        {preview.monthly_breakdown.map((month) => (
                          <div key={month.month} className="p-3 bg-muted rounded-lg">
                            <p className="text-xs text-muted-foreground">{month.month}</p>
                            <p className="text-lg font-semibold">
                              {formatCurrency(month.total)}
                            </p>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              ) : (
                <p className="text-muted-foreground text-center py-8">
                  No data available for this period
                </p>
              )}
            </CardContent>
          </Card>
        )}

        {/* Report Types Info */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Report Contents</CardTitle>
            <CardDescription>
              What&apos;s included in each report type
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid gap-4 md:grid-cols-3">
              <div className="p-4 bg-muted rounded-lg space-y-2">
                <h3 className="font-medium flex items-center gap-2">
                  <Calendar className="h-4 w-4" />
                  Monthly Report
                </h3>
                <ul className="text-sm text-muted-foreground space-y-1">
                  <li>- Summary statistics</li>
                  <li>- Top 10 stocks table</li>
                  <li>- All dividend payments</li>
                </ul>
              </div>
              <div className="p-4 bg-muted rounded-lg space-y-2">
                <h3 className="font-medium flex items-center gap-2">
                  <BarChart3 className="h-4 w-4" />
                  Quarterly Report
                </h3>
                <ul className="text-sm text-muted-foreground space-y-1">
                  <li>- Quarterly summary</li>
                  <li>- Monthly breakdown</li>
                  <li>- Top performers</li>
                </ul>
              </div>
              <div className="p-4 bg-muted rounded-lg space-y-2">
                <h3 className="font-medium flex items-center gap-2">
                  <FileText className="h-4 w-4" />
                  Yearly Report
                </h3>
                <ul className="text-sm text-muted-foreground space-y-1">
                  <li>- Annual overview</li>
                  <li>- Monthly trend analysis</li>
                  <li>- Complete stock breakdown</li>
                </ul>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </Layout>
  );
}
