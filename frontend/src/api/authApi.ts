/**
 * Inputs :
 *   - apiCall (from api/client.ts), ENDPOINTS (from api/endpoints.ts)
 *   - request types from shared/types.ts
 * Outputs :
 *   - login(body: LoginRequest): Promise<LoginResponse>
 *   - logout(): Promise<OkResponse>
 *   - requestPasswordChange(body: ChangePasswordRequest): Promise<OkResponse>
 *   - confirmPasswordChange(body: ChangePasswordConfirmRequest): Promise<OkResponse>
 *   - forgotPassword(body: ForgotPasswordRequest): Promise<OkResponse>
 *   - resetPassword(body: ResetPasswordRequest): Promise<OkResponse>
 *   - acceptInvite(body: AcceptInviteRequest): Promise<OkResponse>
 *   - listAuthEvents(query?: AuthEventsQuery): Promise<AuthEvent[]>
 * File explanation : Typed one-line wrappers for every /auth/* endpoint. No logic besides calling apiCall with the right ENDPOINTS entry.
 */

import { apiCall } from './client';
import { ENDPOINTS } from './endpoints';
import type {
  AcceptInviteRequest,
  AuthEvent,
  AuthEventsQuery,
  ChangePasswordConfirmRequest,
  ChangePasswordRequest,
  ForgotPasswordRequest,
  LoginRequest,
  LoginResponse,
  OkResponse,
  ResetPasswordRequest,
} from '../shared/types';

export function login(body: LoginRequest): Promise<LoginResponse> {
  return apiCall(ENDPOINTS.login, { body });
}

export function logout(): Promise<OkResponse> {
  return apiCall(ENDPOINTS.logout);
}

export function requestPasswordChange(body: ChangePasswordRequest): Promise<OkResponse> {
  return apiCall(ENDPOINTS.changePasswordRequest, { body });
}

export function confirmPasswordChange(body: ChangePasswordConfirmRequest): Promise<OkResponse> {
  return apiCall(ENDPOINTS.changePasswordConfirm, { body });
}

export function forgotPassword(body: ForgotPasswordRequest): Promise<OkResponse> {
  return apiCall(ENDPOINTS.forgotPassword, { body });
}

export function resetPassword(body: ResetPasswordRequest): Promise<OkResponse> {
  return apiCall(ENDPOINTS.resetPassword, { body });
}

export function acceptInvite(body: AcceptInviteRequest): Promise<OkResponse> {
  return apiCall(ENDPOINTS.acceptInvite, { body });
}

export function listAuthEvents(query?: AuthEventsQuery): Promise<AuthEvent[]> {
  return apiCall(ENDPOINTS.listAuthEvents, { query });
}
