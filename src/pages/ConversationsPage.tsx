/**
 * Inputs :
 *   - props: {} (no props)
 *   - useApp(): AppContextValue (from shared/AppContext.tsx)
 *   - usePolling(listThreads) -> ThreadSummary[] (api/outreachApi.ts)
 *   - useAuthGuard()
 * Outputs :
 *   - JSX.Element (PageHeader 'Conversations'; threads needing a human sorted first, then newest; ThreadCards; click -> goTo('chat', company_id); Skeleton / EmptyState 'No conversations yet' / ErrorState)
 * File explanation : List of all conversations with prospects.
 */

import { useCallback, useMemo } from 'react';
import { MessagesSquare } from 'lucide-react';
import { listThreads } from '../api/outreachApi';
import { ThreadCard } from '../components/features/ThreadCard';
import { PageHeader } from '../components/layout/PageHeader';
import { EmptyState } from '../components/ui/EmptyState';
import { ErrorState } from '../components/ui/ErrorState';
import { Skeleton } from '../components/ui/Skeleton';
import { useAuthGuard } from '../hooks/useAuthGuard';
import { usePolling } from '../hooks/usePolling';
import { useApp } from '../shared/AppContext';
import type { ThreadSummary } from '../shared/types';

export function ConversationsPage() {
  useAuthGuard();
  const { goTo } = useApp();

  const fetchThreads = useCallback(() => listThreads(), []);
  const { data: threads, loading, error, refresh } = usePolling<ThreadSummary[]>(fetchThreads);

  const sorted = useMemo(() => {
    const list = [...(threads ?? [])];
    return list.sort((a, b) => {
      const aNeeds = a.thread_state === 'needs_human' ? 0 : 1;
      const bNeeds = b.thread_state === 'needs_human' ? 0 : 1;
      if (aNeeds !== bNeeds) return aNeeds - bNeeds;
      return new Date(b.last_message_at).getTime() - new Date(a.last_message_at).getTime();
    });
  }, [threads]);

  if (loading && !threads) {
    return (
      <div className="space-y-6">
        <PageHeader title="Conversations" />
        <Skeleton variant="card" count={3} />
      </div>
    );
  }

  if (error && !threads) {
    return (
      <div className="space-y-6">
        <PageHeader title="Conversations" />
        <ErrorState message={error.detail} onRetry={() => void refresh()} />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Conversations"
        subtitle="Threads needing human attention appear at the top"
      />

      {sorted.length === 0 ? (
        <EmptyState
          icon={MessagesSquare}
          title="No conversations yet"
          message="Replies from prospects and agent follow-ups will show up here."
        />
      ) : (
        <div className="grid gap-4 sm:grid-cols-2">
          {sorted.map((thread, idx) => (
            <ThreadCard
              key={thread.company_id}
              thread={thread}
              index={idx}
              onOpen={(companyId) => goTo('chat', companyId)}
            />
          ))}
        </div>
      )}
    </div>
  );
}
