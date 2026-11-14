/**
 * Inputs :
 *   - props: { company: CompanySummary; index: number; busy: boolean; onDecision: (companyId: number, decision: 'human_approved' | 'human_rejected') => Promise<void> }
 * Outputs :
 *   - JSX.Element (Card with domain, ScoreBadge, why it was flagged (domain_check.status text such as 'Blocked: HTTP 403'), reasons_preview, Approve and Reject Buttons that call onDecision)
 * File explanation : One company waiting for a human decision.
 */

import { Check, X } from 'lucide-react';
import type { CompanySummary, DomainCheck } from '../../shared/types';
import { Button } from '../ui/Button';
import { Card } from '../ui/Card';
import { ScoreBadge } from '../ui/ScoreBadge';

function formatDomainCheckParts(dc: DomainCheck | null): string[] {
  if (!dc) return [];
  const parts: string[] = [`Bucket ${dc.bucket}`];
  if (dc.status !== null) {
    parts.push(`HTTP ${dc.status}`);
  }
  if (dc.redirected_to) {
    parts.push(`Redirected to ${dc.redirected_to}`);
  }
  return parts;
}

export function HumanReviewCard({
  company,
  index,
  busy,
  onDecision,
}: {
  company: CompanySummary;
  index: number;
  busy: boolean;
  onDecision: (companyId: number, decision: 'human_approved' | 'human_rejected') => Promise<void>;
}) {
  const flagParts = formatDomainCheckParts(company.domain_check);

  return (
    <Card index={index} className="flex flex-col justify-between gap-4">
      <div className="space-y-3">
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0">
            <h3 className="text-base font-semibold text-navy truncate">{company.domain}</h3>
            {flagParts.length > 0 ? (
              <p className="text-xs text-warn font-medium mt-1">{flagParts.join(' · ')}</p>
            ) : null}
          </div>
          <ScoreBadge score={company.score} />
        </div>

        {company.reasons_preview.length > 0 ? (
          <ul className="space-y-1 text-xs text-navy-soft">
            {company.reasons_preview.map((reason, idx) => (
              <li key={idx}>{reason.text}</li>
            ))}
          </ul>
        ) : null}
      </div>

      <div className="flex items-center gap-2 pt-2 border-t border-line">
        <Button
          variant="primary"
          icon={Check}
          loading={busy}
          disabled={busy}
          onClick={() => void onDecision(company.id, 'human_approved')}
        >
          Approve
        </Button>
        <Button
          variant="danger"
          icon={X}
          loading={busy}
          disabled={busy}
          onClick={() => void onDecision(company.id, 'human_rejected')}
        >
          Reject
        </Button>
      </div>
    </Card>
  );
}
