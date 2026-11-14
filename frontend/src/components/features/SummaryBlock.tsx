/**
 * Inputs :
 *   - props: { title: string; icon: LucideIcon; stats: { label: string; value: number; tone: StatusTone }[]; onClick?: () => void; index?: number }
 * Outputs :
 *   - JSX.Element (interactive Card with icon, title, and one AnimatedCounter + label per stat colored by tone)
 * File explanation : One block of the dashboard.
 */

import type { LucideIcon } from 'lucide-react';
import type { StatusTone } from '../../shared/types';
import { AnimatedCounter } from '../ui/AnimatedCounter';
import { Card } from '../ui/Card';

export function SummaryBlock({
  title,
  icon: Icon,
  stats,
  onClick,
  index = 0,
}: {
  title: string;
  icon: LucideIcon;
  stats: { label: string; value: number; tone: StatusTone }[];
  onClick?: () => void;
  index?: number;
}) {
  const toneTextClass: Record<StatusTone, string> = {
    success: 'text-ok',
    warning: 'text-gold-deep',
    danger: 'text-bad',
    info: 'text-slateblue-600',
    neutral: 'text-navy-mute',
  };

  return (
    <Card interactive={Boolean(onClick)} onClick={onClick} index={index} className="space-y-4">
      <div className="flex items-center gap-3">
        <div className="h-9 w-9 rounded-lg bg-canvas flex items-center justify-center text-slateblue-600 shrink-0">
          <Icon className="h-5 w-5" aria-hidden="true" />
        </div>
        <h2 className="text-base font-semibold text-navy">{title}</h2>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
        {stats.map((stat) => (
          <div key={stat.label} className="space-y-0.5">
            <div className={`text-2xl font-bold ${toneTextClass[stat.tone]}`}>
              <AnimatedCounter value={stat.value} />
            </div>
            <div className="text-xs font-medium text-navy-mute">{stat.label}</div>
          </div>
        ))}
      </div>
    </Card>
  );
}
