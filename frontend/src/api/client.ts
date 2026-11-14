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

import type { EndpointDef } from './endpoints';
import { API_BASE_URL, TOKEN_STORAGE_KEY } from '../shared/constants';
import type { ApiErrorShape, ErrorBody } from '../shared/types';

export class ApiError extends Error implements ApiErrorShape {
  status: number;
  detail: string;
  retryAfter: number | null;

  constructor(status: number, detail: string, retryAfter: number | null = null) {
    super(detail);
    this.name = 'ApiError';
    this.status = status;
    this.detail = detail;
    this.retryAfter = retryAfter;
  }
}

let clientHandlers: { onUnauthorized: () => void; onRateLimited: () => void } = {
  onUnauthorized: () => {},
  onRateLimited: () => {},
};

export function getStoredToken(): string | null {
  try {
    return localStorage.getItem(TOKEN_STORAGE_KEY);
  } catch {
    return null;
  }
}

export function setStoredToken(token: string | null): void {
  try {
    if (token === null) {
      localStorage.removeItem(TOKEN_STORAGE_KEY);
    } else {
      localStorage.setItem(TOKEN_STORAGE_KEY, token);
    }
  } catch {
    // Ignore storage errors in restricted environments
  }
}

export function registerClientHandlers(h: {
  onUnauthorized: () => void;
  onRateLimited: () => void;
}): void {
  clientHandlers = h;
}

function buildUrl(
  pathTemplate: string,
  pathParams?: Record<string, string | number>,
  query?: unknown,
): string {
  let path = pathTemplate;
  if (pathParams) {
    for (const [key, val] of Object.entries(pathParams)) {
      path = path.replace(`{${key}}`, encodeURIComponent(String(val)));
    }
  }
  const base = (API_BASE_URL || '').replace(/\/+$/, '');
  let url = `${base}${path}`;

  if (query && typeof query === 'object') {
    const params = new URLSearchParams();
    for (const [key, val] of Object.entries(query as Record<string, unknown>)) {
      if (val === undefined || val === null) continue;
      if (Array.isArray(val)) {
        if (val.length > 0) {
          params.set(key, val.map(String).join(','));
        }
      } else {
        params.set(key, String(val));
      }
    }
    const qs = params.toString();
    if (qs) {
      url += `?${qs}`;
    }
  }

  return url;
}

function parseRetryAfter(headerValue: string | null): number | null {
  if (!headerValue) return null;
  const num = Number(headerValue);
  if (!Number.isNaN(num) && Number.isFinite(num)) {
    return num;
  }
  const dateMs = Date.parse(headerValue);
  if (!Number.isNaN(dateMs)) {
    return Math.max(0, Math.ceil((dateMs - Date.now()) / 1000));
  }
  return null;
}

export async function apiCall<Body, Query, Res>(
  endpoint: EndpointDef<Body, Query, Res>,
  args?: {
    pathParams?: Record<string, string | number>;
    query?: Query;
    body?: Body;
  },
): Promise<Res> {
  const url = buildUrl(endpoint.path, args?.pathParams, args?.query);
  const headers: Record<string, string> = {};

  if (endpoint.auth !== 'none') {
    const token = getStoredToken();
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
  }

  let bodyStr: string | undefined;
  if (args?.body !== undefined) {
    headers['Content-Type'] = 'application/json';
    bodyStr = JSON.stringify(args.body);
  }

  let response: Response;
  try {
    response = await fetch(url, {
      method: endpoint.method,
      headers,
      body: bodyStr,
    });
  } catch {
    throw new ApiError(0, 'Network error', null);
  }

  if (!response.ok) {
    const retryAfter = parseRetryAfter(response.headers.get('Retry-After'));
    let detail = `Request failed (${response.status})`;
    try {
      const parsed = (await response.json()) as Partial<ErrorBody>;
      if (parsed && typeof parsed.detail === 'string' && parsed.detail.length > 0) {
        detail = parsed.detail;
      }
    } catch {
      // Non-JSON error body
    }

    if (response.status === 401 && endpoint.auth !== 'none') {
      clientHandlers.onUnauthorized();
    } else if (response.status === 429) {
      clientHandlers.onRateLimited();
    }

    throw new ApiError(response.status, detail, retryAfter);
  }

  return (await response.json()) as Res;
}
