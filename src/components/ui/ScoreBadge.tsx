/**
 * Inputs :
 *   - props: { score: number | null } (0..10 integer or null)
 * Outputs :
 *   - JSX.Element (round badge showing the score, shade grows with score; shows an em dash when null)
 * File explanation : Visual score indicator. Informational only, it never changes any status.
 */

export function ScoreBadge({ score }: { score: number | null }) {
  if (score === null) {
    return (
      <span
        aria-label="No score"
        className="inline-flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-canvas text-navy-mute border border-line text-sm font-semibold tabular-nums"
      >
        &mdash;
      </span>
    );
  }

  const clamped = Math.max(0, Math.min(10, Math.round(score)));
  const toneClass =
    clamped >= 8
      ? 'bg-gold text-white border-gold-deep'
      : clamped >= 5
        ? 'bg-slateblue-500 text-white border-slateblue-600'
        : clamped >= 3
          ? 'bg-slateblue-300/40 text-navy border-slateblue-400'
          : 'bg-canvas text-navy-soft border-line';

  return (
    <span
      aria-label={`Score ${clamped} out of 10`}
      className={`inline-flex h-9 w-9 shrink-0 items-center justify-center rounded-full border text-sm font-semibold tabular-nums ${toneClass}`}
    >
      {clamped}
    </span>
  );
}
