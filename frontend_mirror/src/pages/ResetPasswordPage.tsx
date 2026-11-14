/**
 * Inputs :
 *   - props: {} (no props)
 *   - useApp(): AppContextValue (from shared/AppContext.tsx)
 *   - resetPassword(body: ResetPasswordRequest): Promise<OkResponse> (api/authApi.ts)
 *   - PASSWORD_MIN_LEN: number, CODE_LENGTH: number (shared/constants.ts)
 *   - useAsync, useToast hooks
 * Outputs :
 *   - JSX.Element (AuthCardLayout with email, 6-digit code, new password and confirm TextInputs; client check: password length >= PASSWORD_MIN_LEN and both passwords equal; on success toast 'Password updated' and goTo('login'); shows 400/410 detail inline)
 * File explanation : Step 2 of resetting a forgotten password.
 */
