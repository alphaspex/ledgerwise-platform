/**
 * Inputs :
 *   - props: {} (no props)
 *   - useApp(): AppContextValue (from shared/AppContext.tsx)
 *   - context.selectedCompanyId: number | null
 *   - usePolling(() => getCompany(id)) -> CompanyDetail (api/researchApi.ts)
 *   - useAuthGuard()
 * Outputs :
 *   - JSX.Element (full screen: PageHeader with back button -> goTo('companies'); ScoreBadge + status pills; ReasonList(research_data.reasons, research_data.sources); FactList(memory.facts) when memory exists; contact block (email, role, source); do_not_contact warning banner when true; if selectedCompanyId is null it calls goTo('companies'); Skeleton / ErrorState)
 * File explanation : Everything known about one company, with proof for each reason.
 */
