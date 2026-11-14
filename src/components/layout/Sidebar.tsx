/**
 * Inputs :
 *   - props: { activeScreen: ScreenName; onNavigate: (screen: ScreenName) => void; isAdmin: boolean }
 *   - SIDEBAR_ITEMS: SidebarItem[] (from shared/constants.ts)
 *   - icons map from lucide-react (resolve SidebarItem.icon by name)
 * Outputs :
 *   - JSX.Element (vertical nav shown from md breakpoint up; active item highlighted with a sliding gold indicator; items with adminOnly hidden when isAdmin is false; 'Ledgerwise' wordmark on top)
 * File explanation : Desktop navigation.
 */

import { motion } from 'framer-motion';
import { icons } from 'lucide-react';
import { SIDEBAR_ITEMS } from '../../shared/constants';
import type { ScreenName } from '../../shared/types';

export function Sidebar({
  activeScreen,
  onNavigate,
  isAdmin,
}: {
  activeScreen: ScreenName;
  onNavigate: (screen: ScreenName) => void;
  isAdmin: boolean;
}) {
  const visibleItems = SIDEBAR_ITEMS.filter((item) => !item.adminOnly || isAdmin);

  return (
    <aside className="hidden md:flex md:w-60 md:flex-col md:shrink-0 bg-surface border-r border-line min-h-screen">
      <div className="h-16 px-6 flex items-center border-b border-line">
        <span className="text-lg font-bold tracking-tight text-navy">Ledgerwise</span>
      </div>

      <nav aria-label="Primary navigation" className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
        {visibleItems.map((item) => {
          const Icon = icons[item.icon as keyof typeof icons];
          const active = activeScreen === item.screen;

          return (
            <button
              key={item.screen}
              type="button"
              onClick={() => onNavigate(item.screen)}
              className={`relative w-full flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors text-left ${
                active ? 'text-navy bg-canvas' : 'text-navy-soft hover:text-navy hover:bg-canvas/60'
              }`}
            >
              {active ? (
                <motion.span
                  layoutId="sidebar-gold-indicator"
                  transition={{ type: 'spring', stiffness: 400, damping: 30 }}
                  className="absolute left-0 top-1.5 bottom-1.5 w-1 rounded-r-full bg-gold"
                />
              ) : null}
              {Icon ? (
                <Icon
                  className={`h-4 w-4 shrink-0 ${active ? 'text-gold-deep' : 'text-navy-mute'}`}
                  aria-hidden="true"
                />
              ) : null}
              <span className="truncate">{item.label}</span>
            </button>
          );
        })}
      </nav>
    </aside>
  );
}
