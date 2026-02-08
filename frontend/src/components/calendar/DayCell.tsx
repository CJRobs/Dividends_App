/**
 * Day Cell Component for Calendar View.
 *
 * Displays a single day in the calendar grid with dividend events.
 */

'use client';

import { DividendEvent } from '@/types';
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover';

interface DayCellProps {
  day: number;
  events: DividendEvent[];
}

export default function DayCell({ day, events }: DayCellProps) {
  const hasEvents = events.length > 0;
  const total = events.reduce((sum, e) => sum + e.amount, 0);

  return (
    <Popover>
      <PopoverTrigger asChild>
        <button
          className={`
            aspect-square p-1 text-sm rounded hover:bg-accent transition-colors
            ${hasEvents ? 'bg-primary/10 font-semibold' : 'text-muted-foreground'}
          `}
        >
          <div className="flex flex-col items-center justify-center h-full">
            <div>{day}</div>
            {hasEvents && (
              <div className="text-xs text-primary mt-0.5">
                £{total.toFixed(0)}
              </div>
            )}
          </div>
        </button>
      </PopoverTrigger>

      {hasEvents && (
        <PopoverContent className="w-80">
          <div className="space-y-2">
            <h4 className="font-semibold">Dividends on Day {day}</h4>
            <div className="space-y-2">
              {events.map((event, i) => (
                <div
                  key={i}
                  className="flex justify-between items-start text-sm border-b pb-2 last:border-b-0 last:pb-0"
                >
                  <div className="flex-1">
                    <div className="font-medium">{event.ticker}</div>
                    <div className="text-xs text-muted-foreground">
                      {event.company_name}
                    </div>
                    {event.expected && (
                      <div className="text-xs text-orange-500 mt-0.5">
                        Expected
                      </div>
                    )}
                  </div>
                  <div className="font-semibold ml-2">
                    £{event.amount.toFixed(2)}
                  </div>
                </div>
              ))}
            </div>
            <div className="border-t pt-2 flex justify-between font-semibold">
              <span>Total</span>
              <span>£{total.toFixed(2)}</span>
            </div>
          </div>
        </PopoverContent>
      )}
    </Popover>
  );
}
