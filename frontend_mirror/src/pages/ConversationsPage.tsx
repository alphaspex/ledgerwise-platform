/**
 * Inputs :
 *   - props: {} (no props)
 *   - useApp(): AppContextValue (from shared/AppContext.tsx)
 *   - usePolling(listThreads) -> ThreadSummary[] (api/outreachApi.ts)
 *   - useAuthGuard()
 * Outputs :
 *   - JSX.Element (PageHeader 'Conversations'; threads needing a human sorted first, then newest; ThreadCards; click -> goTo('chat', company_id); Skeleton / EmptyState 'No conversations yet' / ErrorState)
 * File explanation : List of all conversations with prospects.
 */
