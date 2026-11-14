/**
 * Inputs :
 *   - none
 *   - useApp(): AppContextValue (from shared/AppContext.tsx)
 * Outputs :
 *   - { success: (text: string) => void; error: (text: string) => void; info: (text: string) => void }
 * File explanation : Thin convenience hook over context.pushToast so components call toast.success('Saved').
 */

import { useMemo } from 'react';
import { useApp } from '../shared/AppContext';

export function useToast(): {
  success: (text: string) => void;
  error: (text: string) => void;
  info: (text: string) => void;
} {
  const { pushToast } = useApp();

  return useMemo(
    () => ({
      success: (text: string) => pushToast('success', text),
      error: (text: string) => pushToast('error', text),
      info: (text: string) => pushToast('info', text),
    }),
    [pushToast],
  );
}
