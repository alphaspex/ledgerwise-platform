/**
 * Inputs :
 *   - props: { value: number; max: number; label?: string }
 * Outputs :
 *   - JSX.Element (track + slate-gradient fill whose width animates to value/max, clamped 0..100%; optional label above)
 * File explanation : Animated progress bar (research approved vs target, etc).
 */

import { motion } from 'framer-motion';

export function ProgressBar({
  value,
  max,
  label,
}: {
  value: number;
  max: number;
  label?: string;
}) {
  const ratio = max > 0 ? (value / max) * 100 : 0;
  const pct = Math.max(0, Math.min(100, ratio));

  return (
    <div className="w-full">
      {label ? (
        <div className="flex items-center justify-between text-xs font-medium text-navy-soft mb-1.5">
          <span>{label}</span>
          <span className="tabular-nums text-navy">
            {value} / {max}
          </span>
        </div>
      ) : null}
      <div
        role="progressbar"
        aria-valuenow={value}
        aria-valuemin={0}
        aria-valuemax={max}
        className="h-2.5 w-full rounded-full bg-canvas overflow-hidden border border-line"
      >
        <motion.div
          className="h-full rounded-full bg-slate-gradient"
          initial={{ width: 0 }}
          animate={{ width: `${pct}%` }}
          transition={{ duration: 0.4, ease: 'easeOut' }}
        />
      </div>
    </div>
  );
}
