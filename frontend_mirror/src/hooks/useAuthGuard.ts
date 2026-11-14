/**
 * Inputs :
 *   - options?: { requireAdmin?: boolean }
 *   - useApp(): AppContextValue (from shared/AppContext.tsx)
 * Outputs :
 *   - { user: AuthUser | null; isAdmin: boolean }
 * File explanation : Used by protected pages. If user is null it calls goTo('login'). If requireAdmin is true and the user is not an admin it pushes an error toast and calls goTo('dashboard').
 */
