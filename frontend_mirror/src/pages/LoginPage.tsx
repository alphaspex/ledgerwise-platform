/**
 * Inputs :
 *   - props: {} (no props)
 *   - useApp(): AppContextValue (from shared/AppContext.tsx)
 *   - login(body: LoginRequest): Promise<LoginResponse> (api/authApi.ts)
 *   - useAsync, useToast hooks
 * Outputs :
 *   - JSX.Element (AuthCardLayout with email + password TextInputs and Log in Button; links 'Forgot password' -> goTo('forgot_password') and 'Have an invite code' -> goTo('accept_invite'); shows the SESSION_EXPIRED_TEXT notice when context.sessionExpired is true; on success calls signIn(token, user) then goTo('dashboard'); on failure shows the error detail under the form)
 * File explanation : Login screen.
 */
