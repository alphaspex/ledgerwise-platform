/**
 * Inputs :
 *   - props: {} (no props)
 *   - useApp(): AppContextValue (from shared/AppContext.tsx)
 * Outputs :
 *   - default export App(): JSX.Element
 *   - if user is null: renders ONE auth screen chosen by context.screen ('login' | 'forgot_password' | 'reset_password' | 'accept_invite') inside nothing else
 *   - if user exists: renders <AppShell> containing <PageTransition screenKey={screen}> containing the page for context.screen; also renders <ToastHost /> in both cases
 * File explanation : The screen switcher (there is no router). Maps ScreenName -> page component. Unknown/inaccessible screen falls back to 'dashboard' (or 'login' when signed out). Also guards 'admin_users' for non-admins.
 */
