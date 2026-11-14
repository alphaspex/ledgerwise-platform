/**
 * Inputs : none (declarative constant, imports types only)
 * Outputs : ENDPOINTS (typed object with every endpoint the frontend calls), EndpointDef<Body, Query, Res>, EndpointName
 * File explanation : THE ONLY file listing all API endpoints. Hand this file to the backend builder: each entry gives method, path, auth level, rate-limit class, request body type, query type, response type and expected error codes. Types come from shared/types.ts. Webhooks (inbound email, Cal.com) are backend-only and intentionally NOT listed. Entries tagged [NEW] are not described in the module .md files and must be added to the backend. Auth: send header "Authorization: Bearer <jwt>" when auth is not 'none'. Errors return JSON ErrorBody { detail: string }. 429 includes a Retry-After header. A 401 on an endpoint with auth 'member'/'admin' makes the UI log out, so wrong passwords/codes must NOT use 401 (use 400).
 */
import type {
  AcceptInviteRequest, AuthEvent, AuthEventsQuery, Booking, BookingsQuery,
  ChangePasswordConfirmRequest, ChangePasswordRequest, CompaniesQuery, CompanyDetail,
  CompanySummary, ContactRequest, DashboardSummary, EmailDraft, EmailReviewRequest,
  ForgotPasswordRequest, HumanReplyRequest, InviteRequest, LoginRequest, LoginResponse,
  MarkReadRequest, Notification, OkResponse, ResearchRun, ResearchStatus, ResetPasswordRequest,
  ReviewCompanyRequest, StartResearchRequest, ThreadDetail, ThreadMessage, ThreadSummary, UserSummary,
} from '../shared/types';

export type HttpMethod = 'GET' | 'POST' | 'PUT' | 'DELETE';
export type AuthLevel = 'none' | 'member' | 'admin';
export type RateClass = 'auth' | 'global'; // auth = 5 req/60s per IP, global = 60 req/60s per IP
export interface EndpointError { status: number; meaning: string }
export interface EndpointDef<Body = void, Query = void, Res = void> {
  method: HttpMethod;
  path: string;                     // {name} segments are path params
  pathParams: readonly string[];
  auth: AuthLevel;
  rateClass: RateClass;
  description: string;
  errors: readonly EndpointError[];
  readonly _types?: { body: Body; query: Query; response: Res }; // phantom, type-level only
}
function def<Body = void, Query = void, Res = void>(
  d: Omit<EndpointDef<Body, Query, Res>, '_types'>,
): EndpointDef<Body, Query, Res> { return d; }

const E401: EndpointError = { status: 401, meaning: 'Missing/invalid/expired token (UI logs out)' };
const E403: EndpointError = { status: 403, meaning: 'Admin only' };
const E404: EndpointError = { status: 404, meaning: 'Item not found' };
const E422: EndpointError = { status: 422, meaning: 'Validation error, detail explains which field' };
const E429: EndpointError = { status: 429, meaning: 'Rate limit exceeded, Retry-After header set' };

export const ENDPOINTS = {
  // ===================== AUTH (Module 3) =====================
  login: def<LoginRequest, void, LoginResponse>({
    method: 'POST', path: '/auth/login', pathParams: [], auth: 'none', rateClass: 'auth',
    description: 'Verify bcrypt, sign 7-day JWT, write login_ok / login_fail.',
    errors: [{ status: 401, meaning: 'Wrong email or password (no logout, auth is none)' }, E422, E429],
  }),
  logout: def<void, void, OkResponse>({
    method: 'POST', path: '/auth/logout', pathParams: [], auth: 'member', rateClass: 'global',
    description: 'Writes logout to auth_events. Client discards the token.',
    errors: [E401, E429],
  }),
  changePasswordRequest: def<ChangePasswordRequest, void, OkResponse>({
    method: 'POST', path: '/auth/change-password', pathParams: [], auth: 'member', rateClass: 'auth',
    description: 'Step 1: verify old password, email a 6-digit code (purpose change, 10 min).',
    errors: [E401, { status: 400, meaning: 'Old password is wrong' }, E422, E429],
  }),
  changePasswordConfirm: def<ChangePasswordConfirmRequest, void, OkResponse>({
    method: 'POST', path: '/auth/change-password/confirm', pathParams: [], auth: 'member', rateClass: 'auth',
    description: 'Step 2: code + new password twice. Wrong code = attempts+1, 3 attempts invalidates the code.',
    errors: [E401, { status: 400, meaning: 'Wrong code' }, { status: 410, meaning: 'Code expired or invalidated, request a new one' }, E422, E429],
  }),
  forgotPassword: def<ForgotPasswordRequest, void, OkResponse>({
    method: 'POST', path: '/auth/forgot-password', pathParams: [], auth: 'none', rateClass: 'auth',
    description: 'Always returns ok:true whether or not the email exists (no account enumeration). Emails a reset code if the user exists.',
    errors: [E422, E429],
  }),
  resetPassword: def<ResetPasswordRequest, void, OkResponse>({
    method: 'POST', path: '/auth/reset-password', pathParams: [], auth: 'none', rateClass: 'auth',
    description: 'Email + code + new password twice. Writes password_reset.',
    errors: [{ status: 400, meaning: 'Wrong code' }, { status: 410, meaning: 'Code expired or invalidated' }, E422, E429],
  }),
  acceptInvite: def<AcceptInviteRequest, void, OkResponse>({
    method: 'POST', path: '/auth/accept-invite', pathParams: [], auth: 'none', rateClass: 'auth',
    description: 'Invited user submits email + invite code + password twice. Writes invite_accepted.',
    errors: [{ status: 400, meaning: 'Wrong code' }, { status: 410, meaning: 'Invite expired (3 days)' }, E422, E429],
  }),
  listAuthEvents: def<void, AuthEventsQuery, AuthEvent[]>({
    method: 'GET', path: '/auth/events', pathParams: [], auth: 'member', rateClass: 'global',
    description: '[NEW route] Last 30 days of auth_events, newest first. Read-only.',
    errors: [E401, E429],
  }),
  // ===================== ADMIN (Module 3) =====================
  listUsers: def<void, void, UserSummary[]>({
    method: 'GET', path: '/admin/users', pathParams: [], auth: 'admin', rateClass: 'global',
    description: 'List users: id, email, is_admin, created_at. Never password fields.',
    errors: [E401, E403, E429],
  }),
  inviteUser: def<InviteRequest, void, UserSummary>({
    method: 'POST', path: '/admin/users/invite', pathParams: [], auth: 'admin', rateClass: 'global',
    description: 'Create user with unusable password, email invite code (3 days). Writes invite_sent.',
    errors: [E401, E403, { status: 409, meaning: 'Email already exists' }, E422, E429],
  }),
  removeUser: def<void, void, OkResponse>({
    method: 'DELETE', path: '/admin/users/{id}', pathParams: ['id'], auth: 'admin', rateClass: 'global',
    description: 'Hard delete the user row. Writes user_removed.',
    errors: [E401, E403, E404, E429],
  }),
  // ===================== RESEARCH (Module 1) =====================
  startResearch: def<StartResearchRequest, void, ResearchRun>({
    method: 'POST', path: '/research/start', pathParams: [], auth: 'member', rateClass: 'global',
    description: 'Insert a research_runs row (target_approved fixed at 30). Orchestrator picks it up on the next tick.',
    errors: [E401, { status: 409, meaning: '[NEW] A run is already running or paused' }, E422, E429],
  }),
  pauseResearch: def<void, void, ResearchRun>({
    method: 'POST', path: '/research/pause', pathParams: [], auth: 'member', rateClass: 'global',
    description: '[NEW] Set the active run status to paused.',
    errors: [E401, { status: 409, meaning: 'No running run' }, E429],
  }),
  resumeResearch: def<void, void, ResearchRun>({
    method: 'POST', path: '/research/resume', pathParams: [], auth: 'member', rateClass: 'global',
    description: '[NEW] Set the paused run back to running.',
    errors: [E401, { status: 409, meaning: 'No paused run' }, E429],
  }),
  getResearchStatus: def<void, void, ResearchStatus>({
    method: 'GET', path: '/research/status', pathParams: [], auth: 'member', rateClass: 'global',
    description: 'Active run + system_status (counts, progress, tokens, searches). Served from the in-memory snapshot, never touches D1.',
    errors: [E401, E429],
  }),
  listCompanies: def<void, CompaniesQuery, CompanySummary[]>({
    method: 'GET', path: '/companies', pathParams: [], auth: 'member', rateClass: 'global',
    description: '[NEW route] Companies, newest first. status = comma-separated list (e.g. status=approved,human_approved). has_contact=false returns only companies with contact_email null. No query = all companies.',
    errors: [E401, E429],
  }),
  getCompany: def<void, void, CompanyDetail>({
    method: 'GET', path: '/companies/{id}', pathParams: ['id'], auth: 'member', rateClass: 'global',
    description: '[NEW route] One company with research_data (reasons, quotes, sources), memory facts and contact info.',
    errors: [E401, E404, E429],
  }),
  reviewCompany: def<ReviewCompanyRequest, void, OkResponse>({
    method: 'POST', path: '/research/review', pathParams: [], auth: 'member', rateClass: 'global',
    description: 'Human decision on a needs_human_review company: writes companies + domain_memory in one batch.',
    errors: [E401, E404, { status: 409, meaning: 'Company is not in needs_human_review' }, E429],
  }),
  // ===================== OUTREACH (Module 2) =====================
  saveContact: def<ContactRequest, void, CompanySummary>({
    method: 'PUT', path: '/companies/{id}/contact', pathParams: ['id'], auth: 'member', rateClass: 'global',
    description: 'Manual contact entry (contact_source = manual). Overwrites anything Apollo wrote.',
    errors: [E401, E404, { status: 422, meaning: 'Invalid email or generic inbox (info@, hello@, support@...)' }, E429],
  }),
  listEmailDrafts: def<void, void, EmailDraft[]>({
    method: 'GET', path: '/emails/drafts', pathParams: [], auth: 'member', rateClass: 'global',
    description: '[NEW route] First-email drafts with status pending_review, each with its verified memory facts.',
    errors: [E401, E429],
  }),
  reviewEmail: def<EmailReviewRequest, void, OkResponse>({
    method: 'POST', path: '/emails/{message_id}/review', pathParams: ['message_id'], auth: 'member', rateClass: 'global',
    description: 'approve | edit (body required, then approve) | reject. Approve/edit inserts a send queue row.',
    errors: [E401, E404, { status: 409, meaning: 'Draft is no longer pending_review' }, E422, E429],
  }),
  listThreads: def<void, void, ThreadSummary[]>({
    method: 'GET', path: '/threads', pathParams: [], auth: 'member', rateClass: 'global',
    description: '[NEW route] Every company whose thread_state is not inactive, newest activity first.',
    errors: [E401, E429],
  }),
  getThread: def<void, void, ThreadDetail>({
    method: 'GET', path: '/threads/{company_id}', pathParams: ['company_id'], auth: 'member', rateClass: 'global',
    description: '[NEW route] Thread summary + all thread_messages in chronological order (with tool_calls).',
    errors: [E401, E404, E429],
  }),
  takeoverThread: def<void, void, ThreadSummary>({
    method: 'POST', path: '/threads/{company_id}/takeover', pathParams: ['company_id'], auth: 'member', rateClass: 'global',
    description: 'Sets thread_state = human_taken_over. The agent never speaks again on this thread.',
    errors: [E401, E404, { status: 409, meaning: 'Thread is closed' }, E429],
  }),
  sendHumanReply: def<HumanReplyRequest, void, ThreadMessage>({
    method: 'POST', path: '/threads/{company_id}/messages', pathParams: ['company_id'], auth: 'member', rateClass: 'global',
    description: 'Writes a thread_messages row (sender_type human, status sent) and sends the email.',
    errors: [E401, E404, { status: 409, meaning: 'Thread not taken over, or do_not_contact is set' }, E422, E429],
  }),
  // ===================== BOOKINGS / NOTIFICATIONS / DASHBOARD =====================
  listBookings: def<void, BookingsQuery, Booking[]>({
    method: 'GET', path: '/bookings', pathParams: [], auth: 'member', rateClass: 'global',
    description: '[NEW route] Bookings with scheduled_at between from and to (ISO), any status.',
    errors: [E401, E422, E429],
  }),
  listNotifications: def<void, void, Notification[]>({
    method: 'GET', path: '/notifications', pathParams: [], auth: 'member', rateClass: 'global',
    description: '[NEW route] Latest 50 notifications, newest first, read and unread.',
    errors: [E401, E429],
  }),
  markNotificationsRead: def<MarkReadRequest, void, OkResponse>({
    method: 'POST', path: '/notifications/read', pathParams: [], auth: 'member', rateClass: 'global',
    description: '[NEW route] Mark the given notification ids as read.',
    errors: [E401, E422, E429],
  }),
  getDashboard: def<void, void, DashboardSummary>({
    method: 'GET', path: '/dashboard', pathParams: [], auth: 'member', rateClass: 'global',
    description: '[NEW route] Summary counts for the dashboard (approved includes human_approved; rejected = rejected_by_human).',
    errors: [E401, E429],
  }),
};

export type EndpointName = keyof typeof ENDPOINTS;
