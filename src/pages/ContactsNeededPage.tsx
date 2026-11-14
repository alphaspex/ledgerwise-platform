/**
 * Inputs :
 *   - props: {} (no props)
 *   - useApp(): AppContextValue (from shared/AppContext.tsx)
 *   - usePolling(() => listCompanies({ status: ['approved', 'human_approved'], has_contact: false })) -> CompanySummary[]; saveContact(companyId: number, body: ContactRequest): Promise<CompanySummary> (api/researchApi.ts, api/outreachApi.ts)
 *   - useAuthGuard(), useAsync, useToast hooks
 * Outputs :
 *   - JSX.Element (PageHeader 'Contacts needed'; one Card per company with domain, ScoreBadge and a ContactForm; on save the card leaves the list and a toast says 'Contact saved, a draft will be written'; a 422 detail (generic inbox) is shown inline on that card; Skeleton / EmptyState / ErrorState)
 * File explanation : Approved companies that still need a named contact before an email can be drafted.
 */

import { useCallback, useEffect, useRef, useState } from 'react';
import { UserPlus } from 'lucide-react';
import { saveContact } from '../api/outreachApi';
import { listCompanies } from '../api/researchApi';
import { ContactForm } from '../components/features/ContactForm';
import { PageHeader } from '../components/layout/PageHeader';
import { Card } from '../components/ui/Card';
import { EmptyState } from '../components/ui/EmptyState';
import { ErrorState } from '../components/ui/ErrorState';
import { ScoreBadge } from '../components/ui/ScoreBadge';
import { Skeleton } from '../components/ui/Skeleton';
import { useAsync } from '../hooks/useAsync';
import { useAuthGuard } from '../hooks/useAuthGuard';
import { usePolling } from '../hooks/usePolling';
import { useToast } from '../hooks/useToast';
import { useApp } from '../shared/AppContext';
import type { CompanySummary, ContactRequest } from '../shared/types';

export function ContactsNeededPage() {
  useAuthGuard();
  const app = useApp();
  void app;
  const toast = useToast();

  const fetchNeeded = useCallback(
    () => listCompanies({ status: ['approved', 'human_approved'], has_contact: false }),
    [],
  );
  const { data: companies, loading, error, refresh } = usePolling<CompanySummary[]>(fetchNeeded);

  const saveAction = useAsync((companyId: number, body: ContactRequest) =>
    saveContact(companyId, body),
  );
  const [savedIds, setSavedIds] = useState<number[]>([]);
  const [cardErrors, setCardErrors] = useState<Record<number, string>>({});
  const lastCompanyIdRef = useRef<number | null>(null);

  useEffect(() => {
    if (!saveAction.error) return;
    const cid = lastCompanyIdRef.current;
    if (saveAction.error.status === 422 && cid !== null) {
      setCardErrors((prev) => ({ ...prev, [cid]: saveAction.error!.detail }));
    } else {
      toast.error(saveAction.error.detail);
    }
  }, [saveAction.error, toast]);

  const handleSave = async (companyId: number, body: ContactRequest) => {
    lastCompanyIdRef.current = companyId;
    setCardErrors((prev) => {
      const next = { ...prev };
      delete next[companyId];
      return next;
    });
    const res = await saveAction.run(companyId, body);
    if (res) {
      setSavedIds((prev) => [...prev, companyId]);
      toast.success('Contact saved, a draft will be written');
      await refresh();
    }
  };

  if (loading && !companies) {
    return (
      <div className="space-y-6">
        <PageHeader title="Contacts needed" />
        <Skeleton variant="card" count={3} />
      </div>
    );
  }

  if (error && !companies) {
    return (
      <div className="space-y-6">
        <PageHeader title="Contacts needed" />
        <ErrorState message={error.detail} onRetry={() => void refresh()} />
      </div>
    );
  }

  const visible = (companies ?? []).filter((c) => !savedIds.includes(c.id));

  return (
    <div className="space-y-6">
      <PageHeader
        title="Contacts needed"
        subtitle="Add a named decision-maker so outreach drafts can be generated"
      />

      {visible.length === 0 ? (
        <EmptyState
          icon={UserPlus}
          title="No contacts needed"
          message="All approved companies already have a named contact."
        />
      ) : (
        <div className="grid gap-4 sm:grid-cols-2">
          {visible.map((company, idx) => (
            <Card key={company.id} index={idx} className="space-y-4">
              <div className="flex items-center justify-between gap-3">
                <h3 className="text-base font-semibold text-navy truncate">{company.domain}</h3>
                <ScoreBadge score={company.score} />
              </div>

              <ContactForm
                initialEmail={company.contact_email}
                initialRole={company.contact_role}
                busy={saveAction.loading}
                onSubmit={(body) => handleSave(company.id, body)}
              />

              {cardErrors[company.id] ? (
                <p className="text-xs text-bad" role="alert">
                  {cardErrors[company.id]}
                </p>
              ) : null}
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
