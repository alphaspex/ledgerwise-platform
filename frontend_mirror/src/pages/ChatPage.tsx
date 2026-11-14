/**
 * Inputs :
 *   - props: {} (no props)
 *   - useApp(): AppContextValue (from shared/AppContext.tsx)
 *   - context.selectedThreadCompanyId: number | null
 *   - usePolling(() => getThread(id)) -> ThreadDetail; takeoverThread(companyId: number): Promise<ThreadSummary>; sendHumanReply(companyId: number, body: HumanReplyRequest): Promise<ThreadMessage> (api/outreachApi.ts)
 *   - useAuthGuard(), useAsync, useToast hooks
 * Outputs :
 *   - JSX.Element (full screen: PageHeader with domain, thread-state pill and back button -> goTo('conversations'); scrollable list of ChatBubbles that auto-scrolls to the newest message; HumanReplyBox pinned at the bottom; if selectedThreadCompanyId is null it calls goTo('conversations'); Skeleton / ErrorState)
 * File explanation : Read a whole conversation, take it over and reply as a human.
 */
