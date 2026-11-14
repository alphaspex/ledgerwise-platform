/**
 * Inputs :
 *   - props: { value: number; durationMs?: number (default 600) }
 * Outputs :
 *   - JSX.Element (<span> that counts smoothly from the previous value to value, shows integers)
 * File explanation : Number that animates when live data changes.
 */

import { useEffect, useRef, useState } from 'react';

export function AnimatedCounter({
  value,
  durationMs = 600,
}: {
  value: number;
  durationMs?: number;
}) {
  const [display, setDisplay] = useState<number>(() => Math.round(value));
  const currentRef = useRef<number>(Math.round(value));

  useEffect(() => {
    const startVal = currentRef.current;
    const endVal = Math.round(value);
    if (startVal === endVal) {
      setDisplay(endVal);
      return;
    }

    let frameId = 0;
    const startTime = performance.now();

    const tick = (now: number) => {
      const elapsed = now - startTime;
      const t = Math.min(1, durationMs > 0 ? elapsed / durationMs : 1);
      const eased = 1 - Math.pow(1 - t, 3);
      const next = Math.round(startVal + (endVal - startVal) * eased);
      currentRef.current = next;
      setDisplay(next);
      if (t < 1) {
        frameId = requestAnimationFrame(tick);
      } else {
        currentRef.current = endVal;
      }
    };

    frameId = requestAnimationFrame(tick);
    return () => {
      cancelAnimationFrame(frameId);
    };
  }, [value, durationMs]);

  return <span className="tabular-nums">{display}</span>;
}
