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
