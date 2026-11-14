/**
 * Inputs :
 *   - props: {} (no props)
 *   - useApp(): AppContextValue (from shared/AppContext.tsx)
 *   - usePolling(() => listCompanies({ status: ['needs_human_review'] })) -> CompanySummary[]; reviewCompany(body: ReviewCompanyRequest): Promise<OkResponse> (api/researchApi.ts)
 *   - useAuthGuard(), useAsync, useToast hooks
 * Outputs :
 *   - JSX.Element (PageHeader 'Human review'; grid of HumanReviewCards; after a decision the card leaves the list with an exit animation and a toast; Skeleton / EmptyState 'Nothing to review' / ErrorState)
 * File explanation : Approve or reject companies whose website could not be checked automatically.
 */

import { useCallback, useEffect, useState } from 'react';
import { AnimatePresence } from 'framer-motion';
import { ShieldCheck } from 'lucide-react';
import { listCompanies, reviewCompany } from '../api/researchApi';
import { HumanReviewCard } from '../components/features/HumanReviewCard';
import { PageHeader } from '../components/layout/PageHeader';
import { EmptyState } from '../components/ui/EmptyState';
import { ErrorState } from '../components/ui/ErrorState';
import { Skeleton } from '../components/ui/Skeleton';
import { useAsync } from '../hooks/useAsync';
import { useAuthGuard } from '../hooks/useAuthGuard';
import { usePolling } from '../hooks/usePolling';
import { useToast } from '../hooks/useToast';
import { useApp } from '../shared/AppContext';
import type { CompanySummary, ReviewCompanyRequest } from '../shared/types';

export function HumanReviewPage() {
  useAuthGuard();
  const app = useApp();
  void app;
  const toast = useToast();

  const fetchReview = useCallback(() => listCompanies({ status: ['needs_human_review'] }), []);
  const { data: companies, loading, error, refresh } = usePolling<CompanySummary[]>(fetchReview);

  const reviewAction = useAsync((body: ReviewCompanyRequest) => reviewCompany(body));
  const [handledIds, setHandledIds] = useState<number[]>([]);

  useEffect(() => {
    if (!reviewAction.error) return;
    if (reviewAction.error.status === 409) {
      toast.info('Company was already reviewed, refreshing');
      void refresh();
    } else {
      toast.error(reviewAction.error.detail);
    }
  }, [reviewAction.error, refresh, toast]);

  const handleDecision = async (
    companyId: number,
    decision: 'human_approved' | 'human_rejected',
  ) => {
    const res = await reviewAction.run({ company_id: companyId, decision });
    if (res?.ok) {
      setHandledIds((prev) => [...prev, companyId]);
      toast.success(
        decision === 'human_approved' ? 'Company approved by team' : 'Company rejected by team',
      );
      await refresh();
    }
  };

  if (loading && !companies) {
    return (
      <div className="space-y-6">
        <PageHeader title="Human review" />
        <Skeleton variant="card" count={3} />
      </div>
    );
  }

  if (error && !companies) {
    return (
      <div className="space-y-6">
        <PageHeader title="Human review" />
        <ErrorState message={error.detail} onRetry={() => void refresh()} />
      </div>
    );
  }

  const pending = (companies ?? []).filter((c) => !handledIds.includes(c.id));

  return (
    <div className="space-y-6">
      <PageHeader
        title="Human review"
        subtitle={`${pending.length} ${pending.length === 1 ? 'company' : 'companies'} waiting`}
      />

      {pending.length === 0 ? (
        <EmptyState
          icon={ShieldCheck}
          title="Nothing to review"
          message="All flagged companies have been reviewed."
        />
      ) : (
        <div className="grid gap-4 sm:grid-cols-2">
          <AnimatePresence mode="popLayout">
            {pending.map((company, idx) => (
              <HumanReviewCard
                key={company.id}
                company={company}
                index={idx}
                busy={reviewAction.loading}
                onDecision={handleDecision}
              />
            ))}
          </AnimatePresence>
        </div>
      )}
    </div>
  );
}
