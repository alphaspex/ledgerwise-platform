/**
 * Inputs :
 *   - apiCall, ENDPOINTS
 *   - types from shared/types.ts
 * Outputs :
 *   - listBookings(query: BookingsQuery): Promise<Booking[]>
 * File explanation : Typed wrapper for GET /bookings.
 */

import { apiCall } from './client';
import { ENDPOINTS } from './endpoints';
import type { Booking, BookingsQuery } from '../shared/types';

export function listBookings(query: BookingsQuery): Promise<Booking[]> {
  return apiCall(ENDPOINTS.listBookings, { query });
}
