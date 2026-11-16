/**
 * Inputs :
 *   - props: {} (no props)
 *   - useApp(): AppContextValue (from shared/AppContext.tsx)
 *   - context.selectedThreadCompanyId: number | null
 *   - usePolling(() => getThread(id)) -> ThreadDetail; takeoverThread(companyId: number): Promise<ThreadSummary>; sendHumanReply(companyId: number, body: HumanReplyRequest): Promise<ThreadMessage> (api/outreachApi.ts)
 *   - useAuthGuard(), useAsync, useToast hooks
 * Outputs :
 *   - JSX.Element (conversation detail; 404 or missing selectedThreadCompanyId returns to 'conversations'; Skeleton / ErrorState for other failures)
 * File explanation : Reads, takes over, and replies to one conversation; stale saved thread IDs return to the conversations list.
 */
