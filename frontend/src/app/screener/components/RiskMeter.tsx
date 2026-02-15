'use client';

import { useState, useEffect } from 'react';
import { Badge } from '@/components/ui/badge';

interface RiskMeterProps {
  score: number;
  level: string;
  animated?: boolean;
}

export function RiskMeter({ score, level, animated = true }: RiskMeterProps) {
  const [displayScore, setDisplayScore] = useState(0);

  useEffect(() => {
    if (!animated) {
      setDisplayScore(score);
      return;
    }

    const duration = 1000;
    const steps = 60;
    const increment = score / steps;
    let current = 0;

    const timer = setInterval(() => {
      current += increment;
      if (current >= score) {
        setDisplayScore(score);
        clearInterval(timer);
      } else {
        setDisplayScore(Math.round(current));
      }
    }, duration / steps);

    return () => clearInterval(timer);
  }, [score, animated]);

  const rotation = -90 + (displayScore / 100) * 180;

  const getColor = () => {
    if (score <= 20) return '#22c55e';
    if (score <= 40) return '#84cc16';
    if (score <= 60) return '#eab308';
    if (score <= 80) return '#f97316';
    return '#ef4444';
  };

  return (
    <div className="flex flex-col items-center">
      <div className="relative w-40 h-24 overflow-hidden">
        <svg className="w-full h-full" viewBox="0 0 100 50">
          <path d="M 10 50 A 40 40 0 0 1 30 14.2" fill="none" stroke="#22c55e" strokeWidth="8" strokeLinecap="round" opacity="0.3" />
          <path d="M 30 14.2 A 40 40 0 0 1 50 10" fill="none" stroke="#84cc16" strokeWidth="8" strokeLinecap="round" opacity="0.3" />
          <path d="M 50 10 A 40 40 0 0 1 70 14.2" fill="none" stroke="#eab308" strokeWidth="8" strokeLinecap="round" opacity="0.3" />
          <path d="M 70 14.2 A 40 40 0 0 1 90 50" fill="none" stroke="#ef4444" strokeWidth="8" strokeLinecap="round" opacity="0.3" />
          <path
            d={`M 10 50 A 40 40 0 ${displayScore > 50 ? 1 : 0} 1 ${
              50 + 40 * Math.sin((displayScore / 100) * Math.PI)
            } ${50 - 40 * Math.cos((displayScore / 100) * Math.PI)}`}
            fill="none"
            stroke={getColor()}
            strokeWidth="8"
            strokeLinecap="round"
            style={{ transition: 'stroke 0.3s ease' }}
          />
          <g
            style={{
              transform: `rotate(${rotation}deg)`,
              transformOrigin: '50px 50px',
              transition: animated ? 'transform 1s cubic-bezier(0.34, 1.56, 0.64, 1)' : 'none',
            }}
          >
            <line x1="50" y1="50" x2="50" y2="18" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
            <circle cx="50" cy="50" r="4" fill="currentColor" />
          </g>
        </svg>
      </div>
      <div className="text-center mt-2">
        <span className="text-3xl font-bold number-display" style={{ color: getColor() }}>
          {displayScore}
        </span>
        <span className="text-lg text-muted-foreground">/100</span>
      </div>
      <Badge
        variant={level === 'Low' ? 'default' : level === 'Medium' ? 'secondary' : 'destructive'}
        className="mt-2"
      >
        {level} Risk
      </Badge>
    </div>
  );
}
