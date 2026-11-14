/**
 * Inputs :
 *   - apiCall, ENDPOINTS
 *   - types from shared/types.ts
 * Outputs :
 *   - getDashboard(): Promise<DashboardSummary>
 * File explanation : Typed wrapper for GET /dashboard.
 */

import { apiCall } from './client';
import { ENDPOINTS } from './endpoints';
import type { DashboardSummary } from '../shared/types';

export function getDashboard(): Promise<DashboardSummary> {
  return apiCall(ENDPOINTS.getDashboard);
}
