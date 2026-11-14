/**
 * Inputs :
 *   - props: { icon: LucideIcon; title: string; message: string; action?: { label: string; onClick: () => void } }
 * Outputs :
 *   - JSX.Element (centered icon, title, message and optional Button)
 * File explanation : Shown when a list loads successfully but has zero items.
 */

import type { LucideIcon } from 'lucide-react';
import { Button } from './Button';

export function EmptyState({
  icon: Icon,
  title,
  message,
  action,
}: {
  icon: LucideIcon;
  title: string;
  message: string;
  action?: { label: string; onClick: () => void };
}) {
  return (
    <div className="flex flex-col items-center justify-center text-center py-12 px-6 bg-surface border border-line rounded-xl shadow-card">
      <div className="h-12 w-12 rounded-full bg-canvas flex items-center justify-center text-slateblue-500 mb-4">
        <Icon className="h-6 w-6" aria-hidden="true" />
      </div>
      <h3 className="text-base font-semibold text-navy mb-1">{title}</h3>
      <p className="text-sm text-navy-mute max-w-md">{message}</p>
      {action ? (
        <div className="mt-5">
          <Button variant="primary" onClick={action.onClick}>
            {action.label}
          </Button>
        </div>
      ) : null}
    </div>
  );
}
