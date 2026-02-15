'use client';

import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import {
  Building2, DollarSign, TrendingUp, Activity, Percent,
  Wallet, Scale, Droplets, BarChart3, ChevronDown, ChevronUp,
} from 'lucide-react';
import { formatPercentage, formatLargeNumber } from '@/lib/constants';
import { MetricCard } from './MetricCard';
import type { ScreenerAnalysis } from '@/types/screener';

interface CompanyProfileProps {
  analysis: ScreenerAnalysis;
}

export function CompanyProfile({ analysis }: CompanyProfileProps) {
  const [showDetails, setShowDetails] = useState(false);
  const overview = analysis.overview;

  const payoutRatio = overview.payout_ratio ? overview.payout_ratio * 100 : 0;
  const currentRatio = analysis.balance_sheets?.[0]?.current_ratio ?? 0;
  const debtToEquity = analysis.balance_sheets?.[0]?.debt_to_equity ?? 0;

  return (
    <>
      <div>
        <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
          <Building2 className="h-5 w-5 text-primary" />
          Company Profile: {overview.name} ({overview.symbol})
          {overview.sector && (
            <Badge variant="outline" className="ml-2 font-normal">{overview.sector}</Badge>
          )}
        </h2>

        <div className="grid gap-4 grid-cols-2 md:grid-cols-4">
          <MetricCard
            label="Market Cap"
            value={overview.market_cap ? formatLargeNumber(overview.market_cap) : 'N/A'}
            icon={<Wallet className="h-3.5 w-3.5" />}
            status="neutral"
            delay={0}
          />
          <MetricCard
            label="EPS"
            value={overview.eps ? `$${overview.eps.toFixed(2)}` : 'N/A'}
            icon={<DollarSign className="h-3.5 w-3.5" />}
            status={!overview.eps ? 'neutral' : overview.eps > 0 ? 'good' : 'danger'}
            delay={50}
          />
          <MetricCard
            label="Dividend Yield"
            value={overview.dividend_yield ? formatPercentage(overview.dividend_yield * 100) : 'N/A'}
            icon={<Percent className="h-3.5 w-3.5" />}
            status={
              !overview.dividend_yield ? 'neutral' :
              overview.dividend_yield * 100 >= 4 ? 'good' :
              overview.dividend_yield * 100 >= 2 ? 'neutral' : 'warning'
            }
            delay={100}
          />
          <MetricCard
            label="P/E Ratio"
            value={overview.pe_ratio?.toFixed(2) || 'N/A'}
            icon={<Activity className="h-3.5 w-3.5" />}
            status={
              !overview.pe_ratio ? 'neutral' :
              overview.pe_ratio <= 15 ? 'good' :
              overview.pe_ratio <= 25 ? 'neutral' :
              overview.pe_ratio <= 35 ? 'warning' : 'danger'
            }
            delay={150}
          />
          <MetricCard
            label="Payout Ratio"
            value={payoutRatio > 0 ? formatPercentage(payoutRatio) : 'N/A'}
            icon={<TrendingUp className="h-3.5 w-3.5" />}
            status={
              payoutRatio <= 0 ? 'neutral' :
              payoutRatio <= 50 ? 'good' :
              payoutRatio <= 70 ? 'neutral' :
              payoutRatio <= 85 ? 'warning' : 'danger'
            }
            delay={200}
          />
          <MetricCard
            label="ROE"
            value={overview.return_on_equity ? formatPercentage(overview.return_on_equity * 100) : 'N/A'}
            icon={<BarChart3 className="h-3.5 w-3.5" />}
            status={
              !overview.return_on_equity ? 'neutral' :
              overview.return_on_equity * 100 >= 15 ? 'good' :
              overview.return_on_equity * 100 >= 10 ? 'neutral' : 'warning'
            }
            delay={250}
          />
          <MetricCard
            label="Debt/Equity"
            value={debtToEquity > 0 ? debtToEquity.toFixed(2) : 'N/A'}
            icon={<Scale className="h-3.5 w-3.5" />}
            status={
              debtToEquity <= 0 ? 'neutral' :
              debtToEquity <= 0.5 ? 'good' :
              debtToEquity <= 1.0 ? 'neutral' :
              debtToEquity <= 1.5 ? 'warning' : 'danger'
            }
            delay={300}
          />
          <MetricCard
            label="Current Ratio"
            value={currentRatio > 0 ? currentRatio.toFixed(2) : 'N/A'}
            icon={<Droplets className="h-3.5 w-3.5" />}
            status={
              currentRatio <= 0 ? 'neutral' :
              currentRatio >= 1.5 ? 'good' :
              currentRatio >= 1.0 ? 'warning' : 'danger'
            }
            delay={350}
          />
        </div>
      </div>

      {/* Expandable Detailed Company Information */}
      <Card>
        <CardHeader
          className="cursor-pointer hover:bg-muted/50 transition-colors"
          onClick={() => setShowDetails(!showDetails)}
        >
          <div className="flex items-center justify-between">
            <CardTitle className="text-base flex items-center gap-2">
              <BarChart3 className="h-4 w-4" />
              Detailed Company Information
            </CardTitle>
            {showDetails ? <ChevronUp className="h-5 w-5" /> : <ChevronDown className="h-5 w-5" />}
          </div>
        </CardHeader>
        {showDetails && (
          <CardContent>
            <div className="grid md:grid-cols-3 gap-6">
              <div className="space-y-2">
                <p><span className="font-medium">Sector:</span> {overview.sector || 'N/A'}</p>
                <p><span className="font-medium">Industry:</span> {overview.industry || 'N/A'}</p>
                <p><span className="font-medium">Exchange:</span> {overview.exchange || 'N/A'}</p>
                <p><span className="font-medium">Currency:</span> {overview.currency || 'USD'}</p>
              </div>
              <div className="space-y-2">
                <p><span className="font-medium">52 Week High:</span> ${overview.fifty_two_week_high?.toFixed(2) || 'N/A'}</p>
                <p><span className="font-medium">52 Week Low:</span> ${overview.fifty_two_week_low?.toFixed(2) || 'N/A'}</p>
                <p><span className="font-medium">Beta:</span> {overview.beta?.toFixed(2) || 'N/A'}</p>
                <p><span className="font-medium">Book Value:</span> ${overview.book_value?.toFixed(2) || 'N/A'}</p>
              </div>
              <div className="space-y-2">
                <p><span className="font-medium">EV/EBITDA:</span> {overview.ev_to_ebitda?.toFixed(2) || 'N/A'}</p>
                <p><span className="font-medium">P/S Ratio:</span> {overview.price_to_sales_ratio?.toFixed(2) || 'N/A'}</p>
                <p><span className="font-medium">Ex-Dividend Date:</span> {overview.ex_dividend_date || 'N/A'}</p>
                <p><span className="font-medium">Dividend Date:</span> {overview.dividend_date || 'N/A'}</p>
              </div>
            </div>
            {overview.description && (
              <div className="mt-4 pt-4 border-t">
                <p className="font-medium mb-2">Company Description:</p>
                <p className="text-sm text-muted-foreground">
                  {overview.description.length > 500
                    ? overview.description.substring(0, 500) + '...'
                    : overview.description}
                </p>
              </div>
            )}
          </CardContent>
        )}
      </Card>
    </>
  );
}
