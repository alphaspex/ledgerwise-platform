/**
 * Inputs :
 *   - props: {} (no props)
 *   - useApp(): AppContextValue (from shared/AppContext.tsx)
 *   - usePolling(getDashboard) -> DashboardSummary (api/dashboardApi.ts)
 *   - useAuthGuard()
 * Outputs :
 *   - JSX.Element (four pipeline SummaryBlocks plus AI usage totals, cost completeness, and per-module breakdown; Skeleton / ErrorState)
 * File explanation : Home screen with pipeline counts and persisted AI usage totals.
 */
