/**
 * Inputs : import.meta.env.VITE_API_BASE_URL (string, from .env), types from shared/types.ts
 * Outputs : API_BASE_URL: string; TOKEN_STORAGE_KEY: string; POLL_INTERVAL_MS: number; RESEARCH_TARGET: number; PASSWORD_MIN_LEN: number; CODE_LENGTH: number; TOAST_DURATION_MS: number; STAGGER_SECONDS: number; PAGE_TRANSITION_SECONDS: number; *_LABEL and *_TONE lookup tables (Record<Enum, string | StatusTone>); SIDEBAR_ITEMS: SidebarItem[]; BOTTOM_BAR_SCREENS: ScreenName[]
 * File explanation : Every fixed value and label in one place (poll interval, token key, status labels and colors-as-tones, navigation items). No hex colors here: colors live in tailwind.config.ts, tones map to them inside StatusPill.
 */
import type {
  BookingStatus, CompanyStatus, ContactRole, EmailStatus, NotificationReason,
  ScreenName, StatusTone, ThreadState,
} from './types';

export const API_BASE_URL: string = import.meta.env.VITE_API_BASE_URL as string;
export const TOKEN_STORAGE_KEY = 'ledgerwise_token';
export const POLL_INTERVAL_MS = 5000;
export const RESEARCH_TARGET = 30;
export const PASSWORD_MIN_LEN = 8;
export const CODE_LENGTH = 6;
export const TOAST_DURATION_MS = 4000;
export const STAGGER_SECONDS = 0.04;
export const PAGE_TRANSITION_SECONDS = 0.25;
export const RATE_LIMIT_TOAST = 'Too many attempts, try again in a minute';
export const SESSION_EXPIRED_TEXT = 'Your session expired. Please log in again.';

export const COMPANY_STATUS_LABEL: Record<CompanyStatus, string> = {
  pending: 'Researching', approved: 'Approved', needs_human_review: 'Needs review',
  human_approved: 'Approved by team', human_rejected: 'Rejected by team',
  rejected_low_evidence: 'Low evidence', failed_404: 'Site not found', failed_enrichment: 'Research failed',
};
export const COMPANY_STATUS_TONE: Record<CompanyStatus, StatusTone> = {
  pending: 'info', approved: 'success', needs_human_review: 'warning', human_approved: 'success',
  human_rejected: 'danger', rejected_low_evidence: 'neutral', failed_404: 'danger', failed_enrichment: 'danger',
};
export const EMAIL_STATUS_LABEL: Record<EmailStatus, string> = {
  not_started: 'Not started', drafting: 'Drafting', pending_review: 'Awaiting review',
  approved: 'Approved', sent: 'Sent', rejected_by_human: 'Rejected', failed_contact: 'Send failed',
};
export const EMAIL_STATUS_TONE: Record<EmailStatus, StatusTone> = {
  not_started: 'neutral', drafting: 'info', pending_review: 'warning',
  approved: 'info', sent: 'success', rejected_by_human: 'danger', failed_contact: 'danger',
};
export const THREAD_STATE_LABEL: Record<ThreadState, string> = {
  inactive: 'No thread', auto: 'Agent replying', needs_human: 'Needs a human',
  human_taken_over: 'Human took over', closed: 'Closed',
};
export const THREAD_STATE_TONE: Record<ThreadState, StatusTone> = {
  inactive: 'neutral', auto: 'info', needs_human: 'warning', human_taken_over: 'success', closed: 'neutral',
};
export const BOOKING_STATUS_LABEL: Record<BookingStatus, string> = {
  booked: 'Booked', cancelled: 'Cancelled', rescheduled: 'Rescheduled', completed: 'Completed',
};
export const BOOKING_STATUS_TONE: Record<BookingStatus, StatusTone> = {
  booked: 'success', cancelled: 'danger', rescheduled: 'warning', completed: 'neutral',
};
export const NOTIFICATION_REASON_LABEL: Record<NotificationReason, string> = {
  unsure_answer: 'Agent unsure', do_not_contact: 'Asked to stop',
  booking_conflict: 'Booking conflict', contact_missing: 'Contact missing',
};
export const CONTACT_ROLE_LABEL: Record<ContactRole, string> = {
  founder: 'Founder', coo: 'COO', finance: 'Finance', unknown: 'Unknown',
};
export const SCREEN_LABEL: Record<ScreenName, string> = {
  login: 'Log in', forgot_password: 'Forgot password', reset_password: 'Reset password',
  accept_invite: 'Accept invite', change_password: 'Change password', admin_users: 'Team',
  auth_events: 'Security log', dashboard: 'Dashboard', research: 'Research',
  companies: 'Companies', company_detail: 'Company', human_review: 'Human review',
  contacts_needed: 'Contacts needed', email_review: 'Email review',
  conversations: 'Conversations', chat: 'Conversation', bookings: 'Bookings',
};

export interface SidebarItem { screen: ScreenName; label: string; icon: string; adminOnly: boolean }
// icon = exported name from lucide-react's `icons` map
export const SIDEBAR_ITEMS: SidebarItem[] = [
  { screen: 'dashboard', label: 'Dashboard', icon: 'LayoutDashboard', adminOnly: false },
  { screen: 'research', label: 'Research', icon: 'Search', adminOnly: false },
  { screen: 'companies', label: 'Companies', icon: 'Building2', adminOnly: false },
  { screen: 'human_review', label: 'Human review', icon: 'ShieldCheck', adminOnly: false },
  { screen: 'contacts_needed', label: 'Contacts needed', icon: 'UserPlus', adminOnly: false },
  { screen: 'email_review', label: 'Email review', icon: 'MailCheck', adminOnly: false },
  { screen: 'conversations', label: 'Conversations', icon: 'MessagesSquare', adminOnly: false },
  { screen: 'bookings', label: 'Bookings', icon: 'CalendarDays', adminOnly: false },
  { screen: 'auth_events', label: 'Security log', icon: 'ScrollText', adminOnly: false },
  { screen: 'admin_users', label: 'Team', icon: 'Users', adminOnly: true },
  { screen: 'change_password', label: 'Change password', icon: 'KeyRound', adminOnly: false },
];
// Mobile bottom bar shows these 5; everything else sits behind a "More" button.
export const BOTTOM_BAR_SCREENS: ScreenName[] = ['dashboard', 'companies', 'email_review', 'conversations', 'bookings'];
