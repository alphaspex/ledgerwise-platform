/**
 * Inputs :
 *   - props: { notifications: Notification[]; error: ApiError | null; onMarkAllRead: () => void; onSelect: (notification: Notification) => void }
 *   - NOTIFICATION_REASON_LABEL (from shared/constants.ts)
 * Outputs :
 *   - JSX.Element (scrollable list, newest first; each row: reason label, domain, body text (plain text), time, unread dot; header with a 'Mark all read' Button; EmptyState text when the list is empty)
 * File explanation : Content of the bell dropdown. Shows polling failures separately from an empty result and retains stale notifications.
 */

import { Bell, CheckCheck } from 'lucide-react';
import type { ApiError } from '../../api/client';
import { NOTIFICATION_REASON_LABEL } from '../../shared/constants';
import type { Notification } from '../../shared/types';
import { Button } from '../ui/Button';
import { EmptyState } from '../ui/EmptyState';

export function NotificationPanel({
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
  const sorted = [...notifications].sort(
    (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime(),
  );
  const hasUnread = sorted.some((n) => !n.read);

  return (
    <div className="flex flex-col max-h-96 bg-surface">
      <div className="flex items-center justify-between gap-2 px-4 py-3 border-b border-line">
        <span className="text-sm font-semibold text-navy">Notifications</span>
        <Button
          variant="ghost"
          icon={CheckCheck}
          onClick={onMarkAllRead}
          disabled={!hasUnread}
        >
          Mark all read
        </Button>
      </div>

      {error ? (
        <div role="alert" className="border-b border-line bg-bad/5 px-4 py-3 text-xs text-bad">
          Notifications could not be refreshed: {error.detail}
          {error.status > 0 ? ' (HTTP ' + error.status + ')' : ' Check the API connection.'}
        </div>
      ) : null}

      {sorted.length === 0 && !error ? (
        <div className="p-3">
          <EmptyState
            icon={Bell}
            title="All caught up"
            message="No notifications yet."
          />
        </div>
      ) : sorted.length > 0 ? (
        <div className="overflow-y-auto divide-y divide-line">
          {sorted.map((n) => {
            const timeText = new Date(n.created_at).toLocaleString(undefined, {
              month: 'short',
              day: 'numeric',
              hour: '2-digit',
              minute: '2-digit',
            });

            return (
              <button
                key={n.id}
                type="button"
                onClick={() => onSelect(n)}
                className="w-full text-left px-4 py-3 hover:bg-canvas/70 transition-colors flex items-start gap-3"
              >
                <span
                  aria-hidden="true"
                  className={`mt-1.5 h-2 w-2 rounded-full shrink-0 ${
                    n.read ? 'bg-transparent' : 'bg-gold'
                  }`}
                />
                <div className="min-w-0 flex-1 space-y-0.5">
                  <div className="flex items-center justify-between gap-2">
                    <span className="text-xs font-semibold text-navy truncate">
                      {NOTIFICATION_REASON_LABEL[n.reason]} · {n.domain}
                    </span>
                    <span className="text-[11px] text-navy-mute shrink-0 tabular-nums">
                      {timeText}
                    </span>
                  </div>
                  {n.body ? (
                    <p className="text-xs text-navy-soft line-clamp-2 break-words">{n.body}</p>
                  ) : null}
                </div>
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}
