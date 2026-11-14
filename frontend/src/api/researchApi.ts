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

import { apiCall } from './client';
import { ENDPOINTS } from './endpoints';
import type {
  CompaniesQuery,
  CompanyDetail,
  CompanySummary,
  OkResponse,
  ResearchRun,
  ResearchStatus,
  ReviewCompanyRequest,
  StartResearchRequest,
} from '../shared/types';

export function startResearch(body: StartResearchRequest): Promise<ResearchRun> {
  return apiCall(ENDPOINTS.startResearch, { body });
}

export function pauseResearch(): Promise<ResearchRun> {
  return apiCall(ENDPOINTS.pauseResearch);
}

export function resumeResearch(): Promise<ResearchRun> {
  return apiCall(ENDPOINTS.resumeResearch);
}

export function getResearchStatus(): Promise<ResearchStatus> {
  return apiCall(ENDPOINTS.getResearchStatus);
}

export function listCompanies(query?: CompaniesQuery): Promise<CompanySummary[]> {
  return apiCall(ENDPOINTS.listCompanies, { query });
}

export function getCompany(id: number): Promise<CompanyDetail> {
  return apiCall(ENDPOINTS.getCompany, { pathParams: { id } });
}

export function reviewCompany(body: ReviewCompanyRequest): Promise<OkResponse> {
  return apiCall(ENDPOINTS.reviewCompany, { body });
}
