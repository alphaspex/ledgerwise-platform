/**
 * Inputs :
 *   - props: { children: React.ReactNode }
 *   - getStoredToken(): string | null, setStoredToken(token: string | null): void, registerClientHandlers(h: { onUnauthorized: () => void; onRateLimited: () => void }): void (from api/client.ts)
 *   - RATE_LIMIT_TOAST: string, SESSION_EXPIRED_TEXT: string, TOKEN_STORAGE_KEY: string (from shared/constants.ts)
 * Outputs :
 *   - AppProvider(props: { children: ReactNode }): JSX.Element
 *   - useApp(): AppContextValue  (user, screen, selectedCompanyId, selectedThreadCompanyId, toasts, sessionExpired, signIn, signOut, goTo, pushToast, dismissToast)
 * File explanation : The ONLY global state (React Context + useState). On load it restores the user by decoding the JWT payload {user_id, email, is_admin, exp} from localStorage (expired or malformed token => signed out). signIn stores the token and user. signOut clears the token, sets screen 'login'. goTo(screen, companyId?) sets screen and, when companyId is given, selectedCompanyId (screen 'company_detail') or selectedThreadCompanyId (screen 'chat'). Registers client handlers: 401 => signOut + sessionExpired=true + SESSION_EXPIRED_TEXT; 429 => pushToast('error', RATE_LIMIT_TOAST). Toasts get an incrementing id; auto-removal is done by ToastHost.
 */
