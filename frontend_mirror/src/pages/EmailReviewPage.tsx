/**
 * Inputs :
 *   - props: {} (no props)
 *   - useApp(): AppContextValue (from shared/AppContext.tsx)
 *   - usePolling(listEmailDrafts) -> EmailDraft[]; reviewEmail(messageId: number, body: EmailReviewRequest): Promise<OkResponse> (api/outreachApi.ts)
 *   - useAuthGuard(), useAsync, useToast hooks
 * Outputs :
 *   - JSX.Element (PageHeader 'Email review' with pending count; stack of EmailDraftCards; approve -> reviewEmail(id, { action: 'approve' }); edit -> { action: 'edit', body }; reject -> { action: 'reject' }; the card exits with animation and a toast; a 409 refreshes the list; Skeleton / EmptyState 'No drafts waiting' / ErrorState)
 * File explanation : Human gate: approve, edit or reject every first email before it is sent.
 */
