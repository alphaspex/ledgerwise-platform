/**
 * Inputs :
 *   - props: {} (no props)
 *   - useApp(): AppContextValue (from shared/AppContext.tsx)
 *   - usePolling(() => listBookings({ from, to })) -> Booking[] where from/to are the first and last instants of the shown month as ISO strings (api/bookingsApi.ts)
 *   - useAuthGuard()
 * Outputs :
 *   - JSX.Element (PageHeader 'Bookings'; BookingCalendar for the shown month (state: year, month; starts at the current month); changing the month refetches; Skeleton / ErrorState; empty month still shows the calendar)
 * File explanation : Calls booked by the agent or through the booking link.
 */

import { useCallback, useState } from 'react';
import { listBookings } from '../api/bookingsApi';
import { BookingCalendar } from '../components/features/BookingCalendar';
import { PageHeader } from '../components/layout/PageHeader';
import { ErrorState } from '../components/ui/ErrorState';
import { Skeleton } from '../components/ui/Skeleton';
import { useAuthGuard } from '../hooks/useAuthGuard';
import { usePolling } from '../hooks/usePolling';
import { useApp } from '../shared/AppContext';
import type { Booking } from '../shared/types';

export function BookingsPage() {
  useAuthGuard();
  const app = useApp();
  void app;

  const now = new Date();
  const [year, setYear] = useState(now.getFullYear());
  const [month, setMonth] = useState(now.getMonth());

  const fetchMonthBookings = useCallback(() => {
    const from = new Date(Date.UTC(year, month, 1, 0, 0, 0, 0)).toISOString();
    const to = new Date(Date.UTC(year, month + 1, 0, 23, 59, 59, 999)).toISOString();
    return listBookings({ from, to });
  }, [year, month]);

  const { data: bookings, loading, error, refresh } = usePolling<Booking[]>(fetchMonthBookings);

  const handleMonthChange = (nextYear: number, nextMonth: number) => {
    setYear(nextYear);
    setMonth(nextMonth);
  };

  if (loading && !bookings) {
    return (
      <div className="space-y-6">
        <PageHeader title="Bookings" />
        <Skeleton variant="card" count={2} />
      </div>
    );
  }

  if (error && !bookings) {
    return (
      <div className="space-y-6">
        <PageHeader title="Bookings" />
        <ErrorState message={error.detail} onRetry={() => void refresh()} />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader title="Bookings" subtitle="Scheduled discovery calls and booking history" />
      <BookingCalendar
        bookings={bookings ?? []}
        year={year}
        month={month}
        onMonthChange={handleMonthChange}
      />
    </div>
  );
}
