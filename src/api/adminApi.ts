/**
 * Inputs :
 *   - apiCall, ENDPOINTS
 *   - types from shared/types.ts
 * Outputs :
 *   - listUsers(): Promise<UserSummary[]>
 *   - inviteUser(body: InviteRequest): Promise<UserSummary>
 *   - removeUser(id: number): Promise<OkResponse>
 * File explanation : Typed wrappers for the admin-only user management endpoints (/admin/users).
 */

import { apiCall } from './client';
import { ENDPOINTS } from './endpoints';
import type { InviteRequest, OkResponse, UserSummary } from '../shared/types';

export function listUsers(): Promise<UserSummary[]> {
  return apiCall(ENDPOINTS.listUsers);
}

export function inviteUser(body: InviteRequest): Promise<UserSummary> {
  return apiCall(ENDPOINTS.inviteUser, { body });
}

export function removeUser(id: number): Promise<OkResponse> {
  return apiCall(ENDPOINTS.removeUser, { pathParams: { id } });
}
