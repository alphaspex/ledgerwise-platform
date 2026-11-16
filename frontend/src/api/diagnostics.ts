/**
 * Inputs :
 *   - method: 'GET' | 'POST' | 'PUT' | 'DELETE'
 *   - path: string (endpoint path template, without query values)
 *   - requestUrl: string (complete request URL)
 *   - status: number; statusText: string; retryAfter: number | null (HTTP failure details)
 *   - error: unknown (browser fetch rejection)
 * Outputs :
 *   - logApiNetworkFailure(method: HttpMethod, path: string, requestUrl: string, error: unknown): void
 *   - logApiHttpFailure(method: HttpMethod, path: string, status: number, statusText: string, retryAfter: number | null): void
 * File explanation : Writes safe browser-console diagnostics for failed API requests. It never receives or logs authorization headers or request bodies.
 */

type HttpMethod = 'GET' | 'POST' | 'PUT' | 'DELETE';

export function logApiNetworkFailure(
  method: HttpMethod,
  path: string,
  requestUrl: string,
  error: unknown,
): void {
  const failure = error instanceof Error
    ? { errorName: error.name, errorMessage: error.message }
    : { errorName: 'UnknownError', errorMessage: String(error) };
  let apiOrigin = 'invalid API URL';
  try {
    apiOrigin = new URL(requestUrl).origin;
  } catch {
    // Keep the diagnostic fallback when the configured URL is invalid.
  }
  console.error('[Ledgerwise API] Network request failed', {
    method, path, apiOrigin, ...failure,
  });
}

export function logApiHttpFailure(
  method: HttpMethod,
  path: string,
  status: number,
  statusText: string,
  retryAfter: number | null,
): void {
  console.warn('[Ledgerwise API] HTTP request failed', {
    method, path, status, statusText, retryAfter,
  });
}
