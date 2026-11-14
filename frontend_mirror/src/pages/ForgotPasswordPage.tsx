/**
 * Inputs :
 *   - props: {} (no props)
 *   - useApp(): AppContextValue (from shared/AppContext.tsx)
 *   - forgotPassword(body: ForgotPasswordRequest): Promise<OkResponse> (api/authApi.ts)
 *   - useAsync, useToast hooks
 * Outputs :
 *   - JSX.Element (AuthCardLayout with an email TextInput and Send code Button; on success shows toast 'If that email exists, a code was sent' and goTo('reset_password'); link back to login)
 * File explanation : Step 1 of resetting a forgotten password.
 */
