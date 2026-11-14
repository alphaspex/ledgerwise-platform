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

import { useCallback, useEffect } from 'react';
import { Search } from 'lucide-react';
import {
  getResearchStatus,
  pauseResearch,
  resumeResearch,
  startResearch,
} from '../api/researchApi';
import { RunProgressPanel } from '../components/features/RunProgressPanel';
import { RunStartForm } from '../components/features/RunStartForm';
import { PageHeader } from '../components/layout/PageHeader';
import { EmptyState } from '../components/ui/EmptyState';
import { ErrorState } from '../components/ui/ErrorState';
import { Skeleton } from '../components/ui/Skeleton';
import { useAsync } from '../hooks/useAsync';
import { useAuthGuard } from '../hooks/useAuthGuard';
import { usePolling } from '../hooks/usePolling';
import { useToast } from '../hooks/useToast';
import { useApp } from '../shared/AppContext';
import type { ResearchStatus } from '../shared/types';

export function ResearchPage() {
  useAuthGuard();
  const app = useApp();
  void app;
  const toast = useToast();

  const fetchStatus = useCallback(() => getResearchStatus(), []);
  const { data: status, loading, error, refresh } = usePolling<ResearchStatus>(fetchStatus);

  const startAction = useAsync(startResearch);
  const pauseAction = useAsync(pauseResearch);
  const resumeAction = useAsync(resumeResearch);

  useEffect(() => {
    if (startAction.error) toast.error(startAction.error.detail);
  }, [startAction.error, toast]);

  useEffect(() => {
    if (pauseAction.error) toast.error(pauseAction.error.detail);
  }, [pauseAction.error, toast]);

  useEffect(() => {
    if (resumeAction.error) toast.error(resumeAction.error.detail);
  }, [resumeAction.error, toast]);

  const handleStart = async (selection: string) => {
    const run = await startAction.run({ selection });
    if (run) {
      toast.success('Research run started');
      await refresh();
    }
  };

  const handlePause = async () => {
    const run = await pauseAction.run();
    if (run) {
      toast.info('Research run paused');
      await refresh();
    }
  };

  const handleResume = async () => {
    const run = await resumeAction.run();
    if (run) {
      toast.success('Research run resumed');
      await refresh();
    }
  };

  const isRunActive = status?.run?.status === 'running' || status?.run?.status === 'paused';

  if (loading && !status) {
    return (
      <div className="space-y-6">
        <PageHeader title="Research" />
        <Skeleton variant="card" count={2} />
      </div>
    );
  }

  if (error && !status) {
    return (
      <div className="space-y-6">
        <PageHeader title="Research" />
        <ErrorState message={error.detail} onRetry={() => void refresh()} />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader title="Research" subtitle="Launch and monitor automated company qualification" />

      <RunStartForm
        onStart={handleStart}
        disabled={Boolean(isRunActive)}
        loading={startAction.loading}
      />

      {status?.run ? (
        <RunProgressPanel
          status={status}
          onPause={() => void handlePause()}
          onResume={() => void handleResume()}
          busy={pauseAction.loading || resumeAction.loading}
        />
      ) : (
        <EmptyState
          icon={Search}
          title="No research run yet"
          message="Describe your target customer criteria above to start qualifying companies."
        />
      )}
    </div>
  );
}
