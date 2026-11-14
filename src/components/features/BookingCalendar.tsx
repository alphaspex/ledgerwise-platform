/**
 * Inputs :
 *   - props: { bookings: Booking[]; year: number; month: number (0..11); onMonthChange: (year: number, month: number) => void }
 *   - BOOKING_STATUS_LABEL, BOOKING_STATUS_TONE (from shared/constants.ts)
 * Outputs :
 *   - JSX.Element (month grid with prev/next arrows and a title; days having bookings show dots; clicking a day shows that day's bookings below as cards with time, domain, source (Agent / Prospect link) and a status StatusPill; today highlighted)
 * File explanation : Month calendar of booked calls. Holds only the selected-day state locally.
 */

import { useMemo, useState } from 'react';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import { BOOKING_STATUS_LABEL, BOOKING_STATUS_TONE } from '../../shared/constants';
import type { Booking } from '../../shared/types';
import { StatusPill } from '../ui/StatusPill';

const WEEKDAYS = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

function toDayKey(year: number, month: number, day: number): string {
  return `${year}-${String(month + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
}

export function BookingCalendar({
  bookings,
  year,
  month,
  onMonthChange,
}: {
  bookings: Booking[];
  year: number;
  month: number;
  onMonthChange: (year: number, month: number) => void;
}) {
  const now = new Date();
  const todayKey = toDayKey(now.getFullYear(), now.getMonth(), now.getDate());
  const [selectedDay, setSelectedDay] = useState<string | null>(todayKey);

  const monthTitle = useMemo(() => {
    return new Date(year, month, 1).toLocaleDateString(undefined, {
      month: 'long',
      year: 'numeric',
    });
  }, [year, month]);

  const bookingsByDay = useMemo(() => {
    const map = new Map<string, Booking[]>();
    for (const b of bookings) {
      const d = new Date(b.scheduled_at);
      if (Number.isNaN(d.getTime())) continue;
      const key = toDayKey(d.getFullYear(), d.getMonth(), d.getDate());
      const arr = map.get(key) ?? [];
      arr.push(b);
      map.set(key, arr);
    }
    return map;
  }, [bookings]);

  const firstWeekday = new Date(year, month, 1).getDay();
  const daysInMonth = new Date(year, month + 1, 0).getDate();
  const cells: Array<number | null> = [
    ...Array.from({ length: firstWeekday }, () => null),
    ...Array.from({ length: daysInMonth }, (_, i) => i + 1),
  ];

  const handlePrev = () => {
    if (month === 0) {
      onMonthChange(year - 1, 11);
    } else {
      onMonthChange(year, month - 1);
    }
  };

  const handleNext = () => {
    if (month === 11) {
      onMonthChange(year + 1, 0);
    } else {
      onMonthChange(year, month + 1);
    }
  };

  const selectedBookings = selectedDay ? (bookingsByDay.get(selectedDay) ?? []) : [];

  return (
    <div className="space-y-6">
      <div className="rounded-xl border border-line bg-surface shadow-card p-5">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-base font-semibold text-navy">{monthTitle}</h2>
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={handlePrev}
              aria-label="Previous month"
              className="p-2 rounded-lg border border-line bg-surface hover:bg-canvas text-navy transition-colors"
            >
              <ChevronLeft className="h-4 w-4" aria-hidden="true" />
            </button>
            <button
              type="button"
              onClick={handleNext}
              aria-label="Next month"
              className="p-2 rounded-lg border border-line bg-surface hover:bg-canvas text-navy transition-colors"
            >
              <ChevronRight className="h-4 w-4" aria-hidden="true" />
            </button>
          </div>
        </div>

        <div className="grid grid-cols-7 gap-1 text-center text-xs font-medium text-navy-mute mb-2">
          {WEEKDAYS.map((wd) => (
            <div key={wd} className="py-1">
              {wd}
            </div>
          ))}
        </div>

        <div className="grid grid-cols-7 gap-1">
          {cells.map((day, idx) => {
            if (day === null) {
              return <div key={`empty-${idx}`} className="h-12 sm:h-14" />;
            }
            const key = toDayKey(year, month, day);
            const dayBookings = bookingsByDay.get(key) ?? [];
            const isToday = key === todayKey;
            const isSelected = key === selectedDay;

            return (
              <button
                key={key}
                type="button"
                onClick={() => setSelectedDay(key)}
                className={[
                  'h-12 sm:h-14 rounded-lg border flex flex-col items-center justify-center gap-1 text-sm tabular-nums transition-colors',
                  isSelected
                    ? 'border-gold bg-gold/10 text-navy font-semibold'
                    : isToday
                      ? 'border-slateblue-400 bg-slateblue-400/10 text-navy font-semibold'
                      : 'border-transparent hover:bg-canvas text-navy-soft',
                ].join(' ')}
              >
                <span>{day}</span>
                {dayBookings.length > 0 ? (
                  <span className="flex items-center gap-0.5">
                    {dayBookings.slice(0, 3).map((b) => (
                      <span key={b.id} className="h-1.5 w-1.5 rounded-full bg-gold-deep" />
                    ))}
                  </span>
                ) : null}
              </button>
            );
          })}
        </div>
      </div>

      <div className="space-y-3">
        <h3 className="text-sm font-semibold text-navy">
          {selectedDay ? `Bookings for ${selectedDay}` : 'Select a day to view bookings'}
        </h3>
        {selectedDay && selectedBookings.length === 0 ? (
          <p className="text-sm text-navy-mute">No bookings on this day.</p>
        ) : null}
        <div className="grid gap-3 sm:grid-cols-2">
          {selectedBookings.map((booking) => {
            const timeStr = new Date(booking.scheduled_at).toLocaleTimeString(undefined, {
              hour: '2-digit',
              minute: '2-digit',
            });
            const sourceLabel = booking.source === 'agent' ? 'Agent' : 'Prospect link';

            return (
              <div
                key={booking.id}
                className="rounded-xl border border-line bg-surface p-4 shadow-card flex items-center justify-between gap-3"
              >
                <div className="min-w-0">
                  <div className="text-sm font-semibold text-navy truncate">{booking.domain}</div>
                  <div className="text-xs text-navy-mute mt-0.5 tabular-nums">
                    {timeStr} · {sourceLabel}
                  </div>
                </div>
                <StatusPill
                  label={BOOKING_STATUS_LABEL[booking.status]}
                  tone={BOOKING_STATUS_TONE[booking.status]}
                />
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
