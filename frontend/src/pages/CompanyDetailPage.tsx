/**
 * Inputs :
 *   - props: {} (no props)
 *   - useApp(): AppContextValue (from shared/AppContext.tsx)
 *   - context.selectedCompanyId: number | null
 *   - usePolling(() => getCompany(id)) -> CompanyDetail (api/researchApi.ts)
 *   - useAuthGuard()
 * Outputs :
 *   - JSX.Element (company detail; 404 or missing selectedCompanyId returns to 'companies'; Skeleton / ErrorState for other failures)
 * File explanation : Shows one company's research evidence, verified memory, contact details, and status; stale saved company IDs return to the company list.
 */

import { useCallback, useEffect } from 'react';
import { getCompany } from '../api/researchApi';
import { FactList } from '../components/features/FactList';
import { ReasonList } from '../components/features/ReasonList';
import { PageHeader } from '../components/layout/PageHeader';
import { Card } from '../components/ui/Card';
import { ErrorState } from '../components/ui/ErrorState';
import { ScoreBadge } from '../components/ui/ScoreBadge';
import { Skeleton } from '../components/ui/Skeleton';
import { StatusPill } from '../components/ui/StatusPill';
import { useAuthGuard } from '../hooks/useAuthGuard';
import { usePolling } from '../hooks/usePolling';
import { useApp } from '../shared/AppContext';
import {
  COMPANY_STATUS_LABEL,
  COMPANY_STATUS_TONE,
  EMAIL_STATUS_LABEL,
  EMAIL_STATUS_TONE,
} from '../shared/constants';
import type { CompanyDetail } from '../shared/types';

export function CompanyDetailPage() {
  useAuthGuard();
  const { selectedCompanyId, goTo } = useApp();

  useEffect(() => {
    if (selectedCompanyId === null) {
      goTo('companies');
    }
  }, [selectedCompanyId, goTo]);

  const fetchCompany = useCallback(() => {
    if (selectedCompanyId === null) {
      return Promise.reject(new Error('No company selected'));
    }
    return getCompany(selectedCompanyId);
  }, [selectedCompanyId]);

  const { data: company, loading, error, refresh } = usePolling<CompanyDetail>(fetchCompany, {
    enabled: selectedCompanyId !== null,
  });

  useEffect(() => {
    if (error?.status === 404) goTo('companies');
  }, [error, goTo]);

  if (selectedCompanyId === null) {
    return null;
  }

  if (loading && !company) {
    return (
      <div className="space-y-6">
        <PageHeader title="Company" onBack={() => goTo('companies')} />
        <Skeleton variant="card" count={3} />
      </div>
    );
  }

  if (error && !company) {
    return (
      <div className="space-y-6">
        <PageHeader title="Company" onBack={() => goTo('companies')} />
        <ErrorState message={error.detail} onRetry={() => void refresh()} />
      </div>
    );
  }

  if (!company) {
    return null;
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title={company.domain}
        subtitle={`Run #${company.run_id}`}
        onBack={() => goTo('companies')}
        actions={
          <div className="flex flex-wrap items-center gap-2">
            <StatusPill
              label={COMPANY_STATUS_LABEL[company.status]}
              tone={COMPANY_STATUS_TONE[company.status]}
            />
            <StatusPill
              label={EMAIL_STATUS_LABEL[company.email_status]}
              tone={EMAIL_STATUS_TONE[company.email_status]}
            />
            <ScoreBadge score={company.score} />
          </div>
        }
      />

      {company.do_not_contact ? (
        <div
          role="alert"
          className="rounded-xl border border-bad/40 bg-bad/10 px-4 py-3 text-sm font-medium text-bad"
        >
          Do not contact: this company requested not to be contacted.
        </div>
      ) : null}

      <Card className="space-y-1.5 text-sm">
        <div className="font-semibold text-navy">Contact</div>
        <div className="text-navy-soft">Email: {company.contact_email ?? 'None'}</div>
        <div className="text-navy-soft">Role: {company.contact_role ?? 'Unknown'}</div>
        <div className="text-navy-mute text-xs">Source: {company.contact_source ?? 'N/A'}</div>
      </Card>

      {company.research_data ? (
        <ReasonList
          reasons={company.research_data.reasons}
          sources={company.research_data.sources}
        />
      ) : (
        <ReasonList reasons={company.reasons_preview} sources={[]} />
      )}

      {company.memory ? (
        <Card>
          <FactList facts={company.memory.facts} />
        </Card>
      ) : null}
    </div>
  );
}
