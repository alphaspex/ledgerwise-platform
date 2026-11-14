/**
 * Inputs :
 *   - props: { activeScreen: ScreenName; onNavigate: (screen: ScreenName) => void; isAdmin: boolean }
 *   - BOTTOM_BAR_SCREENS: ScreenName[], SIDEBAR_ITEMS (from shared/constants.ts)
 * Outputs :
 *   - JSX.Element (fixed bottom tab bar, visible below md breakpoint; 5 tabs from BOTTOM_BAR_SCREENS plus a 'More' tab that opens a Modal listing the remaining SIDEBAR_ITEMS)
 * File explanation : Mobile navigation.
 */
