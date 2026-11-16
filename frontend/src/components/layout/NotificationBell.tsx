/**
 * Inputs :
 *   - props: { notifications: Notification[]; error: ApiError | null; onMarkAllRead: () => void; onSelect: (notification: Notification) => void }
 * Outputs :
 *   - JSX.Element (bell icon button with animated unread-count badge (read === false); click toggles an animated dropdown containing NotificationPanel; closes on outside click)
 * File explanation : Header bell. Pure presentation: no API calls. Forwards notification polling errors to the dropdown.
 */

import { useEffect, useRef, useState } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { Bell } from 'lucide-react';
import type { ApiError } from '../../api/client';
import type { Notification } from '../../shared/types';
import { NotificationPanel } from '../features/NotificationPanel';

export function NotificationBell({
  notifications,
  error,
  onMarkAllRead,
  onSelect,
}: {
  notifications: Notification[];
  error: ApiError | null;
  onMarkAllRead: () => void;
  onSelect: (notification: Notification) => void;
}) {
  const [open, setOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement | null>(null);
  const unreadCount = notifications.filter((n) => !n.read).length;

  useEffect(() => {
    if (!open) return;
    const handlePointerDown = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener('mousedown', handlePointerDown);
    return () => document.removeEventListener('mousedown', handlePointerDown);
  }, [open]);

  return (
    <div ref={containerRef} className="relative">
      <button
        type="button"
        onClick={() => setOpen((prev) => !prev)}
        aria-label={`Notifications (${unreadCount} unread)`}
        aria-expanded={open}
        className="relative inline-flex h-9 w-9 items-center justify-center rounded-lg border border-line bg-surface text-navy-soft hover:text-navy hover:bg-canvas transition-colors"
      >
        <Bell className="h-4 w-4" aria-hidden="true" />
        <AnimatePresence>
          {unreadCount > 0 ? (
            <motion.span
              key="unread-badge"
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              exit={{ scale: 0 }}
              className="absolute -top-1.5 -right-1.5 inline-flex min-w-[18px] h-[18px] items-center justify-center rounded-full bg-gold px-1 text-[10px] font-bold text-white tabular-nums"
            >
              {unreadCount > 99 ? '99+' : unreadCount}
            </motion.span>
          ) : null}
        </AnimatePresence>
      </button>

      <AnimatePresence>
        {open ? (
          <motion.div
            initial={{ opacity: 0, y: 6, scale: 0.96 }}
            animate={{ opacity: 1, y: 0, scale: 1, transition: { duration: 0.16, ease: 'easeOut' } }}
            exit={{ opacity: 0, y: 4, scale: 0.96, transition: { duration: 0.12, ease: 'easeIn' } }}
            className="origin-top-right absolute right-0 mt-2 w-80 sm:w-96 rounded-xl border border-line bg-surface shadow-lift z-50 overflow-hidden"
          >
            <NotificationPanel
              notifications={notifications}
              error={error}
              onMarkAllRead={onMarkAllRead}
              onSelect={(notification) => {
                setOpen(false);
                onSelect(notification);
              }}
            />
          </motion.div>
        ) : null}
      </AnimatePresence>
    </div>
  );
}
