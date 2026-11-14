/**
 * Inputs :
 *   - props: { variant?: 'card' | 'line' | 'circle' | 'block' (default 'block'); count?: number (default 1); className?: string }
 * Outputs :
 *   - JSX.Element (pulsing grey placeholder(s), repeated count times)
 * File explanation : Loading placeholder shown on every data page before the first poll result.
 */

export function Skeleton({
  variant = 'block',
  count = 1,
  className = '',
}: {
  variant?: 'card' | 'line' | 'circle' | 'block';
  count?: number;
  className?: string;
}) {
  const variantClasses: Record<'card' | 'line' | 'circle' | 'block', string> = {
    card: 'h-32 w-full rounded-xl',
    line: 'h-4 w-full rounded-md',
    circle: 'h-10 w-10 rounded-full',
    block: 'h-20 w-full rounded-lg',
  };

  return (
    <div className="space-y-3" aria-busy="true" aria-label="Loading">
      {Array.from({ length: Math.max(1, count) }).map((_, idx) => (
        <div
          key={idx}
          className={`animate-pulse bg-line/70 ${variantClasses[variant]} ${className}`.trim()}
        />
      ))}
    </div>
  );
}
