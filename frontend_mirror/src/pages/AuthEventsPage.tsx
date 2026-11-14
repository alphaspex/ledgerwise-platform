/**
 * Inputs :
 *   - props: {} (no props)
 *   - useApp(): AppContextValue (from shared/AppContext.tsx)
 *   - usePolling(() => listAuthEvents({ limit: 200 })) -> AuthEvent[] (api/authApi.ts)
 *   - useAuthGuard()
 * Outputs :
 *   - JSX.Element (PageHeader 'Security log' with note 'Kept for 30 days'; staggered Cards each showing event type pill, user id, IP, user agent, detail and time; read-only, no delete; Skeleton / EmptyState / ErrorState)
 * File explanation : Read-only auth event log visible to all members.
 */
