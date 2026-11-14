/**
 * Inputs :
 *   - props: {} (no props)
 *   - useApp(): AppContextValue (from shared/AppContext.tsx)
 *   - usePolling(() => listCompanies()) -> CompanySummary[] (api/researchApi.ts)
 *   - useAuthGuard()
 * Outputs :
 *   - JSX.Element (PageHeader 'Companies' with count; CompanyFilters; responsive grid of CompanyCards filtered client-side by status and domain text and sorted by score desc or created_at desc; card click -> goTo('company_detail', id); Skeleton / EmptyState / ErrorState)
 * File explanation : Grid of all researched companies with score and status.
 */

import { useCallback, useMemo, useState } from 'react';
import { Building2 } from 'lucide-react';
import { listCompanies } from '../api/researchApi';
import { CompanyCard } from '../components/features/CompanyCard';
import { CompanyFilters } from '../components/features/CompanyFilters';
import { PageHeader } from '../components/layout/PageHeader';
import { EmptyState } from '../components/ui/EmptyState';
import { ErrorState } from '../components/ui/ErrorState';
import { Skeleton } from '../components/ui/Skeleton';
import { useAuthGuard } from '../hooks/useAuthGuard';
import { usePolling } from '../hooks/usePolling';
import { useApp } from '../shared/AppContext';
import type { CompanyStatus, CompanySummary } from '../shared/types';

export function CompaniesPage() {
  useAuthGuard();
  const { goTo } = useApp();

  const fetchCompanies = useCallback(() => listCompanies(), []);
  const { data: companies, loading, error, refresh } = usePolling<CompanySummary[]>(fetchCompanies);

  const [status, setStatus] = useState<CompanyStatus | 'all'>('all');
  const [query, setQuery] = useState('');
  const [sort, setSort] = useState<'score' | 'recent'>('score');

  const filtered = useMemo(() => {
    const list = companies ?? [];
    const q = query.trim().toLowerCase();
    return list
      .filter((c) => (status === 'all' ? true : c.status === status))
      .filter((c) => (q ? c.domain.toLowerCase().includes(q) : true))
      .sort((a, b) => {
        if (sort === 'score') {
          return (b.score ?? -1) - (a.score ?? -1);
        }
        return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
      });
  }, [companies, status, query, sort]);

  if (loading && !companies) {
    return (
      <div className="space-y-6">
        <PageHeader title="Companies" />
        <Skeleton variant="card" count={3} />
      </div>
    );
  }

  if (error && !companies) {
    return (
      <div className="space-y-6">
        <PageHeader title="Companies" />
        <ErrorState message={error.detail} onRetry={() => void refresh()} />
      </div>
    );
  }

  const totalCount = (companies ?? []).length;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Companies"
        subtitle={`${filtered.length} of ${totalCount} ${totalCount === 1 ? 'company' : 'companies'}`}
      />

      <CompanyFilters
        status={status}
        onStatusChange={setStatus}
        query={query}
        onQueryChange={setQuery}
        sort={sort}
        onSortChange={setSort}
      />

      {filtered.length === 0 ? (
        <EmptyState
          icon={Building2}
          title={totalCount === 0 ? 'No companies researched yet' : 'No matching companies'}
          message={
            totalCount === 0
              ? 'Start a research run to discover and qualify companies.'
              : 'Try clearing or adjusting your status and domain filters.'
          }
          action={
            totalCount === 0
              ? { label: 'Go to Research', onClick: () => goTo('research') }
              : {
                  label: 'Clear filters',
                  onClick: () => {
                    setStatus('all');
                    setQuery('');
                  },
                }
          }
        />
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {filtered.map((company, idx) => (
            <CompanyCard
              key={company.id}
              company={company}
              index={idx}
              onOpen={(id) => goTo('company_detail', id)}
            />
          ))}
        </div>
      )}
    </div>
  );
}
