/**
 * Inputs :
 *   - method: 'GET' | 'POST' | 'PUT' | 'DELETE'
 *   - path: string (endpoint path template, without query values)
 *   - requestUrl: string (complete request URL)
 *   - error: unknown (browser fetch rejection)
 * Outputs :
 *   - logApiNetworkFailure(...): void; logApiHttpFailure(...): void
 * File explanation : Writes safe browser-console diagnostics for failed API requests. It never receives or logs authorization headers or request bodies.
 */
