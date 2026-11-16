/**
 * Inputs :
 *   - props: {} (no props)
 *   - useApp(): AppContextValue (from shared/AppContext.tsx)
 *   - context.selectedCompanyId: number | null
 *   - usePolling(() => getCompany(id)) -> CompanyDetail (api/researchApi.ts)
 *   - useAuthGuard()
 * Outputs :
 *   - JSX.Element (company evidence and contact details, per-company AI usage totals, and 404 recovery to 'companies'; Skeleton / ErrorState for other failures)
 * File explanation : Shows verified company research, memory, contact state, and the AI tokens/cost attributed to that company.
 */
