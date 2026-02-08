/**
 * Month View Component for Calendar.
 *
 * Displays a single month's calendar grid with dividend events.
 */

'use client';

import { CalendarMonth } from '@/types';
import DayCell from './DayCell';

const MONTH_NAMES = [
  'January',
  'February',
  'March',
  'April',
  'May',
  'June',
  'July',
  'August',
  'September',
  'October',
  'November',
  'December',
];

const DAY_NAMES = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

interface MonthViewProps {
  month: CalendarMonth;
}

export default function MonthView({ month }: MonthViewProps) {
  // Calculate calendar grid layout
  const daysInMonth = new Date(month.year, month.month, 0).getDate();
  const firstDay = new Date(month.year, month.month - 1, 1).getDay();

  // Group events by day
  const eventsByDay = month.events.reduce(
    (acc, event) => {
      const day = new Date(event.date).getDate();
      if (!acc[day]) acc[day] = [];
      acc[day].push(event);
      return acc;
    },
    {} as Record<number, typeof month.events>
  );

  return (
    <div className="space-y-4">
      {/* Month header */}
      <div className="flex justify-between items-center">
        <h3 className="font-semibold text-lg">
          {MONTH_NAMES[month.month - 1]}
        </h3>
        {month.total > 0 && (
          <span className="text-sm text-muted-foreground">
            Total: £{month.total.toFixed(2)}
          </span>
        )}
      </div>

      {/* Calendar grid */}
      <div className="grid grid-cols-7 gap-1">
        {/* Day headers */}
        {DAY_NAMES.map((day) => (
          <div
            key={day}
            className="text-center text-xs font-medium text-muted-foreground py-2"
          >
            {day}
          </div>
        ))}

        {/* Empty cells for days before month starts */}
        {Array.from({ length: firstDay }).map((_, i) => (
          <div key={`empty-${i}`} className="aspect-square" />
        ))}

        {/* Days of month */}
        {Array.from({ length: daysInMonth }).map((_, i) => {
          const day = i + 1;
          return (
            <DayCell key={day} day={day} events={eventsByDay[day] || []} />
          );
        })}
      </div>
    </div>
  );
}
