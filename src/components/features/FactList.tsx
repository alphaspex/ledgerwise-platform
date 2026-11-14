/**
 * Inputs :
 *   - props: { facts: MemoryFact[] }
 * Outputs :
 *   - JSX.Element (list of verified facts: field name, value, quote, and a source link opening in a new tab; empty list renders an inline 'No verified facts' note)
 * File explanation : Shows the verified memory facts of a company. Used under email drafts and on the company detail page.
 */

import { ExternalLink } from 'lucide-react';
import type { MemoryFact } from '../../shared/types';

export function FactList({ facts }: { facts: MemoryFact[] }) {
  if (facts.length === 0) {
    return <p className="text-xs text-navy-mute italic">No verified facts</p>;
  }

  return (
    <div className="space-y-2">
      <div className="text-xs font-semibold text-navy-soft uppercase tracking-wide">
        Verified facts
      </div>
      <ul className="space-y-2">
        {facts.map((fact, idx) => (
          <li
            key={`${fact.field}-${idx}`}
            className="rounded-lg border border-line bg-canvas/50 p-3 text-xs space-y-1"
          >
            <div className="flex items-center justify-between gap-2">
              <span className="font-semibold text-navy">
                {fact.field}: <span className="font-normal text-navy-soft">{fact.value}</span>
              </span>
              {fact.source_url ? (
                <a
                  href={fact.source_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1 text-slateblue-600 hover:underline shrink-0"
                >
                  <span>Source</span>
                  <ExternalLink className="h-3 w-3" aria-hidden="true" />
                </a>
              ) : null}
            </div>
            {fact.quote ? (
              <blockquote className="text-navy-mute italic border-l-2 border-line pl-2.5">
                {fact.quote}
              </blockquote>
            ) : null}
          </li>
        ))}
      </ul>
    </div>
  );
}
