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
