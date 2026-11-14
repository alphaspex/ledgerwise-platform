/**
 * Inputs :
 *   - props: {} (no props)
 *   - useApp(): AppContextValue (from shared/AppContext.tsx)
 *   - requestPasswordChange(body: ChangePasswordRequest): Promise<OkResponse>, confirmPasswordChange(body: ChangePasswordConfirmRequest): Promise<OkResponse> (api/authApi.ts)
 *   - useAuthGuard(), useAsync, useToast hooks
 *   - PASSWORD_MIN_LEN, CODE_LENGTH (shared/constants.ts)
 * Outputs :
 *   - JSX.Element (PageHeader + Card with two steps: step 1 old password -> requestPasswordChange; step 2 code + new password + confirm -> confirmPasswordChange; step switch animated; on 410 returns to step 1 with 'Code expired, request a new one'; on success toast and goTo('dashboard'))
 * File explanation : Logged-in password change with an emailed code.
 */
