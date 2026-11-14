/**
 * Inputs :
 *   - props: {} (no props)
 *   - useApp(): AppContextValue (from shared/AppContext.tsx)
 *   - usePolling(() => listCompanies()) -> CompanySummary[] (api/researchApi.ts)
 *   - useAuthGuard()
 * Outputs :
 *   - JSX.Element (PageHeader 'Companies' with count; CompanyFilters; responsive grid of CompanyCards filtered client-side by status and domain text and sorted by score desc or created_at desc; card click -> goTo('company_detail', id); Skeleton / EmptyState / ErrorState)
 * File explanation : Grid of all researched companies with score and status.
 */
