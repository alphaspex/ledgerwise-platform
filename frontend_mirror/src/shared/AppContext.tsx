/**
 * Inputs :
 *   - props: { children: React.ReactNode }
 *   - getStoredToken(): string | null, setStoredToken(token: string | null): void, registerClientHandlers(h: { onUnauthorized: () => void; onRateLimited: () => void }): void (from api/client.ts)
 *   - sessionStorage key ledgerwise.navigation.v1: { userId: number; screen: ScreenName; selectedCompanyId: number | null; selectedThreadCompanyId: number | null }
 * Outputs :
 *   - AppProvider(props: { children: ReactNode }): JSX.Element
 *   - useApp(): AppContextValue (user, screen, selectedCompanyId, selectedThreadCompanyId, toasts, sessionExpired, signIn, signOut, goTo, pushToast, dismissToast)
 * File explanation : Owns global React state. Restores the authenticated user's current screen and selected entity from tab-scoped sessionStorage, validates the saved user and IDs, persists navigation changes, and clears stored navigation on sign-out. JWT validation and 401/429 handlers remain unchanged.
 */
