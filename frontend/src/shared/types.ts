/**
 * Inputs : none (pure type declarations, no runtime code)
 * Outputs : every shared TypeScript type/interface used by the frontend (domain models, request/response bodies, query objects, context value, and AI usage summaries)
 * File explanation : The single source of truth for all data shapes. Every other file imports its types from here. Shapes mirror the backend API contract. Booleans are sent as true/false in JSON even though D1 stores 0/1; AI usage cost is nullable when pricing is incomplete.
 */

// ===================== primitives & enums =====================
export type ISODateString = string;
export type ContactRole = 'founder' | 'coo' | 'finance' | 'unknown';
export type ContactSource = 'manual' | 'apollo';
export type CompanyStatus =
  | 'pending' | 'approved' | 'needs_human_review' | 'human_approved'
  | 'human_rejected' | 'rejected_low_evidence' | 'failed_404' | 'failed_enrichment';
export type EmailStatus =
  | 'not_started' | 'drafting' | 'pending_review' | 'approved'
  | 'sent' | 'rejected_by_human' | 'failed_contact';
export type ThreadState = 'inactive' | 'auto' | 'needs_human' | 'human_taken_over' | 'closed';
export type ResearchRunStatus = 'running' | 'paused' | 'done';
export type SourceResult = 'untested' | 'live' | 'dead' | 'unverified';
export type MessageSender = 'agent' | 'prospect' | 'human';
export type MessageStatus =
  | 'draft' | 'pending_review' | 'approved' | 'sent'
  | 'received' | 'failed' | 'blocked_by_do_not_contact';
export type BookingStatus = 'booked' | 'cancelled' | 'rescheduled' | 'completed';
export type BookingSource = 'agent' | 'prospect_link';
export type NotificationReason = 'unsure_answer' | 'do_not_contact' | 'booking_conflict' | 'contact_missing';
export type AuthEventType =
  | 'login_ok' | 'login_fail' | 'password_change' | 'password_reset'
  | 'invite_sent' | 'invite_accepted' | 'user_removed' | 'logout' | 'rate_limited';
export type ToolName = 'check_availability' | 'book_slot' | 'call_human';
export type StatusTone = 'success' | 'warning' | 'danger' | 'neutral' | 'info';
export type ToastKind = 'success' | 'error' | 'info';
export type ScreenName =
  | 'login' | 'forgot_password' | 'reset_password' | 'accept_invite'
  | 'change_password' | 'admin_users' | 'auth_events' | 'dashboard'
  | 'research' | 'companies' | 'company_detail' | 'human_review'
  | 'contacts_needed' | 'email_review' | 'conversations' | 'chat' | 'bookings';

// ===================== auth / users =====================
export interface AuthUser { id: number; email: string; is_admin: boolean }
export interface UserSummary { id: number; email: string; is_admin: boolean; created_at: ISODateString }
export interface AuthEvent {
  id: number; user_id: number | null; event: AuthEventType;
  ip: string | null; user_agent: string | null; detail: string | null; created_at: ISODateString;
}
export interface LoginRequest { email: string; password: string }
export interface LoginResponse { token: string; user: AuthUser }
export interface ChangePasswordRequest { old_password: string }
export interface ChangePasswordConfirmRequest { code: string; new_password: string; new_password_confirm: string }
export interface ForgotPasswordRequest { email: string }
export interface ResetPasswordRequest { email: string; code: string; new_password: string; new_password_confirm: string }
export interface AcceptInviteRequest { email: string; code: string; new_password: string; new_password_confirm: string }
export interface InviteRequest { email: string }
export interface AuthEventsQuery { limit?: number }

// ===================== model usage =====================
export interface ModelUsageTotals {
  calls: number;
  input_tokens: number;
  output_tokens: number;
  reasoning_tokens: number;
  total_tokens: number;
  cost_usd: number | null;
  cost_complete: boolean;
}
export interface ModelUsageSummary extends ModelUsageTotals {
  by_module: Record<string, ModelUsageTotals>;
}

// ===================== research (Module 1) =====================
export interface Reason { text: string; source_url: string; quote: string }
export interface SourceCheck { url: string; result: SourceResult; status: number | null }
export interface DomainCheck { bucket: 1 | 2 | 3; status: number | null; redirected_to: string | null }
export interface ResearchData { reasons: Reason[]; domain_check?: DomainCheck; sources: SourceCheck[] }
export interface MemoryFact { field: string; value: string; source_url: string; quote: string }
export interface Memory { facts: MemoryFact[] }
export interface ResearchRun {
  id: number; status: ResearchRunStatus; selection: string;
  target_approved: number; created_at: ISODateString;
}
export interface ResearchStatus {
  run: ResearchRun | null;
  counts: Partial<Record<CompanyStatus, number>>;
  progress: { search_jobs: number };
  tokens: { in: number; out: number };
  searches: number;
}
export interface StartResearchRequest { selection: string }
export interface ReviewCompanyRequest { company_id: number; decision: 'human_approved' | 'human_rejected' }
export interface CompaniesQuery { status?: CompanyStatus[]; has_contact?: boolean }

export interface CompanySummary {
  id: number; domain: string; score: number | null; status: CompanyStatus;
  email_status: EmailStatus; thread_state: ThreadState; do_not_contact: boolean;
  contact_email: string | null; contact_role: ContactRole | null;
  domain_check: DomainCheck | null; reasons_preview: Reason[];
  created_at: ISODateString; updated_at: ISODateString;
}
export interface CompanyDetail extends CompanySummary {
  run_id: number; contact_source: ContactSource | null;
  research_data: ResearchData | null; memory: Memory | null; usage: ModelUsageSummary;
}

// ===================== outreach (Module 2) =====================
export interface ContactRequest { contact_email: string; contact_role: ContactRole }
export interface EmailDraft {
  message_id: number; company_id: number; domain: string;
  contact_email: string; contact_role: ContactRole;
  body: string; facts: MemoryFact[]; created_at: ISODateString;
}
export interface EmailReviewRequest { action: 'approve' | 'edit' | 'reject'; body?: string }
export interface ToolCall {
  name: ToolName; args: Record<string, unknown>; result: Record<string, unknown> | null;
}
export interface ThreadMessage {
  id: number; company_id: number; sender_type: MessageSender; body: string;
  status: MessageStatus; tool_calls: ToolCall[] | null;
  created_at: ISODateString; updated_at: ISODateString;
}
export interface ThreadSummary {
  company_id: number; domain: string; contact_email: string | null;
  thread_state: ThreadState; last_message_preview: string;
  last_message_sender: MessageSender; last_message_at: ISODateString;
}
export interface ThreadDetail { summary: ThreadSummary; messages: ThreadMessage[]; usage: ModelUsageSummary }
export interface HumanReplyRequest { body: string }

// ===================== bookings / notifications / dashboard =====================
export interface Booking {
  id: number; company_id: number; domain: string; cal_booking_uid: string;
  scheduled_at: ISODateString; status: BookingStatus; source: BookingSource;
  created_at: ISODateString; updated_at: ISODateString;
}
export interface BookingsQuery { from: ISODateString; to: ISODateString }
export interface Notification {
  id: number; company_id: number; domain: string; reason: NotificationReason;
  body: string | null; read: boolean; created_at: ISODateString;
}
export interface MarkReadRequest { ids: number[] }
export interface DashboardSummary {
  research: { approved: number; pending: number; needs_human_review: number };
  emails: { pending_review: number; sent: number; rejected: number };
  conversations: { auto: number; needs_human: number; human_taken_over: number };
  bookings: { upcoming: number };
  notifications: { unread: number };
  usage: ModelUsageSummary;
}

// ===================== generic =====================
export interface OkResponse { ok: true }
export interface ErrorBody { detail: string }
export interface ApiErrorShape { status: number; detail: string; retryAfter: number | null }

// ===================== UI / context =====================
export interface Toast { id: number; kind: ToastKind; text: string }
export interface AppContextValue {
  user: AuthUser | null;
  screen: ScreenName;
  selectedCompanyId: number | null;        // used by 'company_detail'
  selectedThreadCompanyId: number | null;  // used by 'chat'
  toasts: Toast[];
  sessionExpired: boolean;
  signIn: (token: string, user: AuthUser) => void;
  signOut: () => void;
  goTo: (screen: ScreenName, companyId?: number) => void; // companyId fills the selected id matching the target screen
  pushToast: (kind: ToastKind, text: string) => void;
  dismissToast: (id: number) => void;
}
