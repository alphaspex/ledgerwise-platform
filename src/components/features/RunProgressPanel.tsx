/**
 * Inputs :
 *   - props: { status: ResearchStatus; onPause: () => void; onResume: () => void; busy: boolean }
 *   - COMPANY_STATUS_LABEL, COMPANY_STATUS_TONE, RESEARCH_TARGET (from shared/constants.ts)
 * Outputs :
 *   - JSX.Element (run status StatusPill; ProgressBar of (approved + human_approved) vs run.target_approved; one AnimatedCounter per status in counts; tokens in/out and searches; Pause Button when running, Resume Button when paused, none when done or run is null)
 * File explanation : Live research progress, redrawn on every 5s poll.
 */

import { Pause, Play } from 'lucide-react';
import {
  COMPANY_STATUS_LABEL,
  COMPANY_STATUS_TONE,
  RESEARCH_TARGET,
} from '../../shared/constants';
import type {
  CompanyStatus,
  ResearchRunStatus,
  ResearchStatus,
  StatusTone,
} from '../../shared/types';
import { AnimatedCounter } from '../ui/AnimatedCounter';
import { Button } from '../ui/Button';
import { ProgressBar } from '../ui/ProgressBar';
import { StatusPill } from '../ui/StatusPill';

const ALL_COMPANY_STATUSES: CompanyStatus[] = [
  'approved',
  'human_approved',
  'pending',
  'needs_human_review',
  'human_rejected',
  'rejected_low_evidence',
  'failed_404',
  'failed_enrichment',
];

const RUN_STATUS_LABEL: Record<ResearchRunStatus, string> = {
  running: 'Running',
  paused: 'Paused',
  done: 'Done',
};

const RUN_STATUS_TONE: Record<ResearchRunStatus, StatusTone> = {
  running: 'info',
  paused: 'warning',
  done: 'success',
};

const STAT_TONE_TEXT: Record<StatusTone, string> = {
  success: 'text-ok',
  warning: 'text-gold-deep',
  danger: 'text-bad',
  info: 'text-slateblue-600',
  neutral: 'text-navy-soft',
};

export function RunProgressPanel({
  status,
  onPause,
  onResume,
  busy,
}: {
  status: ResearchStatus;
  onPause: () => void;
  onResume: () => void;
  busy: boolean;
}) {
  const { run, counts, tokens, searches } = status;
  const approvedTotal = (counts.approved ?? 0) + (counts.human_approved ?? 0);
  const target = run?.target_approved ?? RESEARCH_TARGET;

  return (
    <div className="rounded-xl border border-line bg-surface p-5 shadow-card space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2.5">
            <h3 className="text-base font-semibold text-navy">
              {run ? `Run #${run.id}` : 'Research status'}
            </h3>
            {run ? (
              <StatusPill
                label={RUN_STATUS_LABEL[run.status]}
                tone={RUN_STATUS_TONE[run.status]}
              />
            ) : (
              <StatusPill label="Idle" tone="neutral" />
            )}
          </div>
          {run ? <p className="text-xs text-navy-mute mt-1 break-words">{run.selection}</p> : null}
        </div>

        <div className="flex items-center gap-2 shrink-0">
          {run?.status === 'running' ? (
            <Button variant="secondary" icon={Pause} onClick={onPause} loading={busy}>
              Pause
            </Button>
          ) : null}
          {run?.status === 'paused' ? (
            <Button variant="primary" icon={Play} onClick={onResume} loading={busy}>
              Resume
            </Button>
          ) : null}
        </div>
      </div>

      <ProgressBar value={approvedTotal} max={target} label="Approved companies" />

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {ALL_COMPANY_STATUSES.map((key) => {
          const tone = COMPANY_STATUS_TONE[key];
          return (
            <div key={key} className="rounded-lg border border-line bg-canvas/50 p-3 space-y-1">
              <div className="text-xs text-navy-mute">{COMPANY_STATUS_LABEL[key]}</div>
              <div className={`text-lg font-bold ${STAT_TONE_TEXT[tone]}`}>
                <AnimatedCounter value={counts[key] ?? 0} />
              </div>
            </div>
          );
        })}
      </div>

      <div className="flex flex-wrap items-center gap-6 pt-2 border-t border-line text-xs text-navy-soft tabular-nums">
        <span>Tokens in: {tokens.in.toLocaleString()}</span>
        <span>Tokens out: {tokens.out.toLocaleString()}</span>
        <span>Searches: {searches.toLocaleString()}</span>
      </div>
    </div>
  );
}
