/**
 * Inputs :
 *   - apiCall, ENDPOINTS
 *   - types from shared/types.ts
 * Outputs :
 *   - startResearch(body: StartResearchRequest): Promise<ResearchRun>
 *   - pauseResearch(): Promise<ResearchRun>
 *   - resumeResearch(): Promise<ResearchRun>
 *   - getResearchStatus(): Promise<ResearchStatus>
 *   - listCompanies(query?: CompaniesQuery): Promise<CompanySummary[]>
 *   - getCompany(id: number): Promise<CompanyDetail>
 *   - reviewCompany(body: ReviewCompanyRequest): Promise<OkResponse>
 * File explanation : Typed wrappers for Module 1: research run control, status, company lists/detail and human review decisions.
 */
