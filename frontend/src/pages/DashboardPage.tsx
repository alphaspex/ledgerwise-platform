/**
 * Inputs :
 *   - props: {} (no props)
 *   - useApp(): AppContextValue (from shared/AppContext.tsx)
 *   - usePolling(getDashboard) -> DashboardSummary (api/dashboardApi.ts)
 *   - useAuthGuard()
 * Outputs :
 *   - JSX.Element (PageHeader 'Dashboard' and four SummaryBlocks: Research (approved / pending / needs review) -> goTo('research'); Emails (pending review / sent / rejected) -> goTo('email_review'); Conversations (auto / needs human / taken over) -> goTo('conversations'); Bookings (upcoming) with unread notifications count -> goTo('bookings'); Skeleton / ErrorState)
 * File explanation : Home screen with summary numbers.
 */

import { useCallback } from 'react';
import { CalendarDays, MailCheck, MessagesSquare, Search } from 'lucide-react';
import { getDashboard } from '../api/dashboardApi';
import { SummaryBlock } from '../components/features/SummaryBlock';
import { PageHeader } from '../components/layout/PageHeader';
import { ErrorState } from '../components/ui/ErrorState';
import { Skeleton } from '../components/ui/Skeleton';
import { useAuthGuard } from '../hooks/useAuthGuard';
import { usePolling } from '../hooks/usePolling';
import { useApp } from '../shared/AppContext';
import type { DashboardSummary } from '../shared/types';

export function DashboardPage() {
  useAuthGuard();
  const { goTo } = useApp();

  const fetchDashboard = useCallback(() => getDashboard(), []);
  const { data: summary, loading, error, refresh } = usePolling<DashboardSummary>(fetchDashboard);

  if (loading && !summary) {
    return (
      <div className="space-y-6">
        <PageHeader title="Dashboard" />
        <div className="grid gap-4 sm:grid-cols-2">
          <Skeleton variant="card" count={2} />
          <Skeleton variant="card" count={2} />
        </div>
      </div>
    );
  }

  if (error && !summary) {
    return (
      <div className="space-y-6">
        <PageHeader title="Dashboard" />
        <ErrorState message={error.detail} onRetry={() => void refresh()} />
      </div>
    );
  }

  if (!summary) {
    return null;
  }

  return (
    <div className="space-y-6">
      <PageHeader title="Dashboard" subtitle="Live pipeline and outreach overview" />

      <div className="grid gap-4 sm:grid-cols-2">
        <SummaryBlock
          index={0}
          title="Research"
          icon={Search}
          onClick={() => goTo('research')}
          stats={[
            { label: 'Approved', value: summary.research.approved, tone: 'success' },
            { label: 'Pending', value: summary.research.pending, tone: 'info' },
            { label: 'Needs review', value: summary.research.needs_human_review, tone: 'warning' },
          ]}
        />

        <SummaryBlock
          index={1}
          title="Emails"
          icon={MailCheck}
          onClick={() => goTo('email_review')}
          stats={[
            { label: 'Pending review', value: summary.emails.pending_review, tone: 'warning' },
            { label: 'Sent', value: summary.emails.sent, tone: 'success' },
            { label: 'Rejected', value: summary.emails.rejected, tone: 'danger' },
          ]}
        />

        <SummaryBlock
          index={2}
          title="Conversations"
          icon={MessagesSquare}
          onClick={() => goTo('conversations')}
          stats={[
            { label: 'Agent active', value: summary.conversations.auto, tone: 'info' },
            { label: 'Needs human', value: summary.conversations.needs_human, tone: 'warning' },
            { label: 'Taken over', value: summary.conversations.human_taken_over, tone: 'success' },
          ]}
        />

        <SummaryBlock
          index={3}
          title="Bookings"
          icon={CalendarDays}
          onClick={() => goTo('bookings')}
          stats={[
            { label: 'Upcoming', value: summary.bookings.upcoming, tone: 'info' },
            {
              label: 'Unread alerts',
              value: summary.notifications.unread,
              tone: summary.notifications.unread > 0 ? 'warning' : 'neutral',
            },
          ]}
        />
      </div>
    </div>
  );
}
