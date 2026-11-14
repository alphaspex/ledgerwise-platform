/**
 * Inputs :
 *   - props: { bookings: Booking[]; year: number; month: number (0..11); onMonthChange: (year: number, month: number) => void }
 *   - BOOKING_STATUS_LABEL, BOOKING_STATUS_TONE (from shared/constants.ts)
 * Outputs :
 *   - JSX.Element (month grid with prev/next arrows and a title; days having bookings show dots; clicking a day shows that day's bookings below as cards with time, domain, source (Agent / Prospect link) and a status StatusPill; today highlighted)
 * File explanation : Month calendar of booked calls. Holds only the selected-day state locally.
 */
