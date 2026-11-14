/**
 * Inputs :
 *   - props: { message: string; onRetry?: () => void }
 * Outputs :
 *   - JSX.Element (centered error icon, message and optional 'Try again' Button)
 * File explanation : Shown when a data page fails to load.
 */

import { AlertCircle, RefreshCw } from 'lucide-react';
import { Button } from './Button';

export function ErrorState({
  message,
  onRetry,
}: {
  message: string;
  onRetry?: () => void;
}) {
  return (
    <div className="flex flex-col items-center justify-center text-center py-12 px-6 bg-surface border border-line rounded-xl shadow-card">
      <div className="h-12 w-12 rounded-full bg-bad/10 flex items-center justify-center text-bad mb-4">
        <AlertCircle className="h-6 w-6" aria-hidden="true" />
      </div>
      <p className="text-sm font-medium text-navy max-w-md">{message}</p>
      {onRetry ? (
        <div className="mt-5">
          <Button variant="secondary" icon={RefreshCw} onClick={onRetry}>
            Try again
          </Button>
        </div>
      ) : null}
    </div>
  );
}
