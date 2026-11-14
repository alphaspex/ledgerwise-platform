/**
 * Inputs :
 *   - props: {} (no props)
 *   - useApp(): AppContextValue (from shared/AppContext.tsx)
 *   - usePolling(listUsers) -> UserSummary[]; inviteUser(body: InviteRequest): Promise<UserSummary>; removeUser(id: number): Promise<OkResponse> (api/adminApi.ts)
 *   - useAuthGuard({ requireAdmin: true }), useAsync, useToast hooks
 * Outputs :
 *   - JSX.Element (PageHeader 'Team', InviteForm, grid of Cards (email, Admin/Member pill, joined date, Remove Button hidden for the current user); Remove opens a confirmation Modal; Skeleton / EmptyState / ErrorState for loading / empty / failed)
 * File explanation : Admin-only user management.
 */
