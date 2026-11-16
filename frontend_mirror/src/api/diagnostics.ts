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
