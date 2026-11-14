/**
 * Inputs :
 *   - apiCall, ENDPOINTS
 *   - types from shared/types.ts
 * Outputs :
 *   - saveContact(companyId: number, body: ContactRequest): Promise<CompanySummary>
 *   - listEmailDrafts(): Promise<EmailDraft[]>
 *   - reviewEmail(messageId: number, body: EmailReviewRequest): Promise<OkResponse>
 *   - listThreads(): Promise<ThreadSummary[]>
 *   - getThread(companyId: number): Promise<ThreadDetail>
 *   - takeoverThread(companyId: number): Promise<ThreadSummary>
 *   - sendHumanReply(companyId: number, body: HumanReplyRequest): Promise<ThreadMessage>
 * File explanation : Typed wrappers for Module 2: contact entry, first-email review, conversations and human takeover/replies.
 */

import { apiCall } from './client';
import { ENDPOINTS } from './endpoints';
import type {
  CompanySummary,
  ContactRequest,
  EmailDraft,
  EmailReviewRequest,
  HumanReplyRequest,
  OkResponse,
  ThreadDetail,
  ThreadMessage,
  ThreadSummary,
} from '../shared/types';

export function saveContact(companyId: number, body: ContactRequest): Promise<CompanySummary> {
  return apiCall(ENDPOINTS.saveContact, { pathParams: { id: companyId }, body });
}

export function listEmailDrafts(): Promise<EmailDraft[]> {
  return apiCall(ENDPOINTS.listEmailDrafts);
}

export function reviewEmail(messageId: number, body: EmailReviewRequest): Promise<OkResponse> {
  return apiCall(ENDPOINTS.reviewEmail, { pathParams: { message_id: messageId }, body });
}

export function listThreads(): Promise<ThreadSummary[]> {
  return apiCall(ENDPOINTS.listThreads);
}

export function getThread(companyId: number): Promise<ThreadDetail> {
  return apiCall(ENDPOINTS.getThread, { pathParams: { company_id: companyId } });
}

export function takeoverThread(companyId: number): Promise<ThreadSummary> {
  return apiCall(ENDPOINTS.takeoverThread, { pathParams: { company_id: companyId } });
}

export function sendHumanReply(companyId: number, body: HumanReplyRequest): Promise<ThreadMessage> {
  return apiCall(ENDPOINTS.sendHumanReply, { pathParams: { company_id: companyId }, body });
}
