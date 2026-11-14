/**
 * Inputs :
 *   - props: { company: CompanySummary; index: number; onOpen: (id: number) => void }
 *   - COMPANY_STATUS_LABEL, COMPANY_STATUS_TONE, EMAIL_STATUS_LABEL, EMAIL_STATUS_TONE (from shared/constants.ts)
 * Outputs :
 *   - JSX.Element (interactive Card with domain, ScoreBadge, company StatusPill, email-status StatusPill, up to 2 reasons_preview texts; click calls onOpen(company.id))
 * File explanation : One company in the company grid.
 */
