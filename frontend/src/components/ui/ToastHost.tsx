/**
 * Inputs :
 *   - none
 *   - context.toasts: Toast[] and context.dismissToast(id: number): void via useApp()
 *   - TOAST_DURATION_MS: number (from shared/constants.ts)
 * Outputs :
 *   - JSX.Element (fixed stack of toasts; each slides in, auto-dismisses after TOAST_DURATION_MS, colored by ToastKind)
 * File explanation : Displays toast notifications. Mounted once in App.tsx.
 */

import { useEffect } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { AlertCircle, CheckCircle2, Info, X } from 'lucide-react';
import { useApp } from '../../shared/AppContext';
import { TOAST_DURATION_MS } from '../../shared/constants';
import type { Toast, ToastKind } from '../../shared/types';

function ToastItem({
  toast,
  onDismiss,
}: {
  toast: Toast;
  onDismiss: (id: number) => void;
}) {
  useEffect(() => {
    const timer = window.setTimeout(() => {
      onDismiss(toast.id);
    }, TOAST_DURATION_MS);
    return () => window.clearTimeout(timer);
  }, [toast.id, onDismiss]);

  const kindStyles: Record<ToastKind, string> = {
    success: 'border-ok/40 bg-surface text-navy',
    error: 'border-bad/40 bg-surface text-navy',
    info: 'border-slateblue-400/40 bg-surface text-navy',
  };

  const Icon =
    toast.kind === 'success'
      ? CheckCircle2
      : toast.kind === 'error'
        ? AlertCircle
        : Info;

  const iconColor =
    toast.kind === 'success'
      ? 'text-ok'
      : toast.kind === 'error'
        ? 'text-bad'
        : 'text-slateblue-500';

  return (
    <motion.div
      layout
      initial={{ opacity: 0, x: 24, scale: 0.96 }}
      animate={{ opacity: 1, x: 0, scale: 1 }}
      exit={{ opacity: 0, x: 24, scale: 0.96 }}
      transition={{ duration: 0.2 }}
      role="status"
      className={`pointer-events-auto flex items-start gap-3 rounded-xl border px-4 py-3 shadow-lift max-w-sm ${kindStyles[toast.kind]}`}
    >
      <Icon className={`h-4 w-4 mt-0.5 shrink-0 ${iconColor}`} aria-hidden="true" />
      <p className="text-sm font-medium flex-1 break-words">{toast.text}</p>
      <button
        type="button"
        onClick={() => onDismiss(toast.id)}
        aria-label="Dismiss notification"
        className="text-navy-mute hover:text-navy p-0.5 rounded"
      >
        <X className="h-3.5 w-3.5" aria-hidden="true" />
      </button>
    </motion.div>
  );
}

export function ToastHost() {
  const { toasts, dismissToast } = useApp();

  return (
    <div
      aria-live="polite"
      className="fixed bottom-20 md:bottom-4 right-4 z-50 flex flex-col gap-2 pointer-events-none"
    >
      <AnimatePresence mode="popLayout">
        {toasts.map((t) => (
          <ToastItem key={t.id} toast={t} onDismiss={dismissToast} />
        ))}
      </AnimatePresence>
    </div>
  );
}
