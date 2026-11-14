/**
 * Inputs :
 *   - props: {} (no props)
 *   - useApp(): AppContextValue (from shared/AppContext.tsx)
 *   - usePolling(getResearchStatus) -> ResearchStatus; startResearch(body: StartResearchRequest): Promise<ResearchRun>; pauseResearch(): Promise<ResearchRun>; resumeResearch(): Promise<ResearchRun> (api/researchApi.ts)
 *   - useAuthGuard(), useAsync, useToast hooks
 * Outputs :
 *   - JSX.Element (PageHeader 'Research'; RunStartForm (disabled while run.status is 'running' or 'paused'); RunProgressPanel when a run exists; EmptyState 'No research run yet' otherwise; after start/pause/resume it refreshes the poll immediately and shows a toast)
 * File explanation : Start, watch, pause and resume the research run.
 */
