/**
 * Inputs :
 *   - props: {} (no props)
 *   - useApp(): AppContextValue (from shared/AppContext.tsx)
 *   - usePolling(getDashboard) -> DashboardSummary (api/dashboardApi.ts)
 *   - useAuthGuard()
 * Outputs :
 *   - JSX.Element (PageHeader 'Dashboard' and four SummaryBlocks: Research (approved / pending / needs review) -> goTo('research'); Emails (pending review / sent / rejected) -> goTo('email_review'); Conversations (auto / needs human / taken over) -> goTo('conversations'); Bookings (upcoming) with unread notifications count -> goTo('bookings'); Skeleton / ErrorState)
 * File explanation : Home screen with summary numbers.
 */
