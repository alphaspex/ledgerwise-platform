/**
 * Inputs :
 *   - props: { company: CompanySummary; index: number; busy: boolean; onDecision: (companyId: number, decision: 'human_approved' | 'human_rejected') => Promise<void> }
 * Outputs :
 *   - JSX.Element (Card with domain, ScoreBadge, why it was flagged (domain_check.status text such as 'Blocked: HTTP 403'), reasons_preview, Approve and Reject Buttons that call onDecision)
 * File explanation : One company waiting for a human decision.
 */
