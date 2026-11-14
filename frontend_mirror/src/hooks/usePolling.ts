/**
 * Inputs :
 *   - fetcher: () => Promise<T>
 *   - options?: { intervalMs?: number (default POLL_INTERVAL_MS = 5000); enabled?: boolean (default true) }
 * Outputs :
 *   - { data: T | null; loading: boolean (true only until the first result); error: ApiError | null; refresh: () => Promise<void> }
 * File explanation : Calls fetcher immediately, then every intervalMs while the component is mounted, so only the screen currently open polls. Never starts a new request while one is still running. Keeps the previous data when a later poll fails (error is set, data is not cleared). Stops on unmount.
 */
