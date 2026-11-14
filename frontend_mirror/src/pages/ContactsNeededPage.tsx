/**
 * Inputs :
 *   - props: {} (no props)
 *   - useApp(): AppContextValue (from shared/AppContext.tsx)
 *   - usePolling(() => listCompanies({ status: ['approved', 'human_approved'], has_contact: false })) -> CompanySummary[]; saveContact(companyId: number, body: ContactRequest): Promise<CompanySummary> (api/researchApi.ts, api/outreachApi.ts)
 *   - useAuthGuard(), useAsync, useToast hooks
 * Outputs :
 *   - JSX.Element (PageHeader 'Contacts needed'; one Card per company with domain, ScoreBadge and a ContactForm; on save the card leaves the list and a toast says 'Contact saved, a draft will be written'; a 422 detail (generic inbox) is shown inline on that card; Skeleton / EmptyState / ErrorState)
 * File explanation : Approved companies that still need a named contact before an email can be drafted.
 */
