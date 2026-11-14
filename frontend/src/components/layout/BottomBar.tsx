/**
 * Inputs :
 *   - props: { activeScreen: ScreenName; onNavigate: (screen: ScreenName) => void; isAdmin: boolean }
 *   - BOTTOM_BAR_SCREENS: ScreenName[], SIDEBAR_ITEMS (from shared/constants.ts)
 * Outputs :
 *   - JSX.Element (fixed bottom tab bar, visible below md breakpoint; 5 tabs from BOTTOM_BAR_SCREENS plus a 'More' tab that opens a Modal listing the remaining SIDEBAR_ITEMS)
 * File explanation : Mobile navigation.
 */

import { useState } from 'react';
import { icons, MoreHorizontal } from 'lucide-react';
import { BOTTOM_BAR_SCREENS, SIDEBAR_ITEMS } from '../../shared/constants';
import type { ScreenName } from '../../shared/types';
import { Modal } from '../ui/Modal';

export function BottomBar({
  activeScreen,
  onNavigate,
  isAdmin,
}: {
  activeScreen: ScreenName;
  onNavigate: (screen: ScreenName) => void;
  isAdmin: boolean;
}) {
  const [moreOpen, setMoreOpen] = useState(false);

  const visibleItems = SIDEBAR_ITEMS.filter((item) => !item.adminOnly || isAdmin);
  const primaryItems = BOTTOM_BAR_SCREENS.map((s) =>
    visibleItems.find((item) => item.screen === s),
  ).filter((item): item is (typeof visibleItems)[number] => Boolean(item));
  const remainingItems = visibleItems.filter(
    (item) => !BOTTOM_BAR_SCREENS.includes(item.screen),
  );
  const isMoreActive = remainingItems.some((item) => item.screen === activeScreen);

  return (
    <>
      <nav
        aria-label="Mobile navigation"
        className="fixed bottom-0 inset-x-0 z-40 md:hidden bg-surface border-t border-line px-1 py-1.5 flex items-center justify-around"
      >
        {primaryItems.map((item) => {
          const Icon = icons[item.icon as keyof typeof icons];
          const active = activeScreen === item.screen;
          return (
            <button
              key={item.screen}
              type="button"
              onClick={() => onNavigate(item.screen)}
              className={`flex flex-col items-center justify-center gap-0.5 px-2 py-1 rounded-lg text-[11px] font-medium transition-colors min-w-0 ${
                active ? 'text-gold-deep' : 'text-navy-mute hover:text-navy'
              }`}
            >
              {Icon ? <Icon className="h-5 w-5 shrink-0" aria-hidden="true" /> : null}
              <span className="truncate max-w-[64px]">{item.label}</span>
            </button>
          );
        })}
        <button
          type="button"
          onClick={() => setMoreOpen(true)}
          className={`flex flex-col items-center justify-center gap-0.5 px-2 py-1 rounded-lg text-[11px] font-medium transition-colors ${
            isMoreActive ? 'text-gold-deep' : 'text-navy-mute hover:text-navy'
          }`}
        >
          <MoreHorizontal className="h-5 w-5 shrink-0" aria-hidden="true" />
          <span>More</span>
        </button>
      </nav>

      <Modal open={moreOpen} title="More" onClose={() => setMoreOpen(false)}>
        <div className="space-y-1">
          {remainingItems.map((item) => {
            const Icon = icons[item.icon as keyof typeof icons];
            const active = activeScreen === item.screen;
            return (
              <button
                key={item.screen}
                type="button"
                onClick={() => {
                  onNavigate(item.screen);
                  setMoreOpen(false);
                }}
                className={`w-full flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors text-left ${
                  active
                    ? 'bg-gold/10 text-gold-deep'
                    : 'text-navy-soft hover:bg-canvas hover:text-navy'
                }`}
              >
                {Icon ? <Icon className="h-4 w-4 shrink-0" aria-hidden="true" /> : null}
                <span>{item.label}</span>
              </button>
            );
          })}
        </div>
      </Modal>
    </>
  );
}
