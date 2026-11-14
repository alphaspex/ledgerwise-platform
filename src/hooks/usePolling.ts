/**
 * Inputs :
 *   - fetcher: () => Promise<T>
 *   - options?: { intervalMs?: number (default POLL_INTERVAL_MS = 5000); enabled?: boolean (default true) }
 * Outputs :
 *   - { data: T | null; loading: boolean (true only until the first result); error: ApiError | null; refresh: () => Promise<void> }
 * File explanation : Calls fetcher immediately, then every intervalMs while the component is mounted, so only the screen currently open polls. Never starts a new request while one is still running. Keeps the previous data when a later poll fails (error is set, data is not cleared). Stops on unmount.
 */

import { useCallback, useEffect, useRef, useState } from 'react';
import type { ApiError } from '../api/client';
import { POLL_INTERVAL_MS } from '../shared/constants';

export function usePolling<T>(
  fetcher: () => Promise<T>,
  options?: { intervalMs?: number; enabled?: boolean },
): {
  data: T | null;
  loading: boolean;
  error: ApiError | null;
  refresh: () => Promise<void>;
} {
  const intervalMs = options?.intervalMs ?? POLL_INTERVAL_MS;
  const enabled = options?.enabled ?? true;

  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState<boolean>(enabled);
  const [error, setError] = useState<ApiError | null>(null);

  const inFlightRef = useRef(false);
  const mountedRef = useRef(true);
  const fetcherRef = useRef(fetcher);
  fetcherRef.current = fetcher;

  const execute = useCallback(async () => {
    if (inFlightRef.current || !mountedRef.current) return;
    inFlightRef.current = true;
    try {
      const result = await fetcherRef.current();
      if (!mountedRef.current) return;
      setData(result);
      setError(null);
      setLoading(false);
    } catch (err) {
      if (!mountedRef.current) return;
      setError(err as ApiError);
      setLoading(false);
    } finally {
      inFlightRef.current = false;
    }
  }, []);

  useEffect(() => {
    mountedRef.current = true;
    return () => {
      mountedRef.current = false;
    };
  }, []);

  useEffect(() => {
    if (!enabled) {
      setLoading(false);
      return;
    }
    setLoading((prev) => (data === null ? true : prev));
    void execute();
    const timer = window.setInterval(() => {
      void execute();
    }, intervalMs);
    return () => {
      window.clearInterval(timer);
    };
  }, [enabled, intervalMs, fetcher, execute]);

  const refresh = useCallback(async () => {
    await execute();
  }, [execute]);

  return { data, loading, error, refresh };
}
