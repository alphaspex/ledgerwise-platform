/**
 * Inputs :
 *   - props: { status: CompanyStatus | 'all'; onStatusChange: (s: CompanyStatus | 'all') => void; query: string; onQueryChange: (q: string) => void; sort: 'score' | 'recent'; onSortChange: (s: 'score' | 'recent') => void }
 *   - COMPANY_STATUS_LABEL (from shared/constants.ts)
 * Outputs :
 *   - JSX.Element (scrollable row of status filter pills with 'All', a search TextInput for the domain, and a Score / Recent toggle)
 * File explanation : Filter bar of the Companies page. Pure controlled component: filtering itself happens in CompaniesPage.
 */

import { COMPANY_STATUS_LABEL } from '../../shared/constants';
import type { CompanyStatus } from '../../shared/types';
import { TextInput } from '../ui/TextInput';

const STATUS_KEYS = Object.keys(COMPANY_STATUS_LABEL) as CompanyStatus[];

export function CompanyFilters({
  status,
  onStatusChange,
  query,
  onQueryChange,
  sort,
  onSortChange,
}: {
  status: CompanyStatus | 'all';
  onStatusChange: (s: CompanyStatus | 'all') => void;
  query: string;
  onQueryChange: (q: string) => void;
  sort: 'score' | 'recent';
  onSortChange: (s: 'score' | 'recent') => void;
}) {
  return (
    <div className="space-y-3 mb-6">
      <div className="flex items-center gap-2 overflow-x-auto pb-1">
        <button
          type="button"
          onClick={() => onStatusChange('all')}
          className={`rounded-full px-3 py-1 text-xs font-medium whitespace-nowrap shrink-0 border transition-colors ${
            status === 'all'
              ? 'bg-navy text-white border-navy'
              : 'bg-surface text-navy-soft border-line hover:bg-canvas'
          }`}
        >
          All
        </button>
        {STATUS_KEYS.map((key) => (
          <button
            key={key}
            type="button"
            onClick={() => onStatusChange(key)}
            className={`rounded-full px-3 py-1 text-xs font-medium whitespace-nowrap shrink-0 border transition-colors ${
              status === key
                ? 'bg-navy text-white border-navy'
                : 'bg-surface text-navy-soft border-line hover:bg-canvas'
            }`}
          >
            {COMPANY_STATUS_LABEL[key]}
          </button>
        ))}
      </div>

      <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-3">
        <div className="flex-1">
          <TextInput
            label="Search domain"
            value={query}
            onChange={onQueryChange}
            placeholder="Filter by domain..."
          />
        </div>

        <div className="inline-flex items-center rounded-lg border border-line bg-surface p-1 shrink-0 self-start sm:self-end">
          <button
            type="button"
            onClick={() => onSortChange('score')}
            className={`px-3 py-1.5 rounded-md text-xs font-medium transition-colors whitespace-nowrap ${
              sort === 'score' ? 'bg-slate-gradient text-white' : 'text-navy-soft hover:text-navy'
            }`}
          >
            Score
          </button>
          <button
            type="button"
            onClick={() => onSortChange('recent')}
            className={`px-3 py-1.5 rounded-md text-xs font-medium transition-colors whitespace-nowrap ${
              sort === 'recent' ? 'bg-slate-gradient text-white' : 'text-navy-soft hover:text-navy'
            }`}
          >
            Recent
          </button>
        </div>
      </div>
    </div>
  );
}
