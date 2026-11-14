/**
 * Inputs :
 *   - props: { label: string; tone: StatusTone }
 * Outputs :
 *   - JSX.Element (small rounded pill; success=ok green, warning=gold, danger=bad red, info=slateblue, neutral=grey)
 * File explanation : The only place that maps a StatusTone to colors. Labels and tones come from shared/constants.ts lookup tables.
 */

import type { StatusTone } from '../../shared/types';

export function StatusPill({ label, tone }: { label: string; tone: StatusTone }) {
  const toneClasses: Record<StatusTone, string> = {
    success: 'bg-ok/15 text-ok border-ok/30',
    warning: 'bg-gold/15 text-gold-deep border-gold/40',
    danger: 'bg-bad/15 text-bad border-bad/30',
    info: 'bg-slateblue-400/15 text-slateblue-600 border-slateblue-400/30',
    neutral: 'bg-canvas text-navy-mute border-line',
  };

  return (
    <span
      className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium whitespace-nowrap shrink-0 ${toneClasses[tone]}`}
    >
      {label}
    </span>
  );
}
