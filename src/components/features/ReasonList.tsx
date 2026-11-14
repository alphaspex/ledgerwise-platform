/**
 * Inputs :
 *   - props: { reasons: Reason[]; sources: SourceCheck[] }
 * Outputs :
 *   - JSX.Element (each reason: text, the verbatim quote in a quote block, and a link to source_url opening in a new tab with rel='noopener noreferrer'; below, the checked sources each with a result StatusPill live/dead/unverified/untested and HTTP status)
 * File explanation : Shows WHY a company was qualified, with proof.
 */

import { ExternalLink } from 'lucide-react';
import type { Reason, SourceCheck, SourceResult, StatusTone } from '../../shared/types';
import { StatusPill } from '../ui/StatusPill';

const SOURCE_RESULT_LABEL: Record<SourceResult, string> = {
  live: 'Live',
  dead: 'Dead',
  unverified: 'Unverified',
  untested: 'Untested',
};

const SOURCE_RESULT_TONE: Record<SourceResult, StatusTone> = {
  live: 'success',
  dead: 'danger',
  unverified: 'warning',
  untested: 'neutral',
};

export function ReasonList({
  reasons,
  sources,
}: {
  reasons: Reason[];
  sources: SourceCheck[];
}) {
  return (
    <div className="space-y-6">
      <div className="space-y-3">
        <h3 className="text-sm font-semibold text-navy">Qualification reasons</h3>
        {reasons.length === 0 ? (
          <p className="text-sm text-navy-mute">No reasons recorded.</p>
        ) : (
          <ul className="space-y-3">
            {reasons.map((r, idx) => (
              <li
                key={idx}
                className="rounded-xl border border-line bg-surface p-4 shadow-card space-y-2"
              >
                <div className="flex items-start justify-between gap-3">
                  <p className="text-sm font-medium text-navy">{r.text}</p>
                  {r.source_url ? (
                    <a
                      href={r.source_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1 text-xs font-medium text-slateblue-600 hover:underline shrink-0"
                    >
                      <span>Source</span>
                      <ExternalLink className="h-3 w-3" aria-hidden="true" />
                    </a>
                  ) : null}
                </div>
                {r.quote ? (
                  <blockquote className="text-xs text-navy-soft italic border-l-2 border-gold pl-3 py-0.5">
                    {r.quote}
                  </blockquote>
                ) : null}
              </li>
            ))}
          </ul>
        )}
      </div>

      <div className="space-y-2">
        <h3 className="text-sm font-semibold text-navy">Checked sources</h3>
        {sources.length === 0 ? (
          <p className="text-sm text-navy-mute">No checked sources.</p>
        ) : (
          <ul className="divide-y divide-line rounded-xl border border-line bg-surface">
            {sources.map((src, idx) => (
              <li key={idx} className="px-4 py-2.5 flex items-center justify-between gap-3 text-xs">
                <a
                  href={src.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-slateblue-600 hover:underline truncate"
                >
                  {src.url}
                </a>
                <div className="flex items-center gap-2 shrink-0">
                  {src.status !== null ? (
                    <span className="text-navy-mute tabular-nums">HTTP {src.status}</span>
                  ) : null}
                  <StatusPill
                    label={SOURCE_RESULT_LABEL[src.result]}
                    tone={SOURCE_RESULT_TONE[src.result]}
                  />
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
