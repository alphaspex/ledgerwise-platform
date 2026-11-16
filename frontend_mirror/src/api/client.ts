/**
 * Inputs :
 *   - endpoint: EndpointDef<Body, Query, Res> (from api/endpoints.ts)
 *   - args?: { pathParams?: Record<string, string | number>; query?: Query; body?: Body }
 *   - API_BASE_URL: string, TOKEN_STORAGE_KEY: string (from shared/constants.ts)
 * Outputs :
 *   - apiCall<Body, Query, Res>(endpoint, args?): Promise<Res> (rejects with ApiError)
 *   - ApiError, getStoredToken(), setStoredToken(), registerClientHandlers()
 * File explanation : The ONE fetch wrapper. Builds endpoint URLs, adds bearer auth when required, sends JSON and parses responses. Network and HTTP failures are logged through api/diagnostics.ts without request headers or bodies.
 */
