/**
 * Dividend Calendar Page.
 *
 * Displays a yearly calendar view of dividend payments with export functionality.
 */

'use client';

import { useState } from 'react';
import { Layout } from '@/components/layout/Layout';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import MonthView from '@/components/calendar/MonthView';
import { useCalendar } from '@/hooks/useCalendar';
import { exportCalendar } from '@/lib/api';
import { Download, ChevronLeft, ChevronRight, Calendar } from 'lucide-react';
import { toast } from 'sonner';

export default function CalendarPage() {
  const currentYear = new Date().getFullYear();
  const [selectedYear, setSelectedYear] = useState(currentYear);

  const { data: calendarData, isLoading } = useCalendar(selectedYear, 12);

  const handleExport = async () => {
    try {
      const blob = await exportCalendar(selectedYear, 12);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `dividends_${selectedYear}.ics`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
      toast.success('Calendar exported successfully');
    } catch (error) {
      console.error('Failed to export calendar:', error);
      toast.error('Failed to export calendar');
    }
  };

  const handlePreviousYear = () => {
    setSelectedYear((y) => y - 1);
  };

  const handleNextYear = () => {
    setSelectedYear((y) => y + 1);
  };

  const handleCurrentYear = () => {
    setSelectedYear(currentYear);
  };

  // Calculate year totals
  const yearTotal =
    calendarData?.reduce((sum, month) => sum + month.total, 0) || 0;
  const monthsWithDividends =
    calendarData?.filter((month) => month.events.length > 0).length || 0;

  return (
    <Layout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div className="flex items-center gap-4">
          <Button
            variant="outline"
            size="icon"
            onClick={handlePreviousYear}
            disabled={isLoading}
          >
            <ChevronLeft className="h-4 w-4" />
          </Button>

          <div className="flex flex-col items-center">
            <h1 className="text-3xl font-bold">{selectedYear}</h1>
            {!isLoading && (
              <p className="text-sm text-muted-foreground">
                £{yearTotal.toFixed(2)} across {monthsWithDividends} months
              </p>
            )}
          </div>

          <Button
            variant="outline"
            size="icon"
            onClick={handleNextYear}
            disabled={isLoading}
          >
            <ChevronRight className="h-4 w-4" />
          </Button>
        </div>

        <div className="flex gap-2">
          {selectedYear !== currentYear && (
            <Button variant="outline" onClick={handleCurrentYear}>
              <Calendar className="mr-2 h-4 w-4" />
              Current Year
            </Button>
          )}
          <Button onClick={handleExport} disabled={isLoading}>
            <Download className="mr-2 h-4 w-4" />
            Export to Calendar
          </Button>
        </div>
      </div>

      {/* Calendar Grid */}
      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {Array.from({ length: 12 }).map((_, i) => (
            <Card key={i}>
              <CardContent className="p-6">
                <Skeleton className="h-[300px]" />
              </CardContent>
            </Card>
          ))}
        </div>
      ) : calendarData ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {calendarData.map((month) => (
            <Card key={month.month}>
              <CardContent className="p-6">
                <MonthView month={month} />
              </CardContent>
            </Card>
          ))}
        </div>
      ) : (
        <Card>
          <CardContent className="p-6 text-center text-muted-foreground">
            No calendar data available for {selectedYear}
          </CardContent>
        </Card>
      )}
      </div>
    </Layout>
  );
}
