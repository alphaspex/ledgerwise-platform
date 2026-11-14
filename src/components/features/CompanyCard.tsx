/**
 * Inputs :
 *   - props: { company: CompanySummary; index: number; onOpen: (id: number) => void }
 *   - COMPANY_STATUS_LABEL, COMPANY_STATUS_TONE, EMAIL_STATUS_LABEL, EMAIL_STATUS_TONE (from shared/constants.ts)
 * Outputs :
 *   - JSX.Element (interactive Card with domain, ScoreBadge, company StatusPill, email-status StatusPill, up to 2 reasons_preview texts; click calls onOpen(company.id))
 * File explanation : One company in the company grid.
 */

import {
  COMPANY_STATUS_LABEL,
  COMPANY_STATUS_TONE,
  EMAIL_STATUS_LABEL,
  EMAIL_STATUS_TONE,
} from '../../shared/constants';
import type { CompanySummary } from '../../shared/types';
import { Card } from '../ui/Card';
import { ScoreBadge } from '../ui/ScoreBadge';
import { StatusPill } from '../ui/StatusPill';

export function CompanyCard({
  company,
  index,
  onOpen,
}: {
  company: CompanySummary;
  index: number;
  onOpen: (id: number) => void;
}) {
  const previews = company.reasons_preview.slice(0, 2);

  return (
    <Card
      interactive
      index={index}
      onClick={() => onOpen(company.id)}
      className="flex flex-col gap-3"
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0 space-y-1.5">
          <h3 className="text-base font-semibold text-navy truncate">{company.domain}</h3>
          <div className="flex flex-wrap items-center gap-1.5">
            <StatusPill
              label={COMPANY_STATUS_LABEL[company.status]}
              tone={COMPANY_STATUS_TONE[company.status]}
            />
            <StatusPill
              label={EMAIL_STATUS_LABEL[company.email_status]}
              tone={EMAIL_STATUS_TONE[company.email_status]}
            />
          </div>
        </div>
        <ScoreBadge score={company.score} />
      </div>

      {previews.length > 0 ? (
        <ul className="space-y-1 text-xs text-navy-soft pt-1 border-t border-line">
          {previews.map((reason, idx) => (
            <li key={idx} className="line-clamp-2">
              {reason.text}
            </li>
          ))}
        </ul>
      ) : null}
    </Card>
  );
}
