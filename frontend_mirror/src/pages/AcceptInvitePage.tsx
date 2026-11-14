/**
 * Inputs :
 *   - props: {} (no props)
 *   - useApp(): AppContextValue (from shared/AppContext.tsx)
 *   - acceptInvite(body: AcceptInviteRequest): Promise<OkResponse> (api/authApi.ts)
 *   - PASSWORD_MIN_LEN: number, CODE_LENGTH: number (shared/constants.ts)
 *   - useAsync, useToast hooks
 * Outputs :
 *   - JSX.Element (AuthCardLayout with email, invite code, password and confirm TextInputs; same client checks as ResetPasswordPage; on success toast 'Account ready, log in' and goTo('login'))
 * File explanation : Invited teammate sets their password.
 */
