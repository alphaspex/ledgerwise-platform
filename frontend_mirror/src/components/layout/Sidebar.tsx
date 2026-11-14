/**
 * Inputs :
 *   - props: { activeScreen: ScreenName; onNavigate: (screen: ScreenName) => void; isAdmin: boolean }
 *   - SIDEBAR_ITEMS: SidebarItem[] (from shared/constants.ts)
 *   - icons map from lucide-react (resolve SidebarItem.icon by name)
 * Outputs :
 *   - JSX.Element (vertical nav shown from md breakpoint up; active item highlighted with a sliding gold indicator; items with adminOnly hidden when isAdmin is false; 'Ledgerwise' wordmark on top)
 * File explanation : Desktop navigation.
 */
