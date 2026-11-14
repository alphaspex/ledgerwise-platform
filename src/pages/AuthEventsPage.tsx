/**
 * Inputs :
 *   - props: {} (no props)
 *   - useApp(): AppContextValue (from shared/AppContext.tsx)
 *   - usePolling(() => listAuthEvents({ limit: 200 })) -> AuthEvent[] (api/authApi.ts)
 *   - useAuthGuard()
 * Outputs :
 *   - JSX.Element (PageHeader 'Security log' with note 'Kept for 30 days'; staggered Cards each showing event type pill, user id, IP, user agent, detail and time; read-only, no delete; Skeleton / EmptyState / ErrorState)
 * File explanation : Read-only auth event log visible to all members.
 */

import { useCallback } from 'react';
import { ScrollText } from 'lucide-react';
import { listAuthEvents } from '../api/authApi';
import { PageHeader } from '../components/layout/PageHeader';
import { Card } from '../components/ui/Card';
import { EmptyState } from '../components/ui/EmptyState';
import { ErrorState } from '../components/ui/ErrorState';
import { Skeleton } from '../components/ui/Skeleton';
import { StatusPill } from '../components/ui/StatusPill';
import { useAuthGuard } from '../hooks/useAuthGuard';
import { usePolling } from '../hooks/usePolling';
import { useApp } from '../shared/AppContext';
import type { AuthEvent, AuthEventType, StatusTone } from '../shared/types';

const AUTH_EVENT_LABEL: Record<AuthEventType, string> = {
  login_ok: 'Signed in',
  login_fail: 'Failed sign-in',
  password_change: 'Password changed',
  password_reset: 'Password reset',
  invite_sent: 'Invite sent',
  invite_accepted: 'Invite accepted',
  user_removed: 'User removed',
  logout: 'Signed out',
  rate_limited: 'Rate limited',
};

const AUTH_EVENT_TONE: Record<AuthEventType, StatusTone> = {
  login_ok: 'success',
  invite_accepted: 'success',
  login_fail: 'danger',
  rate_limited: 'danger',
  user_removed: 'danger',
  password_change: 'info',
  password_reset: 'info',
  invite_sent: 'info',
  logout: 'neutral',
};

export function AuthEventsPage() {
  useAuthGuard();
  const app = useApp();
  void app;

  const fetchEvents = useCallback(() => listAuthEvents({ limit: 200 }), []);
  const { data: events, loading, error, refresh } = usePolling<AuthEvent[]>(fetchEvents);

  if (loading && !events) {
    return (
      <div className="space-y-6">
        <PageHeader title="Security log" subtitle="Kept for 30 days" />
        <Skeleton variant="card" count={4} />
      </div>
    );
  }

  if (error && !events) {
    return (
      <div className="space-y-6">
        <PageHeader title="Security log" subtitle="Kept for 30 days" />
        <ErrorState message={error.detail} onRetry={() => void refresh()} />
      </div>
    );
  }

  const list = events ?? [];

  return (
    <div className="space-y-6">
      <PageHeader title="Security log" subtitle="Kept for 30 days" />

      {list.length === 0 ? (
        <EmptyState
          icon={ScrollText}
          title="No security events yet"
          message="Authentication events from the past 30 days will appear here."
        />
      ) : (
        <div className="grid gap-4 sm:grid-cols-2">
          {list.map((ev, idx) => {
            const timeText = new Date(ev.created_at).toLocaleString();

            return (
              <Card key={ev.id} index={idx} className="space-y-2.5 text-xs">
                <div className="flex items-center justify-between gap-2">
                  <StatusPill
                    label={AUTH_EVENT_LABEL[ev.event]}
                    tone={AUTH_EVENT_TONE[ev.event]}
                  />
                  <span className="text-navy-mute tabular-nums">{timeText}</span>
                </div>
                <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-navy-soft">
                  <span>User ID: {ev.user_id ?? 'N/A'}</span>
                  <span>IP: {ev.ip ?? 'Unknown'}</span>
                </div>
                {ev.user_agent ? (
                  <div className="text-navy-mute truncate">{ev.user_agent}</div>
                ) : null}
                {ev.detail ? (
                  <div className="rounded-md bg-canvas/70 px-2.5 py-1.5 text-navy break-words">
                    {ev.detail}
                  </div>
                ) : null}
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}
