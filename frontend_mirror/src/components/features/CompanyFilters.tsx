/**
 * Inputs :
 *   - props: { status: CompanyStatus | 'all'; onStatusChange: (s: CompanyStatus | 'all') => void; query: string; onQueryChange: (q: string) => void; sort: 'score' | 'recent'; onSortChange: (s: 'score' | 'recent') => void }
 *   - COMPANY_STATUS_LABEL (from shared/constants.ts)
 * Outputs :
 *   - JSX.Element (scrollable row of status filter pills with 'All', a search TextInput for the domain, and a Score / Recent toggle)
 * File explanation : Filter bar of the Companies page. Pure controlled component: filtering itself happens in CompaniesPage.
 */
