/**
 * Inputs :
 *   - props: {} (no props)
 *   - useApp(): AppContextValue (from shared/AppContext.tsx)
 *   - usePolling(getDashboard) -> DashboardSummary (api/dashboardApi.ts)
 *   - useAuthGuard()
 * Outputs :
 *   - JSX.Element (four pipeline SummaryBlocks plus token/search usage totals, estimated USD cost, and per-module breakdown; Skeleton / ErrorState)
 * File explanation : Home screen with pipeline counts and persisted AI usage and cost totals.
 */

import { useCallback } from 'react';
import { CalendarDays, MailCheck, MessagesSquare, Search } from 'lucide-react';
import { getDashboard } from '../api/dashboardApi';
import { SummaryBlock } from '../components/features/SummaryBlock';
import { Card } from '../components/ui/Card';
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

  const usageCostLabel = summary.usage.cost_complete && summary.usage.cost_usd !== null
    ? `${summary.usage.cost_usd.toFixed(6)}`
    : 'Unavailable (pricing not set for all calls)';

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

      <Card className="space-y-4">
        <div>
          <h2 className="text-base font-semibold text-navy">AI usage</h2>
          <p className="text-xs text-navy-mute">Persisted model calls across all modules.</p>
        </div>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
          <div><div className="text-xs text-navy-mute">Calls</div><div className="text-lg font-semibold text-navy">{summary.usage.calls.toLocaleString()}</div></div>
          <div><div className="text-xs text-navy-mute">Input tokens</div><div className="text-lg font-semibold text-navy">{summary.usage.input_tokens.toLocaleString()}</div></div>
          <div><div className="text-xs text-navy-mute">Output tokens</div><div className="text-lg font-semibold text-navy">{summary.usage.output_tokens.toLocaleString()}</div></div>
          <div><div className="text-xs text-navy-mute">Reasoning tokens</div><div className="text-lg font-semibold text-navy">{summary.usage.reasoning_tokens.toLocaleString()}</div></div>
          <div><div className="text-xs text-navy-mute">Web searches</div><div className="text-lg font-semibold text-navy">{summary.usage.searches.toLocaleString()}</div></div>
          <div><div className="text-xs text-navy-mute">Total tokens</div><div className="text-lg font-semibold text-navy">{summary.usage.total_tokens.toLocaleString()}</div></div>
          <div><div className="text-xs text-navy-mute">Estimated cost</div><div className="text-sm font-semibold text-navy">{usageCostLabel}</div></div>
        </div>
        <div className="space-y-2 border-t border-line pt-3">
          <h3 className="text-sm font-semibold text-navy">By module</h3>
          {Object.entries(summary.usage.by_module).length ? Object.entries(summary.usage.by_module).map(([module, usage]) => (
            <div key={module} className="flex items-center justify-between gap-3 text-sm">
              <span className="capitalize text-navy-soft">{module}</span>
              <span className="text-navy-mute">{usage.calls.toLocaleString()} calls · {usage.total_tokens.toLocaleString()} tokens</span>
            </div>
          )) : <p className="text-xs text-navy-mute">No model usage recorded yet.</p>}
        </div>
      </Card>
    </div>
  );
}
