'use client';

import { useState, useEffect, useRef } from 'react';

interface UseCountUpOptions {
  duration?: number;
  delay?: number;
  decimals?: number;
  easing?: (t: number) => number;
}

// Easing function - ease out cubic
const easeOutCubic = (t: number): number => 1 - Math.pow(1 - t, 3);

export function useCountUp(
  end: number,
  options: UseCountUpOptions = {}
): number {
  const {
    duration = 1200,
    delay = 0,
    decimals = 0,
    easing = easeOutCubic,
  } = options;

  const [count, setCount] = useState(0);
  const startTime = useRef<number | null>(null);
  const animationFrame = useRef<number | null>(null);

  useEffect(() => {
    // Reset on end value change
    setCount(0);
    startTime.current = null;

    const timeout = setTimeout(() => {
      const animate = (timestamp: number) => {
        if (!startTime.current) {
          startTime.current = timestamp;
        }

        const elapsed = timestamp - startTime.current;
        const progress = Math.min(elapsed / duration, 1);
        const easedProgress = easing(progress);

        const currentValue = easedProgress * end;
        setCount(Number(currentValue.toFixed(decimals)));

        if (progress < 1) {
          animationFrame.current = requestAnimationFrame(animate);
        }
      };

      animationFrame.current = requestAnimationFrame(animate);
    }, delay);

    return () => {
      clearTimeout(timeout);
      if (animationFrame.current) {
        cancelAnimationFrame(animationFrame.current);
      }
    };
  }, [end, duration, delay, decimals, easing]);

  return count;
}

// Format number with currency
export function formatCountUp(
  value: number,
  options: {
    prefix?: string;
    suffix?: string;
    separator?: string;
    decimals?: number;
  } = {}
): string {
  const {
    prefix = '',
    suffix = '',
    separator = ',',
    decimals = 0,
  } = options;

  const formatted = value.toFixed(decimals).replace(/\B(?=(\d{3})+(?!\d))/g, separator);
  return `${prefix}${formatted}${suffix}`;
}
