'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Users } from 'lucide-react';
import type { AnalystSentiment } from '@/types/screener';

interface AnalystCardProps {
  sentiment?: AnalystSentiment;
  currentPrice?: number;
}

export function AnalystCard({ sentiment, currentPrice }: AnalystCardProps) {
  if (!sentiment || !sentiment.total_analysts) return null;

  const total = sentiment.total_analysts;
  const segments = [
    { label: 'Strong Buy', count: sentiment.strong_buy || 0, color: '#22c55e' },
    { label: 'Buy', count: sentiment.buy || 0, color: '#84cc16' },
    { label: 'Hold', count: sentiment.hold || 0, color: '#eab308' },
    { label: 'Sell', count: sentiment.sell || 0, color: '#f97316' },
    { label: 'Strong Sell', count: sentiment.strong_sell || 0, color: '#ef4444' },
  ];

  const upside = sentiment.target_price && currentPrice && currentPrice > 0
    ? ((sentiment.target_price - currentPrice) / currentPrice * 100)
    : null;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base flex items-center gap-2">
          <Users className="h-4 w-4 text-blue-500" />
          Analyst Sentiment ({total} analysts)
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {/* Consensus Badge */}
          {sentiment.consensus && (
            <div className="flex items-center gap-3">
              <span className="text-sm text-muted-foreground">Consensus:</span>
              <Badge
                variant={
                  sentiment.consensus.includes('Buy') ? 'default' :
                  sentiment.consensus === 'Hold' ? 'secondary' : 'destructive'
                }
                className="text-sm px-3"
              >
                {sentiment.consensus}
              </Badge>
            </div>
          )}

          {/* Horizontal stacked bar */}
          <div>
            <div className="flex h-6 rounded-full overflow-hidden">
              {segments.map(seg => {
                const pct = (seg.count / total) * 100;
                if (pct === 0) return null;
                return (
                  <div
                    key={seg.label}
                    style={{ width: `${pct}%`, backgroundColor: seg.color }}
                    className="flex items-center justify-center text-[10px] font-bold text-white transition-all"
                    title={`${seg.label}: ${seg.count}`}
                  >
                    {pct >= 10 ? seg.count : ''}
                  </div>
                );
              })}
            </div>
            <div className="flex justify-between mt-2">
              {segments.map(seg => (
                <div key={seg.label} className="flex items-center gap-1">
                  <div className="w-2 h-2 rounded-full" style={{ backgroundColor: seg.color }} />
                  <span className="text-[10px] text-muted-foreground">{seg.label}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Target Price */}
          {sentiment.target_price && (
            <div className="flex items-center justify-between pt-2 border-t">
              <div>
                <p className="text-sm text-muted-foreground">Target Price</p>
                <p className="text-xl font-bold">${sentiment.target_price.toFixed(2)}</p>
              </div>
              {upside != null && (
                <div className="text-right">
                  <p className="text-sm text-muted-foreground">Potential Upside</p>
                  <p className={`text-xl font-bold ${upside >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                    {upside >= 0 ? '+' : ''}{upside.toFixed(1)}%
                  </p>
                </div>
              )}
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
