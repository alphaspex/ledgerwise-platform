/**
 * Inputs :
 *   - props: {} (no props)
 *   - useApp(): AppContextValue (from shared/AppContext.tsx)
 *   - usePolling(listEmailDrafts) -> EmailDraft[]; reviewEmail(messageId: number, body: EmailReviewRequest): Promise<OkResponse> (api/outreachApi.ts)
 *   - useAuthGuard(), useAsync, useToast hooks
 * Outputs :
 *   - JSX.Element (PageHeader 'Email review' with pending count; stack of EmailDraftCards; approve -> reviewEmail(id, { action: 'approve' }); edit -> { action: 'edit', body }; reject -> { action: 'reject' }; the card exits with animation and a toast; a 409 refreshes the list; Skeleton / EmptyState 'No drafts waiting' / ErrorState)
 * File explanation : Human gate: approve, edit or reject every first email before it is sent.
 */

import { useCallback, useEffect, useState } from 'react';
import { AnimatePresence } from 'framer-motion';
import { MailCheck } from 'lucide-react';
import { listEmailDrafts, reviewEmail } from '../api/outreachApi';
import { EmailDraftCard } from '../components/features/EmailDraftCard';
import { PageHeader } from '../components/layout/PageHeader';
import { EmptyState } from '../components/ui/EmptyState';
import { ErrorState } from '../components/ui/ErrorState';
import { Skeleton } from '../components/ui/Skeleton';
import { useAsync } from '../hooks/useAsync';
import { useAuthGuard } from '../hooks/useAuthGuard';
import { usePolling } from '../hooks/usePolling';
import { useToast } from '../hooks/useToast';
import { useApp } from '../shared/AppContext';
import type { EmailDraft, EmailReviewRequest } from '../shared/types';

export function EmailReviewPage() {
  useAuthGuard();
  const app = useApp();
  void app;
  const toast = useToast();

  const fetchDrafts = useCallback(() => listEmailDrafts(), []);
  const { data: drafts, loading, error, refresh } = usePolling<EmailDraft[]>(fetchDrafts);

  const reviewAction = useAsync((messageId: number, body: EmailReviewRequest) =>
    reviewEmail(messageId, body),
  );
  const [handledIds, setHandledIds] = useState<number[]>([]);

  useEffect(() => {
    if (!reviewAction.error) return;
    if (reviewAction.error.status === 409) {
      toast.info('Draft was already reviewed, refreshing');
      void refresh();
    } else {
      toast.error(reviewAction.error.detail);
    }
  }, [reviewAction.error, refresh, toast]);

  const handleAction = async (
    messageId: number,
    req: EmailReviewRequest,
    successText: string,
  ) => {
    const res = await reviewAction.run(messageId, req);
    if (res?.ok) {
      setHandledIds((prev) => [...prev, messageId]);
      toast.success(successText);
      await refresh();
    }
  };

  const handleApprove = (id: number) =>
    handleAction(id, { action: 'approve' }, 'Email approved for sending');
  const handleEdit = (id: number, body: string) =>
    handleAction(id, { action: 'edit', body }, 'Edited email approved for sending');
  const handleReject = (id: number) =>
    handleAction(id, { action: 'reject' }, 'Email draft rejected');

  if (loading && !drafts) {
    return (
      <div className="space-y-6">
        <PageHeader title="Email review" />
        <Skeleton variant="card" count={3} />
      </div>
    );
  }

  if (error && !drafts) {
    return (
      <div className="space-y-6">
        <PageHeader title="Email review" />
        <ErrorState message={error.detail} onRetry={() => void refresh()} />
      </div>
    );
  }

  const pending = (drafts ?? []).filter((d) => !handledIds.includes(d.message_id));

  return (
    <div className="space-y-6">
      <PageHeader
        title="Email review"
        subtitle={`${pending.length} ${pending.length === 1 ? 'draft' : 'drafts'} waiting`}
      />

      {pending.length === 0 ? (
        <EmptyState
          icon={MailCheck}
          title="No drafts waiting"
          message="All pending first-touch outreach drafts have been reviewed."
        />
      ) : (
        <div className="space-y-4">
          <AnimatePresence mode="popLayout">
            {pending.map((draft, idx) => (
              <EmailDraftCard
                key={draft.message_id}
                draft={draft}
                index={idx}
                busy={reviewAction.loading}
                onApprove={handleApprove}
                onEdit={handleEdit}
                onReject={handleReject}
              />
            ))}
          </AnimatePresence>
        </div>
      )}
    </div>
  );
}
