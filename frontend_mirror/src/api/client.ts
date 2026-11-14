/**
 * Inputs :
 *   - endpoint: EndpointDef<Body, Query, Res> (from api/endpoints.ts)
 *   - args?: { pathParams?: Record<string, string | number>; query?: Query; body?: Body }
 *   - API_BASE_URL: string, TOKEN_STORAGE_KEY: string (from shared/constants.ts)
 * Outputs :
 *   - apiCall<Body, Query, Res>(endpoint, args?): Promise<Res>  (rejects with ApiError)
 *   - class ApiError implements ApiErrorShape { status: number; detail: string; retryAfter: number | null }
 *   - getStoredToken(): string | null
 *   - setStoredToken(token: string | null): void
 *   - registerClientHandlers(h: { onUnauthorized: () => void; onRateLimited: () => void }): void
 * File explanation : The ONE fetch wrapper. Builds the URL (API_BASE_URL + path with {params} replaced + query string; array values joined with commas, undefined values skipped), adds 'Authorization: Bearer <token>' when endpoint.auth is not 'none', sends JSON body, parses JSON. Non-2xx => throws ApiError built from ErrorBody.detail and the Retry-After header. HTTP 401 on an endpoint whose auth is not 'none' calls onUnauthorized; HTTP 429 calls onRateLimited (no automatic retry). Network failure => ApiError with status 0 and detail 'Network error'.
 */
