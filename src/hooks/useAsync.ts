/**
 * Inputs :
 *   - action: (...args: A) => Promise<R>
 * Outputs :
 *   - { run: (...args: A) => Promise<R | undefined>; loading: boolean; error: ApiError | null }
 * File explanation : Wraps a button-triggered API action: sets loading while it runs, stores the error, returns undefined on failure and the result on success. Does not show toasts itself.
 */

import { useCallback, useState } from 'react';
import type { ApiError } from '../api/client';

export function useAsync<A extends unknown[], R>(
  action: (...args: A) => Promise<R>,
): { run: (...args: A) => Promise<R | undefined>; loading: boolean; error: ApiError | null } {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<ApiError | null>(null);

  const run = useCallback(
    async (...args: A): Promise<R | undefined> => {
      setLoading(true);
      setError(null);
      try {
        const result = await action(...args);
        return result;
      } catch (err) {
        setError(err as ApiError);
        return undefined;
      } finally {
        setLoading(false);
      }
    },
    [action],
  );

  return { run, loading, error };
}
