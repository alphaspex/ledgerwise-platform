/**
 * Inputs :
 *   - props: { status: ResearchStatus; onPause: () => void; onResume: () => void; busy: boolean }
 *   - COMPANY_STATUS_LABEL, COMPANY_STATUS_TONE, RESEARCH_TARGET (from shared/constants.ts)
 * Outputs :
 *   - JSX.Element (run status StatusPill; ProgressBar of (approved + human_approved) vs run.target_approved; one AnimatedCounter per status in counts; tokens in/out and searches; Pause Button when running, Resume Button when paused, none when done or run is null)
 * File explanation : Live research progress, redrawn on every 5s poll.
 */
