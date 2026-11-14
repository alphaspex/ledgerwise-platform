/**
 * Inputs :
 *   - props: {} (no props)
 *   - useApp(): AppContextValue (from shared/AppContext.tsx)
 *   - usePolling(() => listCompanies({ status: ['needs_human_review'] })) -> CompanySummary[]; reviewCompany(body: ReviewCompanyRequest): Promise<OkResponse> (api/researchApi.ts)
 *   - useAuthGuard(), useAsync, useToast hooks
 * Outputs :
 *   - JSX.Element (PageHeader 'Human review'; grid of HumanReviewCards; after a decision the card leaves the list with an exit animation and a toast; Skeleton / EmptyState 'Nothing to review' / ErrorState)
 * File explanation : Approve or reject companies whose website could not be checked automatically.
 */
