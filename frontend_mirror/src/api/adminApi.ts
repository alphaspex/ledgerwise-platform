/**
 * Inputs :
 *   - apiCall, ENDPOINTS
 *   - types from shared/types.ts
 * Outputs :
 *   - listUsers(): Promise<UserSummary[]>
 *   - inviteUser(body: InviteRequest): Promise<UserSummary>
 *   - removeUser(id: number): Promise<OkResponse>
 * File explanation : Typed wrappers for the admin-only user management endpoints (/admin/users).
 */
