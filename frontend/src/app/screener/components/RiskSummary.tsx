'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Shield, Gauge, TrendingUp, AlertTriangle } from 'lucide-react';
import { RiskMeter } from './RiskMeter';
import type { ScreenerAnalysis } from '@/types/screener';

interface RiskSummaryProps {
  analysis: ScreenerAnalysis;
}

export function RiskSummary({ analysis }: RiskSummaryProps) {
  const riskScore = analysis.risk_score ?? 0;
  const riskLevel = analysis.risk_level ?? 'Unknown';
  const riskGrade = analysis.risk_grade ?? 'N/A';
  const riskFactors = analysis.risk_factors;

  // Build risk factor list from backend scores
  const riskItems: string[] = [];
  if (riskFactors) {
    if ((riskFactors.payout_risk ?? 0) > 60) riskItems.push('Elevated payout risk');
    if ((riskFactors.leverage_risk ?? 0) > 60) riskItems.push('High leverage');
    if ((riskFactors.coverage_risk ?? 0) > 60) riskItems.push('Weak cash flow coverage');
    if ((riskFactors.yield_risk ?? 0) > 60) riskItems.push('High yield risk');
    if ((riskFactors.valuation_risk ?? 0) > 60) riskItems.push('Elevated valuation');
    if ((riskFactors.volatility_risk ?? 0) > 60) riskItems.push('High volatility');
  }

  // Build strengths/considerations from analysis data
  const strengths: string[] = [];
  const considerations: string[] = [];

  const dividendYield = (analysis.overview.dividend_yield || 0) * 100;
  const roe = (analysis.overview.return_on_equity || 0) * 100;
  const payoutRatio = (analysis.overview.payout_ratio || 0) * 100;
  const currentRatio = analysis.balance_sheets?.[0]?.current_ratio ?? 0;
  const debtToEquity = analysis.balance_sheets?.[0]?.debt_to_equity ?? 0;

  if (dividendYield >= 4) strengths.push('High dividend yield');
  if (roe >= 15) strengths.push('Strong profitability');
  if (payoutRatio > 0 && payoutRatio <= 60) strengths.push('Conservative payout ratio');
  if (currentRatio >= 1.5) strengths.push('Strong liquidity');

  if (analysis.overview.pe_ratio && analysis.overview.pe_ratio > 25) considerations.push('High valuation');
  if (dividendYield < 2 && dividendYield > 0) considerations.push('Low dividend yield');
  if (debtToEquity > 1) considerations.push('High debt levels');

  // Investment score derived from risk
  const investmentScore = Math.min(100, Math.max(0, Math.round(100 - riskScore)));
  let recommendation = 'Avoid';
  if (investmentScore >= 80) recommendation = 'Strong Buy';
  else if (investmentScore >= 70) recommendation = 'Buy';
  else if (investmentScore >= 60) recommendation = 'Hold';
  else if (investmentScore >= 50) recommendation = 'Weak Hold';

  return (
    <Card className="card-premium">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Shield className="h-5 w-5 text-primary" />
          Risk Assessment & Investment Summary
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-8">
          <div className="grid md:grid-cols-2 gap-8">
            {/* Risk Meter Section */}
            <div className="flex flex-col items-center p-6 rounded-lg bg-card/50 border border-border/50">
              <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <Gauge className="h-5 w-5 text-yellow-500" />
                Risk Assessment
                {riskGrade !== 'N/A' && (
                  <Badge variant="outline" className="ml-2">Grade: {riskGrade}</Badge>
                )}
              </h3>
              <RiskMeter score={riskScore} level={riskLevel} />

              <div className="mt-6 w-full">
                {riskItems.length > 0 ? (
                  <div className="space-y-2">
                    <p className="text-sm font-medium text-muted-foreground text-center mb-3">Risk Factors:</p>
                    {riskItems.map((factor, i) => (
                      <div
                        key={i}
                        className="flex items-center gap-2 text-sm px-3 py-2 rounded-md bg-red-500/10 border border-red-500/20"
                      >
                        <AlertTriangle className="h-3.5 w-3.5 text-red-400 flex-shrink-0" />
                        <span className="text-red-300">{factor}</span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="flex items-center justify-center gap-2 text-sm px-3 py-2 rounded-md bg-green-500/10 border border-green-500/20">
                    <Shield className="h-4 w-4 text-green-400" />
                    <span className="text-green-400">No significant risk factors</span>
                  </div>
                )}
              </div>
            </div>

            {/* Investment Score Section */}
            <div className="flex flex-col items-center p-6 rounded-lg bg-card/50 border border-border/50">
              <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <TrendingUp className="h-5 w-5 text-green-500" />
                Investment Summary
              </h3>

              <div className="flex flex-col items-center mb-4">
                <div className="relative">
                  <svg className="w-32 h-32" viewBox="0 0 100 100">
                    <circle cx="50" cy="50" r="40" fill="none" stroke="currentColor" strokeWidth="8" opacity="0.1" />
                    <circle
                      cx="50" cy="50" r="40" fill="none"
                      stroke={investmentScore >= 70 ? '#22c55e' : investmentScore >= 50 ? '#eab308' : '#ef4444'}
                      strokeWidth="8" strokeLinecap="round"
                      strokeDasharray={`${investmentScore * 2.51} 251`}
                      transform="rotate(-90 50 50)"
                      style={{ transition: 'stroke-dasharray 1s ease-out' }}
                    />
                  </svg>
                  <div className="absolute inset-0 flex flex-col items-center justify-center">
                    <span className="text-3xl font-bold number-display">{investmentScore}</span>
                    <span className="text-xs text-muted-foreground">/100</span>
                  </div>
                </div>
                <Badge
                  variant={
                    recommendation.includes('Buy') ? 'default' :
                    recommendation.includes('Hold') ? 'secondary' : 'destructive'
                  }
                  className="mt-3 text-sm px-4 py-1"
                >
                  {recommendation}
                </Badge>
              </div>

              <div className="w-full space-y-4 mt-2">
                {strengths.length > 0 && (
                  <div className="space-y-2">
                    <p className="text-sm font-medium text-muted-foreground">Key Strengths:</p>
                    {strengths.slice(0, 3).map((s, i) => (
                      <div key={i} className="flex items-center gap-2 text-sm px-3 py-2 rounded-md bg-green-500/10 border border-green-500/20">
                        <TrendingUp className="h-3.5 w-3.5 text-green-400 flex-shrink-0" />
                        <span className="text-green-300">{s}</span>
                      </div>
                    ))}
                  </div>
                )}

                {considerations.length > 0 && (
                  <div className="space-y-2">
                    <p className="text-sm font-medium text-muted-foreground">Considerations:</p>
                    {considerations.slice(0, 3).map((c, i) => (
                      <div key={i} className="flex items-center gap-2 text-sm px-3 py-2 rounded-md bg-yellow-500/10 border border-yellow-500/20">
                        <AlertTriangle className="h-3.5 w-3.5 text-yellow-400 flex-shrink-0" />
                        <span className="text-yellow-300">{c}</span>
                      </div>
                    ))}
                  </div>
                )}

                {considerations.length === 0 && (
                  <div className="flex items-center justify-center gap-2 text-sm px-3 py-2 rounded-md bg-green-500/10 border border-green-500/20">
                    <Shield className="h-4 w-4 text-green-400" />
                    <span className="text-green-400">No major concerns identified</span>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Investment Summary Text */}
          {analysis.investment_summary && (
            <div className="text-center p-4 rounded-lg bg-muted/30 border border-border/50">
              <p className="text-sm text-muted-foreground italic">{analysis.investment_summary}</p>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
