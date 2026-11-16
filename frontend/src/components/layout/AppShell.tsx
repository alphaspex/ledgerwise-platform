/**
 * Inputs :
 *   - props: { children: ReactNode }
 *   - useApp(): AppContextValue (from shared/AppContext.tsx)
 *   - usePolling(listNotifications) -> { data: Notification[] | null; error: ApiError | null }; markNotificationsRead(body: MarkReadRequest): Promise<OkResponse> (from api/notificationsApi.ts)
 *   - logout(): Promise<OkResponse> (from api/authApi.ts)
 * Outputs :
 *   - JSX.Element (desktop: Sidebar left + top bar + scrollable content; mobile: top bar + content + BottomBar)
 *   - top bar contains NotificationBell, the user's email and a Log out button (calls logout() then context.signOut())
 * File explanation : Layout of every signed-in screen. Owns 5s notification polling and passes data plus polling errors to NotificationBell, so failures are not shown as an empty list. Bell item click navigates: unsure_answer and do_not_contact -> goTo('chat', company_id); contact_missing -> goTo('contacts_needed'); booking_conflict -> goTo('bookings').
 */

import { useCallback, useState, type ReactNode } from 'react';
import { LogOut } from 'lucide-react';
import { logout } from '../../api/authApi';
import { listNotifications, markNotificationsRead } from '../../api/notificationsApi';
import { usePolling } from '../../hooks/usePolling';
import { useApp } from '../../shared/AppContext';
import type { Notification } from '../../shared/types';
import { Button } from '../ui/Button';
import { BottomBar } from './BottomBar';
import { NotificationBell } from './NotificationBell';
import { Sidebar } from './Sidebar';

export function AppShell({ children }: { children: ReactNode }) {
  const { user, screen, signOut, goTo } = useApp();
  const [loggingOut, setLoggingOut] = useState(false);

  const fetchNotifications = useCallback(() => listNotifications(), []);
  const { data: notificationsData, error: notificationsError, refresh } = usePolling<Notification[]>(fetchNotifications);
  const notifications = notificationsData ?? [];

  const handleMarkAllRead = useCallback(async () => {
    const unreadIds = notifications.filter((n) => !n.read).map((n) => n.id);
    if (unreadIds.length === 0) return;
    try {
      await markNotificationsRead({ ids: unreadIds });
      await refresh();
    } catch {
      // Handled by client handlers if 401/429
    }
  }, [notifications, refresh]);

  const handleSelectNotification = useCallback(
    async (notification: Notification) => {
      if (!notification.read) {
        try {
          await markNotificationsRead({ ids: [notification.id] });
          await refresh();
        } catch {
          // Proceed with navigation even if mark read fails
        }
      }
      if (notification.reason === 'unsure_answer' || notification.reason === 'do_not_contact') {
        goTo('chat', notification.company_id);
      } else if (notification.reason === 'contact_missing') {
        goTo('contacts_needed');
      } else if (notification.reason === 'booking_conflict') {
        goTo('bookings');
      }
    },
    [goTo, refresh],
  );

  const handleLogout = useCallback(async () => {
    setLoggingOut(true);
    try {
      await logout();
    } catch {
      // Sign out locally even if logout request fails
    } finally {
      setLoggingOut(false);
      signOut();
    }
  }, [signOut]);

  const isAdmin = Boolean(user?.is_admin);

  return (
    <div className="min-h-screen flex bg-canvas text-navy">
      <Sidebar activeScreen={screen} onNavigate={(s) => goTo(s)} isAdmin={isAdmin} />

      <div className="flex-1 flex flex-col min-w-0">
        <header className="h-16 shrink-0 bg-surface border-b border-line px-4 md:px-6 flex items-center justify-between gap-4">
          <div className="md:hidden font-bold text-lg tracking-tight text-navy">Ledgerwise</div>
          <div className="hidden md:block" />

          <div className="flex items-center gap-3 sm:gap-4">
            <NotificationBell
              notifications={notifications}
              error={notificationsError}
              onMarkAllRead={() => void handleMarkAllRead()}
              onSelect={(n) => void handleSelectNotification(n)}
            />
            {user ? (
              <span className="hidden sm:inline text-xs sm:text-sm text-navy-soft truncate max-w-[200px]">
                {user.email}
              </span>
            ) : null}
            <Button
              variant="secondary"
              icon={LogOut}
              loading={loggingOut}
              onClick={() => void handleLogout()}
            >
              Log out
            </Button>
          </div>
        </header>

        <main className="flex-1 overflow-y-auto p-4 md:p-8 pb-24 md:pb-8">
          <div className="mx-auto max-w-6xl">{children}</div>
        </main>
      </div>

      <BottomBar activeScreen={screen} onNavigate={(s) => goTo(s)} isAdmin={isAdmin} />
    </div>
  );
}
