/**
 * Inputs :
 *   - props: {} (no props)
 *   - useApp(): AppContextValue (from shared/AppContext.tsx)
 *   - context.selectedThreadCompanyId: number | null
 *   - usePolling(() => getThread(id)) -> ThreadDetail; takeoverThread(companyId: number): Promise<ThreadSummary>; sendHumanReply(companyId: number, body: HumanReplyRequest): Promise<ThreadMessage> (api/outreachApi.ts)
 *   - useAuthGuard(), useAsync, useToast hooks
 * Outputs :
 *   - JSX.Element (conversation history and controls plus conversation-specific AI usage totals; 404 returns to 'conversations')
 * File explanation : Reads, takes over, and replies to one conversation; shows token and cost usage attributed to its automated replies.
 */
