/**
 * Inputs :
 *   - apiCall, ENDPOINTS
 *   - types from shared/types.ts
 * Outputs :
 *   - listNotifications(): Promise<Notification[]>
 *   - markNotificationsRead(body: MarkReadRequest): Promise<OkResponse>
 * File explanation : Typed wrappers for the notifications endpoints used by the bell.
 */

import { apiCall } from './client';
import { ENDPOINTS } from './endpoints';
import type { MarkReadRequest, Notification, OkResponse } from '../shared/types';

export function listNotifications(): Promise<Notification[]> {
  return apiCall(ENDPOINTS.listNotifications);
}

export function markNotificationsRead(body: MarkReadRequest): Promise<OkResponse> {
  return apiCall(ENDPOINTS.markNotificationsRead, { body });
}
