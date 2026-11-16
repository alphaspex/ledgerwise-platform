/**
 * Inputs :
 *   - props: {} (no props)
 *   - useApp(): AppContextValue (from shared/AppContext.tsx)
 *   - context.selectedCompanyId: number | null
 *   - usePolling(() => getCompany(id)) -> CompanyDetail (api/researchApi.ts)
 *   - useAuthGuard()
 * Outputs :
 *   - JSX.Element (company detail; 404 or missing selectedCompanyId returns to 'companies'; Skeleton / ErrorState for other failures)
 * File explanation : Shows one company's research evidence, verified memory, contact details, and status; stale saved company IDs return to the company list.
 */
