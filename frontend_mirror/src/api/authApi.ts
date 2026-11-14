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
