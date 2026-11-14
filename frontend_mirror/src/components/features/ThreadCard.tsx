/**
 * Inputs :
 *   - props: { thread: ThreadSummary; index: number; onOpen: (companyId: number) => void }
 *   - THREAD_STATE_LABEL, THREAD_STATE_TONE (from shared/constants.ts)
 * Outputs :
 *   - JSX.Element (interactive Card with domain, thread-state StatusPill, last message preview (plain text, one line), who sent it and the time; click calls onOpen(thread.company_id))
 * File explanation : One conversation in the conversations list.
 */
