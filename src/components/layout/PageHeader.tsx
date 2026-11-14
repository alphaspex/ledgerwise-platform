/**
 * Inputs :
 *   - props: { title: string; subtitle?: string; actions?: ReactNode; onBack?: () => void }
 * Outputs :
 *   - JSX.Element (page title row; shows a back-arrow Button when onBack is provided; actions aligned right)
 * File explanation : Header at the top of every page.
 */

import type { ReactNode } from 'react';
import { ArrowLeft } from 'lucide-react';
import { Button } from '../ui/Button';

export function PageHeader({
  title,
  subtitle,
  actions,
  onBack,
}: {
  title: string;
  subtitle?: string;
  actions?: ReactNode;
  onBack?: () => void;
}) {
  return (
    <div className="mb-6 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
      <div className="flex items-center gap-3 min-w-0">
        {onBack ? (
          <Button variant="ghost" icon={ArrowLeft} onClick={onBack}>
            Back
          </Button>
        ) : null}
        <div className="min-w-0">
          <h1 className="text-2xl font-bold tracking-tight text-navy truncate">{title}</h1>
          {subtitle ? <p className="text-sm text-navy-mute mt-0.5">{subtitle}</p> : null}
        </div>
      </div>
      {actions ? <div className="flex items-center gap-2 shrink-0">{actions}</div> : null}
    </div>
  );
}
